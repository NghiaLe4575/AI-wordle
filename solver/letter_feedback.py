# solver/letter_feedback.py
from __future__ import annotations

from enum import IntEnum
from typing import Iterable, List


class Mark(IntEnum):
    """Symbolic mark used in Wordle-style scoring."""
    ABSENT = 0     # "-"
    PARTIAL = 1    # "Y"
    EXACT = 2      # "G"

    def glyph(self) -> str:
        """Return a one-character symbol for display."""
        return {Mark.EXACT: "G", Mark.PARTIAL: "Y", Mark.ABSENT: "-"}[self]

    def color_hex(self) -> str:
        """Return a color code similar to the official game UI."""
        return {
            Mark.EXACT: "#6aaa64",
            Mark.PARTIAL: "#c9b458",
            Mark.ABSENT: "#787c7e",
        }[self]


# a "Feedback" object is simply a list of marks
Feedback = List[Mark]


def score_guess(secret: str, attempt: str) -> Feedback:
    """
    Compute Wordle feedback according to the exact official rules.
    Returns a list of Mark(Enum).
    """
    s = secret.lower()
    g = attempt.lower()
    length = len(g)

    result = [Mark.ABSENT] * length
    remaining = {}

    # Count characters of secret
    for ch in s:
        remaining[ch] = remaining.get(ch, 0) + 1

    # Pass 1: confirmed matches (greens)
    for i in range(length):
        if g[i] == s[i]:
            result[i] = Mark.EXACT
            remaining[g[i]] -= 1

    # Pass 2: present-but-wrong-position matches (yellows)
    for i in range(length):
        if result[i] is Mark.EXACT:
            continue
        letter = g[i]
        if remaining.get(letter, 0) > 0:
            result[i] = Mark.PARTIAL
            remaining[letter] -= 1

    return result


def feedback_string(marks: Iterable[Mark]) -> str:
    """Convert marks to a single ASCII string."""
    return "".join(m.glyph() for m in marks)
