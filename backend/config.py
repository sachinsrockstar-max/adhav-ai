"""
Settings for ADHAV AI.
Reads the .env file once so every other file can import the values from here.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# This file lives in adhav-ai/backend/, so the project root is one folder up.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Read the .env file (if it exists) into environment variables.
load_dotenv(PROJECT_ROOT / ".env")

# Secret key and model name come from .env, never from the code.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash").strip() or "gemini-3.5-flash"

# How many recent messages we send to the AI each time.
# This keeps the conversation fast and within free limits.
MAX_HISTORY_MESSAGES = 20

# Longest message we accept from the user (in characters).
MAX_USER_MESSAGE_CHARS = 4000


def api_key_is_missing() -> bool:
    """Return True if the key is empty or still the placeholder text."""
    return (
        not GEMINI_API_KEY
        or GEMINI_API_KEY.startswith("paste-")
        or "your-gemini-key" in GEMINI_API_KEY
    )