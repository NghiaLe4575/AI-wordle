# solver/feedback_table.py
from __future__ import annotations
import hashlib
import pickle
import random
from pathlib import Path
from typing import Dict, Sequence, Tuple

from .feedback import Feedback, evaluate_guess

class FeedbackTable:
    """Sparse precomputed feedback lookup with disk caching."""

    def __init__(self, word_list: Sequence[str], max_connections: int = 200, cache_dir: Path | None = None):
        self._table: Dict[Tuple[str, str], Feedback] = {}
        self._max_connections = max_connections

        word_list_sorted = sorted(w.lower() for w in word_list)
        word_hash = hashlib.md5("".join(word_list_sorted).encode()).hexdigest()[:8]

        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent / ".cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f"feedback_table_{len(word_list)}_{word_hash}_sparse{max_connections}.pkl"

        if cache_file.exists():
            try:
                with open(cache_file, "rb") as f:
                    self._table = pickle.load(f)
                print(f"[FeedbackTable] loaded {len(self._table)} entries from cache.")
                return
            except Exception as e:
                print(f"[FeedbackTable] failed loading cache ({e}), rebuilding...")

        # Build sparse table
        rng = random.Random(42)
        word_list_lower = [w.lower() for w in word_list]
        n = len(word_list_lower)
        print(f"[FeedbackTable] building sparse table for {n} words (max_connections={max_connections})...")
        for i, guess in enumerate(word_list_lower):
            # self mapping
            self._table[(guess, guess)] = evaluate_guess(guess, guess)
            # sample other targets
            others = word_list_lower[:i] + word_list_lower[i+1:]
            sample_size = min(max_connections - 1, len(others))
            if sample_size > 0:
                for target in rng.sample(others, sample_size):
                    self._table[(guess, target)] = evaluate_guess(target, guess)
            if (i + 1) % 1000 == 0:
                print(f"  progress: {i+1}/{n}")
        try:
            with open(cache_file, "wb") as f:
                pickle.dump(self._table, f, protocol=pickle.HIGHEST_PROTOCOL)
            print(f"[FeedbackTable] saved cache: {cache_file.name}")
        except Exception as e:
            print(f"[FeedbackTable] cache save failed: {e}")

    def get_feedback(self, guess: str, target: str) -> Feedback:
        key = (guess.lower(), target.lower())
        if key in self._table:
            return self._table[key]
        # fallback
        return evaluate_guess(target, guess)
