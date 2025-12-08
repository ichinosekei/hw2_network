import grpc
from app.core.models import Note
from app.core.errors import ValidationError, StorageUnavailable, NoteNotFound
from app.core.service import NotesService

from app.transport.grpc import notes_pb2, notes_pb2_grpc


def _dt_to_ms(dt) -> int:
    # datetime -> epoch milliseconds
    return int(dt.timestamp() * 1000)


def _note_to_proto(note) -> notes_pb2.Note:
    return notes_pb2.Note(
        id=note.id,
        description=note.description,
        created_at_ms=_dt_to_ms(note.created_at),
        updated_at_ms=_dt_to_ms(note.updated_at),
    )


class NotesGrpcServicer(notes_pb2_grpc.NotesServiceServicer):
    def __init__(self, service: NotesService):
        self._service = service

    def _check_deadline(self, context: grpc.ServicerContext):
        rem = context.time_remaining()
        if rem is not None and rem <= 0:
            context.abort(grpc.StatusCode.DEADLINE_EXCEEDED, "deadline exceeded")

    def CreateNote(self, request, context):
        self._check_deadline(context)
        try:
            note = self._service.create(request.description)
            return _note_to_proto(note)
        except ValidationError as e:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(e))
        except StorageUnavailable as e:
            context.abort(grpc.StatusCode.UNAVAILABLE, str(e))
        except Exception:
            context.abort(grpc.StatusCode.INTERNAL, "internal error")

    def GetNote(self, request, context):
        self._check_deadline(context)
        try:
            note = self._service.get(request.id)
            return _note_to_proto(note)
        except NoteNotFound:
            context.abort(grpc.StatusCode.NOT_FOUND, "note not found")
        except StorageUnavailable as e:
            context.abort(grpc.StatusCode.UNAVAILABLE, str(e))
        except Exception:
            context.abort(grpc.StatusCode.INTERNAL, "internal error")

    def ListNotes(self, request, context):
        self._check_deadline(context)
        try:
            notes = self._service.list()
            return notes_pb2.ListNotesResponse(notes=[_note_to_proto(n) for n in notes])
        except StorageUnavailable as e:
            context.abort(grpc.StatusCode.UNAVAILABLE, str(e))
        except Exception:
            context.abort(grpc.StatusCode.INTERNAL, "internal error")

    def UpdateDescription(self, request, context):
        self._check_deadline(context)
        try:
            note = self._service.update(request.id, request.description)
            return _note_to_proto(note)
        except ValidationError as e:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(e))
        except NoteNotFound:
            context.abort(grpc.StatusCode.NOT_FOUND, "note not found")
        except StorageUnavailable as e:
            context.abort(grpc.StatusCode.UNAVAILABLE, str(e))
        except Exception:
            context.abort(grpc.StatusCode.INTERNAL, "internal error")

    def DeleteNote(self, request, context):
        self._check_deadline(context)
        try:
            self._service.delete(request.id)
            return notes_pb2.Empty()
        except NoteNotFound:
            context.abort(grpc.StatusCode.NOT_FOUND, "note not found")
        except StorageUnavailable as e:
            context.abort(grpc.StatusCode.UNAVAILABLE, str(e))
        except Exception:
            context.abort(grpc.StatusCode.INTERNAL, "internal error")
