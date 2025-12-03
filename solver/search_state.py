# solver/search_state.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .letter_feedback import Mark,Feedback


@dataclass(frozen=True)
class SearchState:
    """
    Immutable structure used as a hashable identifier for a node in the search tree.
    It stores the history of (guess, rating) pairs plus the number of valid candidates.
    """
    transcript: Tuple[Tuple[str, Tuple[Mark, ...]], ...]
    remaining: int

    @classmethod
    def create(cls, hist: Tuple[Tuple[str, Feedback], ...], count: int) -> "SearchState":
        # Convert inner feedback lists into tuples to ensure hashability.
        bundled = tuple((w, tuple(r)) for w, r in hist)
        return cls(transcript=bundled, remaining=count)
