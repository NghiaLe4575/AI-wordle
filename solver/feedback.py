# solver/feedback.py
from __future__ import annotations
from enum import IntEnum
from typing import Iterable, List

class Mark(IntEnum):
    MISS = 0       # "-"
    PRESENT = 1    # "Y"
    CORRECT = 2    # "G"

    def to_color(self) -> str:
        return {
            Mark.CORRECT: "#6aaa64",
            Mark.PRESENT: "#c9b458",
            Mark.MISS: "#787c7e",
        }[self]

    def to_symbol(self) -> str:
        return {
            Mark.CORRECT: "G",
            Mark.PRESENT: "Y",
            Mark.MISS: "-",
        }[self]

Feedback = List[Mark]

def evaluate_guess(answer: str, guess: str) -> Feedback:
    """Return Wordle feedback, equivalent to the official rules."""
    answer = answer.lower()
    guess = guess.lower()
    n = len(guess)

    feedback = [Mark.MISS] * n
    counts = {}

    # Count letters in answer
    for ch in answer:
        counts[ch] = counts.get(ch, 0) + 1

    # First pass: GREENS
    for i in range(n):
        if guess[i] == answer[i]:
            feedback[i] = Mark.CORRECT
            counts[guess[i]] -= 1

    # Second pass: YELLOWS
    for i in range(n):
        if feedback[i] is Mark.CORRECT:
            continue
        g = guess[i]
        if counts.get(g, 0) > 0:
            feedback[i] = Mark.PRESENT
            counts[g] -= 1

    return feedback

def feedback_to_string(feedback: Iterable[Mark]) -> str:
    return "".join(m.to_symbol() for m in feedback)
