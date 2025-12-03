from fastapi import FastAPI, HTTPException

from app.core.errors import ValidationError, StorageUnavailable, NoteNotFound
from app.core.models import Note
from app.core.service import NotesService
from app.main import storage
from app.storage.memory import MemoryStorage

app = FastAPI()

service = NotesService(repo=storage)
@app.get("/health")
def health():
    return {"status": "OK"}

@app.post("/notes")
def create_note(description: str):
    try:
        return service.create(description)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except StorageUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/notes")
def list_notes():
    try:
        return service.list()
    except StorageUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.get("/notes/{note_id}")
def get_note(note_id: str):
    try:
        return service.get(note_id)
    except NoteNotFound:
        raise HTTPException(status_code=404, detail="note not found")
    except StorageUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.patch("/notes/{note_id}")
def update_note(note_id: str, description: str):
    try:
        return service.update(note_id, description)
    except NoteNotFound:
        raise HTTPException(status_code=404, detail="note not found")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except StorageUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.delete("/notes/{note_id}", status_code=204)
def delete_note(note_id: str):
    try:
        service.delete(note_id)
    except NoteNotFound:
        raise HTTPException(status_code=404, detail="note not found")
    except StorageUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))
