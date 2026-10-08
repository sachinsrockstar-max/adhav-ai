"""
Understands simple memory commands typed in the chat, for example:
    remember that I like filter coffee
    forget filter coffee
    what do you remember about me?

This is plain pattern matching. It needs no AI call, so it is free, and it never
saves anything by accident: Adhav only saves what the user clearly asks for.
"""

import re
from typing import Optional, Tuple

_REMEMBER = re.compile(
    r"^\s*(?:please\s+)?(?:remember|save\s+(?:to|in)\s+memory|add\s+to\s+memory)\b"
    r"(?:\s+that)?\s*[:,\-]?\s*(.+)$",
    re.IGNORECASE | re.DOTALL,
)

_FORGET = re.compile(
    r"^\s*(?:please\s+)?forget\b(?:\s+that)?\s*[:,\-]?\s*(.+)$",
    re.IGNORECASE | re.DOTALL,
)

_LIST = re.compile(
    r"^\s*(?:please\s+)?(?:"
    r"what\s+do\s+you\s+remember(?:\s+about\s+me)?"
    r"|what\s+do\s+you\s+know\s+about\s+me"
    r"|what\s+(?:have\s+i\s+told|did\s+i\s+tell)\s+you\s+to\s+remember"
    r"|(?:show|list)\s+(?:me\s+)?(?:all\s+)?(?:my\s+)?memor(?:y|ies)"
    r")\s*[?.!]*\s*$",
    re.IGNORECASE,
)

# Messages that start like a command but are really just normal chat.
_QUESTION_STARTS = ("when ", "how ", "what ", "why ", "where ", "who ", "do you ", "did you ", "if ")
_REMEMBER_FILLER = {"that", "this", "it", "me", "to"}
_FORGET_FILLER = {"it", "about it", "that", "this", "me", "never mind", "nothing"}
_FORGET_ALL = {"everything", "all", "everything about me", "all of it", "all memories", "all my memories"}


def parse_memory_command(message: str) -> Optional[Tuple[str, str]]:
    """
    Returns (kind, text) if the message is a memory command, otherwise None.
    kind is one of: "remember", "forget", "forget_all", "list".
    """
    text = (message or "").strip()
    if not text:
        return None

    if _LIST.match(text):
        return ("list", "")

    match = _REMEMBER.match(text)
    if match:
        rest = match.group(1).strip()
        lowered = rest.lower()
        if text.endswith("?") or lowered.startswith(_QUESTION_STARTS) or lowered in _REMEMBER_FILLER:
            return None
        return ("remember", rest)

    match = _FORGET.match(text)
    if match:
        rest = match.group(1).strip(" .!")
        lowered = rest.lower()
        if lowered in _FORGET_ALL:
            return ("forget_all", "")
        if not rest or lowered in _FORGET_FILLER:
            return None
        return ("forget", rest)

    return None