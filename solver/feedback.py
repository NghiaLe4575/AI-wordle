# solver/feedback.py
from __future__ import annotations
from enum import Enum, auto
from typing import Iterable, List

class Mark(Enum):
    MISS = auto()
    PRESENT = auto()
    CORRECT = auto()

    def to_color(self) -> str:
        if self is Mark.CORRECT:
            return "#6aaa64"
        if self is Mark.PRESENT:
            return "#c9b458"
        return "#787c7e"

    def to_symbol(self) -> str:
        if self is Mark.CORRECT:
            return "G"
        if self is Mark.PRESENT:
            return "Y"
        return "-"

Feedback = List[Mark]

def evaluate_guess(answer: str, guess: str) -> Feedback:
    """Return Wordle feedback (list of Mark) for guess when the answer is `answer`."""
    answer = answer.lower()
    guess = guess.lower()
    feedback: Feedback = [Mark.MISS] * len(guess)
    counts: dict[str, int] = {}
    for ch in answer:
        counts[ch] = counts.get(ch, 0) + 1

    # Greens first
    for i, (g, a) in enumerate(zip(guess, answer)):
        if g == a:
            feedback[i] = Mark.CORRECT
            counts[g] -= 1

    # Yellows next
    for i, g in enumerate(guess):
        if feedback[i] is Mark.CORRECT:
            continue
        if counts.get(g, 0) > 0:
            feedback[i] = Mark.PRESENT
            counts[g] -= 1

    return feedback

def feedback_to_string(feedback: Iterable[Mark]) -> str:
    return "".join(mark.to_symbol() for mark in feedback)
