# solver/state.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple
from .feedback import Mark, Feedback

@dataclass(frozen=True)
class CompactState:
    """Compact hashable representation of search state from history signature."""
    history: Tuple[Tuple[str, Tuple[Mark, ...]], ...]
    remaining_count: int

    @classmethod
    def from_history(cls, history: Tuple[Tuple[str, Feedback], ...], remaining: int) -> "CompactState":
        compact = tuple((guess, tuple(feedback)) for guess, feedback in history)
        return cls(history=compact, remaining_count=remaining)
