"""
ADHAV AI - Stage 1: terminal chatbot.

Run from the project root folder (adhav-ai) with:
    python -m backend.main
"""

import sys

from backend import config
from backend.ai.client import AdhavAIError, create_client, get_reply


def make_console_friendly() -> None:
    """Let the Windows terminal print emojis and Tamil text without crashing."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdin.reconfigure(encoding="utf-8")
    except Exception:
        pass  # If this fails, the chat still works. Emojis may look odd.


def main() -> None:
    make_console_friendly()

    # Check the API key before starting the chat.
    try:
        client = create_client()
    except AdhavAIError as error:
        print(f"\n[ERROR] {error}\n")
        sys.exit(1)

    # SHORT-TERM MEMORY: the messages of this session only.
    history = []

    print("=" * 50)
    print("  ADHAV AI - your personal AI companion")
    print("  Type 'exit' or 'quit' to leave.")
    print("=" * 50)

    while True:
        try:
            user_text = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nAdhav: Bye for now! Take care 💚")
            break

        # Empty message: just ask again.
        if not user_text:
            print("Adhav: (You didn't type anything. Say something 😄)")
            continue

        if user_text.lower() in ("exit", "quit"):
            print("\nAdhav: Bye for now! Take care 💚")
            break

        # Very long message: ask the user to shorten it.
        if len(user_text) > config.MAX_USER_MESSAGE_CHARS:
            print(
                f"Adhav: That's a long one! Please keep it under "
                f"{config.MAX_USER_MESSAGE_CHARS} characters."
            )
            continue

        history.append({"role": "user", "content": user_text})
        recent_history = history[-config.MAX_HISTORY_MESSAGES:]

        try:
            reply = get_reply(client, recent_history)
        except AdhavAIError as error:
            print(f"\n[ERROR] {error}")
            history.pop()  # remove the message that failed
            continue

        history.append({"role": "assistant", "content": reply})
        print(f"\nAdhav: {reply}")


if __name__ == "__main__":
    main()