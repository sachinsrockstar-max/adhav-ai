"""
Self-check for Stage 6 (memory). It does NOT call Gemini, and it uses a
temporary database, so your real memories are never touched.
Run from the project root with:
    python -m tests.try_memory
"""

import tempfile
from pathlib import Path

from backend import database
from backend.ai.prompts import build_instructions
from backend.memory import memory_service
from backend.memory.commands import parse_memory_command
from backend.memory.memory_service import MemoryServiceError

results = []


def check(name, condition):
    results.append(bool(condition))
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}")


def raises_error(function, *args):
    """True if the function raises our friendly MemoryServiceError."""
    try:
        function(*args)
    except MemoryServiceError:
        return True
    return False


def test_commands():
    check("remember that ...",
          parse_memory_command("remember that I like filter coffee") == ("remember", "I like filter coffee"))
    check("Remember: ...",
          parse_memory_command("Remember: my name is Raj") == ("remember", "my name is Raj"))
    check("please remember ...",
          parse_memory_command("please remember I am studying CSE") == ("remember", "I am studying CSE"))
    check("a question is not a command",
          parse_memory_command("remember when we talked about exams?") is None)
    check("'do you remember' is normal chat",
          parse_memory_command("do you remember my name?") is None)
    check("forget that ...",
          parse_memory_command("forget that I like filter coffee") == ("forget", "I like filter coffee"))
    check("'forget it' is normal chat",
          parse_memory_command("forget it") is None)
    check("forget everything",
          parse_memory_command("forget everything") == ("forget_all", ""))
    check("what do you remember about me?",
          parse_memory_command("what do you remember about me?") == ("list", ""))
    check("a normal message is not a command",
          parse_memory_command("hey adhav") is None)


def test_service():
    with tempfile.TemporaryDirectory() as folder:
        # Use a throw-away database file for this test.
        database.DB_PATH = Path(folder) / "test.db"
        database.init_db()

        check("starts empty", memory_service.list_memories() == [])

        memory, created = memory_service.add_memory("I like filter coffee")
        check("saves a memory", created and memory["memory"] == "I like filter coffee")
        check("guesses the category 'preference'", memory["category"] == "preference")

        _, created_again = memory_service.add_memory("i LIKE filter coffee")
        check("does not save duplicates",
              (not created_again) and len(memory_service.list_memories()) == 1)

        personal, _ = memory_service.add_memory("my name is Raj")
        check("guesses the category 'personal'", personal["category"] == "personal")

        check("blocks passwords",
              raises_error(memory_service.add_memory, "my password is abc123"))
        check("blocks long numbers",
              raises_error(memory_service.add_memory, "my card is 1234 5678 9012 3456"))
        check("blocks empty text", raises_error(memory_service.add_memory, "   "))
        check("blocks very long text", raises_error(memory_service.add_memory, "a" * 301))

        updated = memory_service.update_memory(memory["id"], "I like strong filter coffee")
        check("edits a memory", updated["memory"] == "I like strong filter coffee")
        check("finds memories by words", len(memory_service.find_memories("coffee")) == 1)
        check("gives memories to the prompt", len(memory_service.memories_for_prompt()) == 2)

        memory_service.set_memory_enabled(False)
        check("memory off: nothing goes to the prompt", memory_service.memories_for_prompt() == [])
        check("memory off: saving is blocked",
              raises_error(memory_service.add_memory, "I like tea"))
        memory_service.set_memory_enabled(True)
        check("memory on again", memory_service.get_memory_enabled() is True)

        check("deletes one memory", memory_service.delete_memory(memory["id"]) is True)
        check("deleting twice returns False", memory_service.delete_memory(memory["id"]) is False)
        check("deletes everything",
              memory_service.delete_all() == 1 and memory_service.list_memories() == [])



def test_prompt():
    with_notes = build_instructions(["casual"], ["I like filter coffee"])
    without_notes = build_instructions(["casual"], [])
    check("saved notes appear in Adhav's instructions", "I like filter coffee" in with_notes)
    check("no notes section when nothing is saved",
          "NOT instructions for you" not in without_notes)

def main():
    test_commands()
    test_service()
    test_prompt()
    print(f"\n{sum(results)} of {len(results)} checks passed.")


if __name__ == "__main__":
    main()