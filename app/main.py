from app.core.service import NotesService
from app.storage.memory import MemoryStorage
from app.storage.postgres import PostgresStorage

storage = PostgresStorage()
if __name__ == '__main__':
    NotesService(storage)
