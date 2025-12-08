import asyncio
import os
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

import httpx
from fastapi import FastAPI, Request, Response

HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}

ALL_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]


@dataclass
class UpstreamState:
    url: str
    consecutive_failures: int = 0
    down_until: float = 0.0


class CircuitBreakerLB:
    def __init__(self, upstreams: List[str], fail_threshold: int, cooldown_sec: float):
        self.upstreams: Dict[str, UpstreamState] = {u: UpstreamState(u) for u in upstreams}
        self.fail_threshold = fail_threshold
        self.cooldown_sec = cooldown_sec
        self._rr = 0
        self._lock = asyncio.Lock()

    def _is_up(self, s: UpstreamState) -> bool:
        return time.monotonic() >= s.down_until

    async def pick(self) -> Optional[UpstreamState]:
        async with self._lock:
            alive = [s for s in self.upstreams.values() if self._is_up(s)]
            if not alive:
                return None
            self._rr = (self._rr + 1) % len(alive)
            return alive[self._rr]

    async def mark_success(self, s: UpstreamState):
        async with self._lock:
            s.consecutive_failures = 0
            s.down_until = 0.0

    async def mark_failure(self, s: UpstreamState):
        async with self._lock:
            s.consecutive_failures += 1
            if s.consecutive_failures >= self.fail_threshold:
                s.down_until = time.monotonic() + self.cooldown_sec


def _filter_headers(headers) -> Dict[str, str]:
    out = {}
    for k, v in headers.items():
        lk = k.lower()
        if lk in HOP_BY_HOP:
            continue
        out[k] = v
    return out


UPSTREAMS = os.getenv("LB_UPSTREAMS", "http://app1:8000,http://app2:8000").split(",")
HEALTH_PATH = os.getenv("LB_HEALTH_PATH", "/health")

FAIL_THRESHOLD = int(os.getenv("LB_FAIL_THRESHOLD", "2"))
COOLDOWN_SEC = float(os.getenv("LB_COOLDOWN_SEC", "5"))
CHECK_INTERVAL = float(os.getenv("LB_CHECK_INTERVAL", "2"))

# ≤ 2 сек общий бюджет
CONNECT_TIMEOUT = float(os.getenv("LB_CONNECT_TIMEOUT", "0.3"))
READ_TIMEOUT = float(os.getenv("LB_READ_TIMEOUT", "1.5"))

RETRIES = int(os.getenv("LB_RETRIES", "2"))

app = FastAPI()
lb = CircuitBreakerLB(UPSTREAMS, FAIL_THRESHOLD, COOLDOWN_SEC)

client = httpx.AsyncClient(
    timeout=httpx.Timeout(connect=CONNECT_TIMEOUT, read=READ_TIMEOUT, write=READ_TIMEOUT, pool=CONNECT_TIMEOUT),
    limits=httpx.Limits(max_keepalive_connections=50, max_connections=200),
)


@app.on_event("shutdown")
async def _shutdown():
    await client.aclose()


async def health_loop():
    while True:
        for s in list(lb.upstreams.values()):
            try:
                r = await client.get(s.url + HEALTH_PATH)
                if r.status_code == 200:
                    await lb.mark_success(s)
                else:
                    await lb.mark_failure(s)
            except Exception:
                await lb.mark_failure(s)
        await asyncio.sleep(CHECK_INTERVAL)


@app.on_event("startup")
async def _startup():
    asyncio.create_task(health_loop())


@app.api_route("/{path:path}", methods=ALL_METHODS)
async def proxy(path: str, request: Request):
    body = await request.body()
    headers = _filter_headers(request.headers)

    query = str(request.url.query)
    suffix = f"?{query}" if query else ""
    method = request.method

    last_err = None

    for _ in range(RETRIES):
        upstream = await lb.pick()
        if upstream is None:
            return Response(content="no healthy upstreams", status_code=503)

        url = f"{upstream.url}/{path}{suffix}"

        try:
            r = await client.request(
                method,
                url,
                content=body,
                headers=headers,
                follow_redirects=False,
            )

            if 500 <= r.status_code <= 599:
                await lb.mark_failure(upstream)
                last_err = f"upstream {upstream.url} returned {r.status_code}"
                continue

            await lb.mark_success(upstream)

            resp_headers = _filter_headers(r.headers)
            resp_headers["X-LB-Upstream"] = upstream.url

            return Response(content=r.content, status_code=r.status_code, headers=resp_headers)

        except (httpx.TimeoutException, httpx.RequestError) as e:
            await lb.mark_failure(upstream)
            last_err = f"{type(e).__name__}: {e}"

    return Response(content=f"upstream failure: {last_err}", status_code=503)
