"""
The /chat endpoint: receives a message and returns Adhav's reply.
It handles memory commands, picks the personality modes, and adds saved memories.
"""

from typing import List, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend import config
from backend.ai.client import AdhavAIError, create_client, get_reply
from backend.ai.modes import detect_modes
from backend.ai.prompts import build_instructions
from backend.memory import memory_service
from backend.memory.commands import parse_memory_command
from backend.memory.memory_service import MemoryServiceError

router = APIRouter()

# We create the Gemini client the first time it is needed, then reuse it.
_client = None


def _get_client():
    global _client
    if _client is None:
        _client = create_client()
    return _client


class HistoryItem(BaseModel):
    """One earlier message in the conversation."""

    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    """What the browser sends to us."""

    message: str = Field(..., description="The user's new message.")
    history: List[HistoryItem] = Field(
        default_factory=list,
        description="Earlier messages (optional).",
    )


class ChatResponse(BaseModel):
    """What we send back."""

    reply: str
    modes: List[str] = Field(
        default_factory=list,
        description="The personality modes used for this reply.",
    )


def _handle_memory_command(kind: str, text: str) -> str:
    """Run a memory command and return Adhav's reply. No AI call is needed."""
    try:
        if kind == "remember":
            memory, created = memory_service.add_memory(text)
            if created:
                return (
                    f"Got it 💚 I'll remember this: “{memory['memory']}”\n"
                    "You can see or edit it in the 🧠 Memory panel."
                )
            return "I already have that saved 😄"

        if kind == "list":
            if not memory_service.get_memory_enabled():
                return "Memory is turned off right now. You can turn it on in the 🧠 Memory panel."
            memories = memory_service.list_memories()
            if not memories:
                return "I haven't saved anything yet. Say “remember that ...” and I will 💚"
            lines = [f"{number}. {item['memory']}" for number, item in enumerate(memories, start=1)]
            return (
                "Here's what I have saved:\n"
                + "\n".join(lines)
                + "\n\nYou can edit or delete these in the 🧠 Memory panel."
            )

        if kind == "forget_all":
            return (
                "To delete everything, open the 🧠 Memory panel and press “Delete all”. "
                "I like that you stay in control 💚"
            )

        if kind == "forget":
            matches = memory_service.find_memories(text)
            if not matches:
                return f"I couldn't find anything saved that matches “{text}”."
            if len(matches) > 1:
                return (
                    f"I found {len(matches)} memories that match “{text}”. "
                    "Try a more specific phrase, or delete the right one in the 🧠 Memory panel."
                )
            memory_service.delete_memory(matches[0]["id"])
            return f"Done. I've forgotten: “{matches[0]['memory']}”"

    except MemoryServiceError as error:
        return str(error)

    return "Hmm, I didn't understand that memory command."


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    message = request.message.strip()

    if not message:
        raise HTTPException(status_code=400, detail="Please type a message.")

    if len(message) > config.MAX_USER_MESSAGE_CHARS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"That message is too long. "
                f"Please keep it under {config.MAX_USER_MESSAGE_CHARS} characters."
            ),
        )

    # 1. Is this a memory command like "remember that ..."?
    command = parse_memory_command(message)
    if command is not None:
        kind, text = command
        return ChatResponse(reply=_handle_memory_command(kind, text), modes=["memory"])

    # 2. Find the user's previous message (used when the new one is very short).
    previous_user_message = ""
    for item in reversed(request.history):
        if item.role == "user":
            previous_user_message = item.content
            break

    # 3. Pick the modes, load saved memories, and build Adhav's instructions.
    modes = detect_modes(message, previous_user_message)
    try:
        memories = memory_service.memories_for_prompt()
    except Exception:
        memories = []  # a memory problem must never break the chat
    instructions = build_instructions(modes, memories)

    # 4. Build the conversation: recent history + the new message.
    history = [{"role": item.role, "content": item.content} for item in request.history]
    history = history[-(config.MAX_HISTORY_MESSAGES - 1):]

    # The conversation we send must start with a user message.
    while history and history[0]["role"] == "assistant":
        history.pop(0)

    history.append({"role": "user", "content": message})

    try:
        client = _get_client()
        reply = get_reply(client, history, instructions)
    except AdhavAIError as error:
        raise HTTPException(status_code=503, detail=str(error))

    return ChatResponse(reply=reply, modes=modes)