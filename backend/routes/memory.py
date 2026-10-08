"""
The memory endpoints used by the Memory panel on the chat page.
"""

from fastapi import APIRouter, HTTPException

from backend.memory import memory_service
from backend.memory.memory_service import MemoryServiceError
from backend.models.memory import (
    MemoryCreate,
    MemoryListResponse,
    MemoryOut,
    MemorySettings,
    MemoryUpdate,
)

router = APIRouter()


def _to_http_error(error: MemoryServiceError) -> HTTPException:
    return HTTPException(status_code=error.status_code, detail=str(error))


@router.get("/memories", response_model=MemoryListResponse)
def list_all():
    return MemoryListResponse(
        enabled=memory_service.get_memory_enabled(),
        memories=memory_service.list_memories(),
        categories=memory_service.CATEGORIES,
        max_memories=memory_service.MAX_MEMORIES,
        max_chars=memory_service.MAX_MEMORY_CHARS,
    )


@router.post("/memories", response_model=MemoryOut, status_code=201)
def create(body: MemoryCreate):
    try:
        memory, _created = memory_service.add_memory(body.memory, body.category)
    except MemoryServiceError as error:
        raise _to_http_error(error)
    return memory


@router.put("/memories/{memory_id}", response_model=MemoryOut)
def update(memory_id: int, body: MemoryUpdate):
    try:
        return memory_service.update_memory(memory_id, body.memory, body.category)
    except MemoryServiceError as error:
        raise _to_http_error(error)


@router.delete("/memories/{memory_id}")
def delete_one(memory_id: int):
    if not memory_service.delete_memory(memory_id):
        raise HTTPException(status_code=404, detail="That memory was not found.")
    return {"deleted": True}


@router.delete("/memories")
def delete_everything():
    return {"deleted": memory_service.delete_all()}


@router.get("/memory-settings", response_model=MemorySettings)
def get_settings():
    return MemorySettings(enabled=memory_service.get_memory_enabled())


@router.put("/memory-settings", response_model=MemorySettings)
def put_settings(body: MemorySettings):
    memory_service.set_memory_enabled(body.enabled)
    return MemorySettings(enabled=memory_service.get_memory_enabled())