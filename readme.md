# Notes service (REST + gRPC + SOAP) + Load Balancing

Проект: сервис управления заметками (CRUD) с тремя транспортами:
- **REST (HTTP/JSON)**
- **gRPC (HTTP/2 + protobuf)**
- **SOAP (XML)**

Хранилище: **PostgreSQL**.  
Развёртывание: **несколько экземпляров** приложения за балансировщиком.  
TLS/HTTPS: **терминация на nginx**.  
Свой балансировщик (**LB**) реализован для HTTP (REST + SOAP) с **health-check** и **circuit breaker**.

---

## Архитектура

```
Client
  ├─ HTTPS :443 ──> nginx ──> http://lb:8080 ──> http://app1:8000 / http://app2:8000   (REST + SOAP)
  └─ gRPC+TLS :8443 -> nginx (grpc_pass) -> app1:50051 / app2:50051                    (gRPC)
```

- `nginx` делает **HTTPS** и проксирование.
- `lb` —  HTTP reverse-proxy с round-robin, таймаутами, health-check и circuit breaker.
- `app1/app2` — экземпляры сервиса, внутри каждого подняты:
  - REST/SOAP на `:8000`
  - gRPC на `:50051`
- `db` — PostgreSQL.



---


## Запуск

Сборка и старт:

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

Проверка логов:

```bash
docker compose logs -f nginx
docker compose logs -f lb
docker compose logs -f app1
docker compose logs -f app2
```

---

## REST API

```bash
curl -k https://localhost/health
curl -k https://localhost/notes
curl -k https://localhost/notes/<ID>
curl -k -X POST https://localhost/notes -H "Content-Type: application/json" -d '{"description":"hello"}'
curl -k -X PATCH https://localhost/notes/<ID> -H "Content-Type: application/json" -d '{"description":"updated"}'
curl -k -X DELETE https://localhost/notes/<ID>
```
---

## SOAP API 
WSDL: `https://localhost/soap/?wsdl`  
Endpoint: `https://localhost/soap/`

Пример вызова:

```bash
curl -k https://localhost/soap/   -H "Content-Type: text/xml"   --data-binary @create_note.xml
```

Операции:
- CreateNote
- GetNote
- ListNotes
- UpdateDescription
- DeleteNote
---

## gRPC API


gRPC через nginx (TLS): `localhost:8443`

Пример вызова:

```bash
grpcurl -insecure   -import-path app/transport/grpc   -proto notes.proto   -d '{"description":"hello grpc"}'   localhost:8443 notes.v1.NotesService/CreateNote
```
Операции:
- CreateNote
- GetNote
- ListNotes
- UpdateDescription
- DeleteNote
---

## Проверки требований (доказательства)

### 1) REST видит заметки, созданные через gRPC

```bash
$ grpcurl -insecure -import-path app/transport/grpc -proto notes.proto \
  -d '{"description":"from grpc test"}' \
  localhost:8443 notes.v1.NotesService/CreateNote
{
  "id": "b2d693dd-f44e-481a-8fc9-44e62de54beb",
  "description": "from grpc test",
  "createdAtMs": "1765210886906",
  "updatedAtMs": "1765210886906"
}

$ curl -k -s https://localhost/notes | grep -n "from grpc test"
1:[{"id":"b2d693dd-f44e-481a-8fc9-44e62de54beb","description":"from grpc test","created_at":"2025-12-08T16:21:26.906810+00:00","updated_at":"2025-12-08T16:21:26.906813+00:00"},{"id":"58f6cdc9-e959-430d-8cb8-e567069ce2a8","description":"hello soap","created_at":"2025-12-08T15:50:03.940350+00:00","updated_at":"2025-12-08T15:50:03.940353+00:00"},{"id":"a54bdf4a-d277-425b-8248-b5abb1feda3b","description":"hello soap","created_at":"2025-12-08T15:23:21.192172+00:00","updated_at":"2025-12-08T15:23:21.192175+00:00"},{"id":"5f709d14-0a06-44fe-9ce4-d3ca605d0e76","description":"from grpc","created_at":"2025-12-08T14:55:07.110370+00:00","updated_at":"2025-12-08T14:55:07.110373+00:00"},{"id":"2b71a997-151f-40c4-b011-7d2c55343bf1","description":"hello grpc","created_at":"2025-12-08T14:31:57.096786+00:00","updated_at":"2025-12-08T14:31:57.096789+00:00"}]


```

### 2) REST видит заметки, созданные через SOAP

Поменяйте `description` в `create_note.xml` на `from soap` и выполните:

```bash
$ curl -k -i https://localhost/soap/ \
  -H "Content-Type: text/xml; charset=utf-8" \
  --data-binary @create_note.xml
HTTP/1.1 200 OK
Server: nginx/1.29.3
Date: Mon, 08 Dec 2025 15:23:21 GMT
Content-Type: text/xml; charset=utf-8
Content-Length: 518
Connection: keep-alive

<?xml version='1.0' encoding='UTF-8'?>
<soap11env:Envelope xmlns:soap11env="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tns="notes.soap" xmlns:s0="app.transport.soap_app"><soap11env:Body><tns:CreateNoteResponse><tns:CreateNoteResult><s0:id>a54bdf4a-d277-425b-8248-b5abb1f
eda3b</s0:id><s0:description>hello soap</s0:description><s0:created_at_ms>1765207401192</s0:created_at_ms><s0:updated_at_ms>1765207401192</s0:updated_at_ms></tns:CreateNoteResult></tns:CreateNoteResponse></soap11env:Body></soap11env:Enve
lope>
```
```bash
$ curl -k -s https://localhost/notes
[{"id":"a54bdf4a-d277-425b-8248-b5abb1feda3b","description":"hello soap","created_at":"2025-12-08T15:23:21.192172+00:00","updated_at":"2025-12-08T15:23:21.192175+00:00"},{"id":"5f709d14-0a06-44fe-9ce4-d3ca605d0e76","description":"from gr
pc","created_at":"2025-12-08T14:55:07.110370+00:00","updated_at":"2025-12-08T14:55:07.110373+00:00"},{"id":"2b71a997-151f-40c4-b011-7d2c55343bf1","description":"hello grpc","created_at":"2025-12-08T14:31:57.096786+00:00","updated_at":"20
25-12-08T14:31:57.096789+00:00"}]
```

### 3) Проверка балансировки и отказоустойчивости (circuit breaker)

В ответах REST/SOAP есть заголовок **`X-LB-Upstream`**, который показывает, куда ушёл запрос:

```bash
$ curl -k -i https://localhost/soap/?wsdl
HTTP/1.1 200 OK
Server: nginx/1.29.3
Date: Mon, 08 Dec 2025 15:49:57 GMT
Content-Type: text/xml; charset=utf-8
Content-Length: 8042
Connection: keep-alive
x-lb-upstream: http://app1:8000

```

```bash
$ curl -k -i https://localhost/soap/ \
  -H "Content-Type: text/xml; charset=utf-8" \
  --data-binary @create_note.xml
HTTP/1.1 200 OK
Server: nginx/1.29.3
Date: Mon, 08 Dec 2025 15:50:03 GMT
Content-Type: text/xml; charset=utf-8
Content-Length: 518
Connection: keep-alive
x-lb-upstream: http://app2:8000

```

Остановка одного экземпляра:

```bash
docker compose stop app1
[+] Stopping 1/1
 ✔ Container notes-app-1  Stopped  
```

```bash
$ curl -k -i https://localhost/notes
HTTP/1.1 200 OK
Server: nginx/1.29.3
Date: Mon, 08 Dec 2025 15:50:30 GMT
Content-Type: application/json
Content-Length: 676
Connection: keep-alive
x-lb-upstream: http://app2:8000

```
```bash
$ curl -k -i https://localhost/notes
HTTP/1.1 200 OK
Server: nginx/1.29.3
Date: Mon, 08 Dec 2025 15:50:35 GMT
Content-Type: application/json
Content-Length: 676
Connection: keep-alive
x-lb-upstream: http://app2:8000
```

Запуск обратно:

```bash
docker compose start app1
[+] Running 1/1
 ✔ Container notes-app-1  Started   
```

```bash
$ curl -k -i https://localhost/notes
HTTP/1.1 200 OK
Server: nginx/1.29.3
Date: Mon, 08 Dec 2025 15:51:04 GMT
Content-Type: application/json
Content-Length: 676
Connection: keep-alive
x-lb-upstream: http://app2:8000
```

```bash
$ curl -k -i https://localhost/notes

HTTP/1.1 200 OK
Server: nginx/1.29.3
Date: Mon, 08 Dec 2025 15:51:06 GMT
Content-Type: application/json
Content-Length: 676
Connection: keep-alive
x-lb-upstream: http://app1:8000

```


Ожидаемо: при остановке `app1` весь трафик идёт в `app2`, после старта `app1` он возвращается в ротацию.

### 4) Таймаут и недоступность компонентов (DB down)

Остановить PostgreSQL:

```bash
$ docker compose stop db
[+] Stopping 1/1
 ✔ Container notes-db  Stopped   
```

Проверить, что ответ возвращается быстро (≤2s):

```bash
$ curl -k -s -o /dev/null -w "status=%{http_code} time=%{time_total}\n" https://localhost/notes
status=504 time=1.017267

```

Вернуть PostgreSQL:

```bash
docker compose start db
```
---

