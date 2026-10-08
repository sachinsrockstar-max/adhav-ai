"""
Talks to the Google Gemini API and returns Adhav's reply.
All errors are converted into one friendly error type: AdhavAIError.
"""

from typing import Optional

import httpx
from google import genai
from google.genai import errors, types

from backend import config
from backend.ai.prompts import build_instructions


class AdhavAIError(Exception):
    """An error with a beginner-friendly message that is safe to show."""


def create_client() -> genai.Client:
    """Create the Gemini client, or raise a friendly error if no key is set."""
    if config.api_key_is_missing():
        raise AdhavAIError(
            "Your Gemini API key is missing.\n"
            "1. Open the .env file in the adhav-ai folder.\n"
            "2. Set:  GEMINI_API_KEY=your-real-key\n"
            "3. Save the file and run this program again."
        )
    return genai.Client(api_key=config.GEMINI_API_KEY)


def _to_gemini_contents(history: list) -> list:
    """
    Convert our simple history into Gemini's format.
    Ours uses the role "assistant". Gemini calls that role "model".
    """
    contents = []
    for message in history:
        role = "model" if message["role"] == "assistant" else "user"
        contents.append(
            types.Content(role=role, parts=[types.Part(text=message["content"])])
        )
    return contents


def get_reply(client: genai.Client, history: list, instructions: Optional[str] = None) -> str:
    """
    Send the conversation so far to Gemini and return Adhav's reply as text.

    history looks like:
        [{"role": "user", "content": "hi"},
         {"role": "assistant", "content": "Heyy!"}, ...]

    instructions is the personality text. If it is not given,
    we use the persona only.
    """
    system_text = instructions or build_instructions([])

    try:
        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=_to_gemini_contents(history),
            config=types.GenerateContentConfig(system_instruction=system_text),
        )
    except errors.APIError as error:
        code = getattr(error, "code", None)
        if code in (401, 403) or "API key" in str(error):
            raise AdhavAIError(
                "Gemini rejected your API key. Check .env for typos, "
                "extra spaces or quotes, or create a new key at aistudio.google.com."
            )
        if code == 404:
            raise AdhavAIError(
                f"The model '{config.GEMINI_MODEL}' was not found.\n"
                "Check ai.google.dev/gemini-api/docs/models for a current model "
                "name and change GEMINI_MODEL in .env."
            )
        if code == 429:
            raise AdhavAIError(
                "Free limit reached for now. Wait a minute and try again. "
                "If it keeps happening, you may have used today's free quota."
            )
        if code is not None and code >= 500:
            raise AdhavAIError(
                "Google's server is busy right now. Please try again in a moment."
            )
        raise AdhavAIError(f"Gemini returned an error (code {code}): {error}")
    except (httpx.ConnectError, httpx.TimeoutException):
        raise AdhavAIError("Could not reach Google. Check your internet connection.")
    except Exception as error:  # last safety net
        raise AdhavAIError(f"Something unexpected went wrong: {error}")

    reply = (response.text or "").strip()
    if not reply:
        raise AdhavAIError(
            "Adhav sent back an empty reply (it may have been blocked). "
            "Please try rephrasing."
        )
    return reply