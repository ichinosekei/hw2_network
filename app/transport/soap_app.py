from datetime import datetime
from spyne import Application, rpc, ServiceBase
from spyne import Unicode, Integer, Iterable
from spyne.model.complex import ComplexModel
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from spyne.error import Fault

from app.core.errors import ValidationError, StorageUnavailable, NoteNotFound
from app.core.service import NotesService


def _dt_to_ms(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


class NoteSoap(ComplexModel):
    id = Unicode
    description = Unicode
    created_at_ms = Integer
    updated_at_ms = Integer


def build_soap_wsgi_app(service: NotesService) -> WsgiApplication:
    class NotesSoapService(ServiceBase):

        @rpc(Unicode, _returns=NoteSoap)
        def CreateNote(ctx, description):
            try:
                note = service.create(description)
                return NoteSoap(
                    id=note.id,
                    description=note.description,
                    created_at_ms=_dt_to_ms(note.created_at),
                    updated_at_ms=_dt_to_ms(note.updated_at),
                )
            except ValidationError as e:
                raise Fault(faultcode="Client", faultstring=str(e))
            except StorageUnavailable as e:
                raise Fault(faultcode="Server", faultstring=str(e))

        @rpc(Unicode, _returns=NoteSoap)
        def GetNote(ctx, note_id):
            try:
                note = service.get(note_id)
                return NoteSoap(
                    id=note.id,
                    description=note.description,
                    created_at_ms=_dt_to_ms(note.created_at),
                    updated_at_ms=_dt_to_ms(note.updated_at),
                )
            except NoteNotFound:
                raise Fault(faultcode="Client", faultstring="note not found")
            except StorageUnavailable as e:
                raise Fault(faultcode="Server", faultstring=str(e))

        @rpc(_returns=Iterable(NoteSoap))
        def ListNotes(ctx):
            try:
                notes = service.list()
                for note in notes:
                    yield NoteSoap(
                        id=note.id,
                        description=note.description,
                        created_at_ms=_dt_to_ms(note.created_at),
                        updated_at_ms=_dt_to_ms(note.updated_at),
                    )
            except StorageUnavailable as e:
                raise Fault(faultcode="Server", faultstring=str(e))

        @rpc(Unicode, Unicode, _returns=NoteSoap)
        def UpdateDescription(ctx, note_id, description):
            try:
                note = service.update(note_id, description)
                return NoteSoap(
                    id=note.id,
                    description=note.description,
                    created_at_ms=_dt_to_ms(note.created_at),
                    updated_at_ms=_dt_to_ms(note.updated_at),
                )
            except ValidationError as e:
                raise Fault(faultcode="Client", faultstring=str(e))
            except NoteNotFound:
                raise Fault(faultcode="Client", faultstring="note not found")
            except StorageUnavailable as e:
                raise Fault(faultcode="Server", faultstring=str(e))

        @rpc(Unicode, _returns=Unicode)
        def DeleteNote(ctx, note_id):
            try:
                service.delete(note_id)
                return "OK"
            except NoteNotFound:
                raise Fault(faultcode="Client", faultstring="note not found")
            except StorageUnavailable as e:
                raise Fault(faultcode="Server", faultstring=str(e))

    app = Application(
        [NotesSoapService],
        tns="notes.soap",
        in_protocol=Soap11(validator="lxml"),   # если lxml нет — Spyne обычно деградирует, но если упрётся, скажи
        out_protocol=Soap11(),
    )
    return WsgiApplication(app)
