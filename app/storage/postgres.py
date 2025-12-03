from datetime import datetime, timezone
from typing import List

from sqlalchemy.orm import Session

from app.core.errors import NoteNotFound
from app.core.models import Note
from app.db import SessionLocal
from app.db_models import NoteORM
from app.storage.base import Base


class PostgresStorage(Base):

    def _to_note(self, orm: NoteORM) -> Note:
        return Note(
            id=orm.id,
            description=orm.description,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )

    def _get_session(self) -> Session:
        return SessionLocal()

    def create(self, description: str) -> Note:
        with self._get_session() as session:
            note_orm = NoteORM(
                description=description,
                # created_at и id зададутся через default в модели
            )
            session.add(note_orm)
            session.commit()
            session.refresh(note_orm)  # подтянуть id/created_at из БД
            return self._to_note(note_orm)

    def get(self, note_id: str) -> Note:
        with self._get_session() as session:
            note_orm = session.get(NoteORM, note_id)
            if note_orm is None:
                raise NoteNotFound(f"note {note_id} not found")
            return self._to_note(note_orm)

    def list(self) -> list[Note]:
        with self._get_session() as session:
            notes_orm = (
                session.query(NoteORM)
                .order_by(NoteORM.created_at.desc())
                .all()
            )
            return [self._to_note(row) for row in notes_orm]

    def update_description(self, note_id: str, description: str) -> Note:
        with self._get_session() as session:
            note_orm = session.get(NoteORM, note_id)
            if note_orm is None:
                raise NoteNotFound(f"note {note_id} not found")

            note_orm.description = description
            note_orm.updated_at = datetime.now(timezone.utc)
            session.commit()
            session.refresh(note_orm)
            return self._to_note(note_orm)


    def delete(self, note_id: str) -> None:
        with self._get_session() as session:
            note_orm = session.get(NoteORM, note_id)
            if note_orm is None:
                raise NoteNotFound(f"note {note_id} not found")

            session.delete(note_orm)
            session.commit()
