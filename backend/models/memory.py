"""
The shapes of the data that go in and out of the memory endpoints.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class MemoryCreate(BaseModel):
    """What the browser sends to save a new memory."""

    memory: str = Field(..., description="What Adhav should remember.")
    category: Optional[str] = Field(
        default=None,
        description="preference, personal, project, learning, conversation or other. "
        "Leave empty and Adhav guesses.",
    )


class MemoryUpdate(BaseModel):
    """What the browser sends to change a memory."""

    memory: Optional[str] = None
    category: Optional[str] = None


class MemoryOut(BaseModel):
    """One saved memory."""

    id: int
    memory: str
    category: str
    created_at: str
    updated_at: str


class MemoryListResponse(BaseModel):
    """The full memory list plus a few settings the page needs."""

    enabled: bool
    memories: List[MemoryOut]
    categories: List[str]
    max_memories: int
    max_chars: int


class MemorySettings(BaseModel):
    """The memory on/off switch."""

    enabled: bool