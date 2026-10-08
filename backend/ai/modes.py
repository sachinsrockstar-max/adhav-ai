"""
Picks which "modes" Adhav should use for a message, and holds the text for each mode.

How the detection works: we look for simple keywords (like "exam" or "error").
It is fast and free. It is not perfect, and the persona still works if it misses.
"""

import re
from typing import List

# ---------------------------------------------------------------------------
# 1. WORDS THAT TURN EACH MODE ON
# ---------------------------------------------------------------------------


def _words(options: List[str]) -> "re.Pattern":
    """Build a case-insensitive pattern that matches whole words only."""
    return re.compile(r"\b(?:" + "|".join(options) + r")\b", re.IGNORECASE)


_EMOTIONAL = _words([
    r"sad", r"depressed", r"depressing", r"lonely", r"alone", r"cry", r"crying",
    r"cried", r"anxious", r"anxiety", r"stressed", r"stress", r"worried", r"worry",
    r"scared", r"afraid", r"hurt", r"upset", r"tired", r"exhausted", r"overwhelmed",
    r"hopeless", r"angry", r"frustrated", r"nervous", r"panic", r"feeling low",
    r"feeling bad", r"feel bad", r"bad day", r"mood off", r"tension",
    r"kavalai", r"kashtam", r"kastam", r"bayama", r"bayam",
    r"suicide", r"suicidal", r"kill myself", r"end my life", r"want to die",
    r"self[- ]harm",
])

_STUDY = _words([
    r"exams?", r"syllabus", r"revision", r"revis(?:e|ing)",
    r"stud(?:y|ying|ies|ied)", r"mcqs?", r"\d+[- ]?marks?", r"semester", r"viva",
    r"mock tests?", r"time ?table", r"previous year", r"important questions",
    r"internals?", r"preparing", r"preparation",
])

_CODING = _words([
    r"codes?", r"coding", r"programs?", r"programming", r"python", r"java",
    r"javascript", r"html", r"css", r"sql", r"git(?:hub)?", r"debug(?:ging)?",
    r"bugs?", r"compil(?:e|er|ing)", r"syntax", r"functions?", r"algorithms?",
    r"arrays?", r"loops?", r"pointers?", r"recursion", r"linked lists?",
    r"stacks?", r"queues?", r"api", r"fastapi", r"traceback", r"exceptions?",
    r"errors?", r"palindrome", r"factorial", r"fibonacci",
])

# Patterns that need special characters, so they are not wrapped in \b ... \b
_CODING_EXTRA = re.compile(
    r"```|#include|c\+\+|\bin c\b|\bc (?:program|programming|language|code)\b"
    r"|\bdef \w+\(|\bconsole\.log\b|\bpublic static void\b",
    re.IGNORECASE,
)

_PROBLEM = _words([
    r"solve", r"calculate", r"equations?", r"integral", r"derivative",
    r"probability", r"matrix", r"matrices", r"algebra", r"geometry",
    r"trigonometry", r"percentage", r"simplify", r"prove", r"theorem",
    r"maths?", r"mathematics", r"puzzle", r"riddle",
])

_PROBLEM_EXTRA = re.compile(r"\d\s*[+*^×÷]\s*\d")


def _scan(text: str) -> List[str]:
    """Return the modes that match this text (in priority order)."""
    found = []
    if _EMOTIONAL.search(text):
        found.append("emotional")
    if _STUDY.search(text):
        found.append("study")
    if _CODING.search(text) or _CODING_EXTRA.search(text):
        found.append("coding")
    if _PROBLEM.search(text) or _PROBLEM_EXTRA.search(text):
        found.append("problem")
    return found


def detect_modes(latest_message: str, previous_user_message: str = "") -> List[str]:
    """
    Decide which modes to use.

    1. Look at the latest message.
    2. If nothing matches (for example the user just says "why?"), look at the
       user's previous message so the conversation keeps its mood.
    3. If still nothing matches, use "casual".
    """
    modes = _scan(latest_message)
    if not modes and previous_user_message:
        modes = _scan(previous_user_message)
    if not modes:
        modes = ["casual"]
    return modes


# ---------------------------------------------------------------------------
# 2. THE TEXT FOR EACH MODE
# ---------------------------------------------------------------------------

MODE_PROMPTS = {
    "casual": """
CASUAL CHAT MODE
- Talk like a close friend. Keep replies short (1 to 4 sentences) and match
  the user's energy and message length.
- Do not list what you can do, and do not lecture. Be curious about their day.
- Tease lightly if the mood is playful.
""".strip(),

    "emotional": """
EMOTIONAL SUPPORT MODE
- The user may be hurting, stressed or scared. LISTEN FIRST.
- Do NOT start with a list of advice or tips. Do not say "calm down".
- Reflect back, in your own words, what you heard. Be soft and human.
- Keep it fairly short. Ask ONE gentle question, such as "What happened?" or
  "Do you want to tell me more?"
- Offer small practical steps only after they have shared, or if they ask.
- Skip jokes and emojis unless the user lightens the mood first.
""".strip(),

    "study": """
STUDY PARTNER MODE
- Be a patient study partner. Explain topics simply, with small examples.
- Useful things you can do: make a study schedule, create MCQs, 2-mark,
  5-mark and scenario questions, run a mock test, check answers, explain
  mistakes, write short revision notes, find weak topics, and prioritise the
  most important topics.
- Ask for the subject, how much time is left, and the syllabus if you need
  them, but ask only one thing at a time.
- If the user is scared or stressed, calm them first, then make the plan.
- When you quiz them, ask one question at a time and wait for the answer.
""".strip(),

    "coding": """
CODING MENTOR MODE
- Be a friendly coding mentor for a beginner.
- Teaching a concept: 1) explain it simply, 2) give small code, 3) explain the
  code line by line, 4) show sample input and output, 5) mention common
  mistakes, 6) give one small practice problem.
- Debugging: 1) read their code, 2) find the error, 3) explain why it
  happened, 4) give the corrected code, 5) explain the fix.
- Put all code inside lines of three backticks (```). Give complete, runnable
  code, not fragments with missing parts.
- If the user's code is missing, ask them to paste it.
""".strip(),

    "problem": """
PROBLEM SOLVING MODE
- Understand the problem, break it into smaller pieces, explain the concept
  simply, solve step by step, then state the final answer clearly.
- Add a short example if it helps. Do not over-complicate simple problems.
- Double-check your arithmetic before giving the final answer.
""".strip(),
}