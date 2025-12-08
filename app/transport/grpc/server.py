import os
from concurrent.futures import ThreadPoolExecutor

import grpc

from app.core.service import NotesService
from app.transport.grpc.servicer import NotesGrpcServicer
from app.transport.grpc import notes_pb2_grpc


def create_grpc_server(service: NotesService) -> grpc.Server:
    workers = int(os.getenv("GRPC_WORKERS", "10"))
    host = os.getenv("GRPC_HOST", "0.0.0.0")
    port = int(os.getenv("GRPC_PORT", "50051"))

    server = grpc.server(ThreadPoolExecutor(max_workers=workers))
    notes_pb2_grpc.add_NotesServiceServicer_to_server(
        NotesGrpcServicer(service), server
    )
    server.add_insecure_port(f"{host}:{port}")
    return server
