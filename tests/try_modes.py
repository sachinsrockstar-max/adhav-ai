"""
A quick self-check for the mode detection. It does NOT call Gemini, so it is free.
Run from the project root with:
    python -m tests.try_modes
"""

from backend.ai.modes import detect_modes

# (latest message, previous user message, expected modes)
CASES = [
    ("hey adhav", "", ["casual"]),
    ("thanks", "", ["casual"]),
    ("I feel sad today", "", ["emotional"]),
    ("I want to die", "", ["emotional"]),
    ("my python code has an error", "", ["coding"]),
    ("explain palindrome in C", "", ["coding"]),
    ("I have an exam tomorrow", "", ["study"]),
    ("I'm scared about tomorrow's exam", "", ["emotional", "study"]),
    ("Study plan for tomorrow, I'm so stressed", "", ["emotional", "study"]),
    ("I feel bad because my code has a bug", "", ["emotional", "coding"]),
    ("solve 2 + 3 * 4", "", ["problem"]),
    ("why?", "my code has an error", ["coding"]),
]


def main() -> None:
    passed = 0
    for latest, previous, expected in CASES:
        got = detect_modes(latest, previous)
        ok = got == expected
        passed += 1 if ok else 0
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {latest!r:50} -> {got}")
        if not ok:
            print(f"        expected: {expected}")
    print(f"\n{passed} of {len(CASES)} checks passed.")


if __name__ == "__main__":
    main()