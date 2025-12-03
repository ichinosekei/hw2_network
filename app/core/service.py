from dataclasses import dataclass

from app.core.errors import NoteNotFound, ValidationError, StorageUnavailable
from app.storage.base import Base

@dataclass
class NotesService:
    repo: Base

    def _normalize(self, description: str):
        description = description.strip()
        if not description:
            raise ValidationError('description cannot be empty')
        return description


    def _wrap_storage_error(self, error: Exception):
        raise StorageUnavailable("storage is unavailable") from error

    def create(self, description: str):
        description = self._normalize(description)
        try:
            return self.repo.create(description)
        except Exception as e:
            self._wrap_storage_error(e)


    def get(self, note_id: str):
        try:
            return self.repo.get(note_id)
        except NoteNotFound:
            raise
        except Exception as e:
            self._wrap_storage_error(e)

    def list(self):
        try:
            return self.repo.list()
        except Exception as e:
            self._wrap_storage_error(e)

    def update(self, note_id: str, description: str):
        description = self._normalize(description)
        try:
            return self.repo.update_description(note_id, description)
        except NoteNotFound:
            raise
        except Exception as exc:
            self._wrap_storage_error(exc)


    # def update_title(self, note_id: str, title: str) -> Note:
    #     title = title.strip()
    #     try:
    #         return self.repo.update_title(note_id, title)
    #     except NoteNotFound:
    #         raise
    #     except Exception as exc:
    #         self._wrap_storage_error(exc)


    def delete(self, note_id: str) -> None:
        try:
            return self.repo.delete(note_id)
        except NoteNotFound:
            raise
        except Exception as exc:
            self._wrap_storage_error(exc)


