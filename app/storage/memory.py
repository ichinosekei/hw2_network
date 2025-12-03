import uuid
from abc import ABC
from datetime import datetime, timezone
from logging import exception

from app.core.errors import NoteNotFound

from app.core.models import Note
from app.storage.base import Base


class MemoryStorage(Base, ABC):
    _notes = {}

    def __init__(self):
        # id -> Note
        self._notes: dict[str, Note] = {}
        
    def create(self, description: str):
        created_at = datetime.now(tz=timezone.utc)
        updated_at = datetime.now(tz=timezone.utc)
        note_id = str(uuid.uuid4())
        note = Note(note_id, description, created_at, updated_at)
        self._notes[note_id] = note
        return note

    def get(self, note_id: str):
        try:
            return self._notes[note_id]
        except KeyError:
            raise NoteNotFound()

    def update_description(self, note_id: str, description: str):
        note = self.get(note_id)
        note.description = description
        note.updated_at = datetime.now(tz=timezone.utc)
        self._notes[note_id] = note
        return note

    # def update_title(self, note_id: str, title: str):
    #     note = self.get(note_id)
    #     note.title = title
    #     note.updated_at = datetime.now(tz=timezone.utc)
    #     self._notes[note_id] = note
    #     return note

    def delete(self, note_id: str):
        if note_id not in self._notes:
            raise NoteNotFound()
        del self._notes[note_id]
    def list(self) -> list[Note]:
        return list(self._notes.values())