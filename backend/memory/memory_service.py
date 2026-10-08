"""
All the memory logic: save, list, edit, delete, on/off switch, safety checks.
Only this file talks to the memories table.
"""

import re
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from backend import database

# Until we add login (Stage 18) there is just one user on this computer.
USER_ID = "local"

CATEGORIES = ["preference", "personal", "project", "learning", "conversation", "other"]
MAX_MEMORY_CHARS = 300
MAX_MEMORIES = 50

_COLUMNS = "id, memory, category, created_at, updated_at"


class MemoryServiceError(Exception):
    """A friendly error message that is safe to show to the user."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


# ---------------------------------------------------------------------------
# Safety: do not save secrets
# ---------------------------------------------------------------------------
_SENSITIVE_WORDS = re.compile(
    r"\b(?:password|passcode|otp|cvv|card number|debit card|credit card"
    r"|api[ _-]?key|aadhaar|aadhar)\b|\bpin\b(?!\s*code)",
    re.IGNORECASE,
)
_LONG_NUMBER = re.compile(r"\d(?:[ -]?\d){11,}")  # 12 or more digits
_KEY_LOOKING = re.compile(r"\bsk-[A-Za-z0-9_-]{8,}|AIza[0-9A-Za-z_-]{10,}")


def looks_sensitive(text: str) -> bool:
    """True if the text looks like a password, card number, OTP or API key."""
    return bool(
        _SENSITIVE_WORDS.search(text)
        or _LONG_NUMBER.search(text)
        or _KEY_LOOKING.search(text)
    )


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
_CATEGORY_HINTS = [
    ("preference", re.compile(
        r"\b(?:like|likes|love|loves|prefer|prefers|favou?rite|enjoy|enjoys"
        r"|hate|hates|dislike|call me)\b", re.IGNORECASE)),
    ("learning", re.compile(
        r"\b(?:study|studying|learn|learning|exam|exams|course|subject"
        r"|syllabus|semester)\b", re.IGNORECASE)),
    ("project", re.compile(
        r"\b(?:project|building|app|website|working on)\b", re.IGNORECASE)),
    ("personal", re.compile(
        r"\b(?:my name|name is|i am|i'm|live in|from|birthday|age|family)\b",
        re.IGNORECASE)),
]


def guess_category(text: str) -> str:
    """Pick a category from simple keywords."""
    for category, pattern in _CATEGORY_HINTS:
        if pattern.search(text):
            return category
    return "other"


def clean_text(text: Optional[str]) -> str:
    """Remove extra spaces and line breaks."""
    return re.sub(r"\s+", " ", text or "").strip()


def validate_text(text: Optional[str]) -> str:
    """Return the cleaned text, or raise a friendly error if it can't be saved."""
    cleaned = clean_text(text)
    if not cleaned:
        raise MemoryServiceError("There is nothing to save. Type what I should remember.")
    if len(cleaned) > MAX_MEMORY_CHARS:
        raise MemoryServiceError(
            f"That is too long to save. Please keep it under {MAX_MEMORY_CHARS} characters."
        )
    if looks_sensitive(cleaned):
        raise MemoryServiceError(
            "That looks like a password, card number, OTP or key, so I won't save it. "
            "Please keep private things like that to yourself."
        )
    return cleaned


def _check_category(category: Optional[str], text: str) -> str:
    if not category:
        return guess_category(text)
    if category not in CATEGORIES:
        raise MemoryServiceError("Unknown category. Use one of: " + ", ".join(CATEGORIES) + ".")
    return category


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# The on/off switch
# ---------------------------------------------------------------------------
def get_memory_enabled(user_id: str = USER_ID) -> bool:
    with database.connection() as conn:
        row = conn.execute(
            "SELECT value FROM settings WHERE user_id = ? AND key = 'memory_enabled'",
            (user_id,),
        ).fetchone()
    return row is None or row["value"] != "0"


def set_memory_enabled(enabled: bool, user_id: str = USER_ID) -> None:
    with database.connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (user_id, key, value) "
            "VALUES (?, 'memory_enabled', ?)",
            (user_id, "1" if enabled else "0"),
        )


# ---------------------------------------------------------------------------
# Save, list, edit, delete
# ---------------------------------------------------------------------------
def list_memories(user_id: str = USER_ID) -> List[dict]:
    with database.connection() as conn:
        rows = conn.execute(
            f"SELECT {_COLUMNS} FROM memories WHERE user_id = ? ORDER BY id",
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def add_memory(
    text: str, category: Optional[str] = None, user_id: str = USER_ID
) -> Tuple[dict, bool]:
    """
    Save a memory. Returns (memory, created).
    created is False when the same memory was already saved.
    """
    if not get_memory_enabled(user_id):
        raise MemoryServiceError(
            "Memory is turned off right now. Turn it on in the Memory panel first."
        )

    cleaned = validate_text(text)
    chosen_category = _check_category(category, cleaned)
    now = _now()

    with database.connection() as conn:
        existing = conn.execute(
            f"SELECT {_COLUMNS} FROM memories "
            "WHERE user_id = ? AND lower(memory) = lower(?)",
            (user_id, cleaned),
        ).fetchone()
        if existing:
            return dict(existing), False

        count = conn.execute(
            "SELECT COUNT(*) FROM memories WHERE user_id = ?", (user_id,)
        ).fetchone()[0]
        if count >= MAX_MEMORIES:
            raise MemoryServiceError(
                f"My memory list is full ({MAX_MEMORIES}). Delete an old one first."
            )

        cursor = conn.execute(
            "INSERT INTO memories (user_id, memory, category, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, cleaned, chosen_category, now, now),
        )
        row = conn.execute(
            f"SELECT {_COLUMNS} FROM memories WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    return dict(row), True


def update_memory(
    memory_id: int,
    text: Optional[str] = None,
    category: Optional[str] = None,
    user_id: str = USER_ID,
) -> dict:
    """Change the text and/or category of a saved memory."""
    with database.connection() as conn:
        row = conn.execute(
            f"SELECT {_COLUMNS} FROM memories WHERE id = ? AND user_id = ?",
            (memory_id, user_id),
        ).fetchone()
        if row is None:
            raise MemoryServiceError("That memory was not found.", 404)

        new_text = row["memory"]
        if text is not None:
            new_text = validate_text(text)

        new_category = row["category"]
        if category:
            new_category = _check_category(category, new_text)

        conn.execute(
            "UPDATE memories SET memory = ?, category = ?, updated_at = ? "
            "WHERE id = ? AND user_id = ?",
            (new_text, new_category, _now(), memory_id, user_id),
        )
        updated = conn.execute(
            f"SELECT {_COLUMNS} FROM memories WHERE id = ?", (memory_id,)
        ).fetchone()
    return dict(updated)


def delete_memory(memory_id: int, user_id: str = USER_ID) -> bool:
    """Delete one memory. Returns True if something was deleted."""
    with database.connection() as conn:
        cursor = conn.execute(
            "DELETE FROM memories WHERE id = ? AND user_id = ?", (memory_id, user_id)
        )
        return cursor.rowcount > 0


def delete_all(user_id: str = USER_ID) -> int:
    """Delete every memory. Returns how many were deleted."""
    with database.connection() as conn:
        cursor = conn.execute("DELETE FROM memories WHERE user_id = ?", (user_id,))
        return cursor.rowcount


def find_memories(phrase: str, user_id: str = USER_ID) -> List[dict]:
    """Find memories that contain these words (ignores capital letters)."""
    wanted = clean_text(phrase).lower()
    if not wanted:
        return []
    return [m for m in list_memories(user_id) if wanted in m["memory"].lower()]


def memories_for_prompt(user_id: str = USER_ID) -> List[str]:
    """The memory texts that should be given to Adhav (empty if memory is off)."""
    if not get_memory_enabled(user_id):
        return []
    return [m["memory"] for m in list_memories(user_id)]