from app.core.service import NotesService
from app.storage.postgres import PostgresStorage
from app.db import BaseORM, engine
from app.db_models import NoteORM


BaseORM.metadata.create_all(bind=engine)

storage = PostgresStorage()

if __name__ == "__main__":
    NotesService(storage)
