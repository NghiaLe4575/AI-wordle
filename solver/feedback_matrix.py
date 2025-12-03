# solver/feedback_matrix.py
from __future__ import annotations

import hashlib
import pickle
import time
from pathlib import Path
from typing import Sequence

from .letter_feedback import score_guess, Mark


def pack_marks(marks) -> int:
    """
    Encode a feedback row into a base-3 integer.
    Mark values are already 0,1,2 from IntEnum.
    """
    code = 0
    for m in marks:
        code = code * 3 + int(m)
    return code


def unpack_marks(code: int, size: int = 5):
    """Reverse of pack_marks(). Convert integer → list of Mark."""
    out = [Mark.ABSENT] * size
    for pos in range(size - 1, -1, -1):
        out[pos] = Mark(code % 3)
        code //= 3
    return out


class FeedbackMatrix:
    """
    Precomputed all-pairs feedback table.
    Stores compact integer encodings instead of full mark lists.
    Uses pickle for fast loading.
    """

    def __init__(self, vocab: Sequence[str], folder: Path | None = None, verbose: bool = True):
        self.words = [w.lower() for w in vocab]
        self.index = {w: i for i, w in enumerate(self.words)}
        self.count = len(self.words)
        self.verbose = verbose

        # choose storage directory
        if folder is None:
            folder = Path(__file__).parent.parent / ".cache"
        folder.mkdir(parents=True, exist_ok=True)

        # hash word list for a unique filename
        checksum = hashlib.md5("".join(sorted(self.words)).encode()).hexdigest()[:8]
        final = folder / f"fbmat_{self.count}_{checksum}.pkl"
        temp = folder / f"fbmat_{self.count}_{checksum}.pkl.tmp"

        # Cleanup of leftover .broken files
        for p in folder.glob(f"fbmat_{self.count}_{checksum}.pkl*"):
            if ".broken" in str(p):
                try:
                    p.unlink()
                except Exception:
                    pass

        # Try load existing file
        if final.exists():
            if self._validate(final):
                if verbose:
                    print(f"[FeedbackMatrix] Loaded: {final.name}")
                with open(final, "rb") as f:
                    self.table = pickle.load(f)
                return
            else:
                corrupted = final.with_suffix(".pkl.broken")
                try:
                    final.replace(corrupted)
                except Exception:
                    try:
                        final.unlink()
                    except Exception:
                        pass

        # Remove stale temp file
        if temp.exists():
            try:
                temp.unlink()
            except Exception:
                pass

        # Build table fresh
        if verbose:
            print(f"[FeedbackMatrix] Generating table ({self.count}×{self.count}) → {final.name}")

        start = time.time()
        table = []

        try:
            for i, g in enumerate(self.words):
                row = []
                for t in self.words:
                    encoded = pack_marks(score_guess(t, g))
                    row.append(encoded)
                table.append(row)

                # Progress updates
                if (i + 1) % 100 == 0 or (i + 1) == self.count:
                    if verbose:
                        pct = (i + 1) * 100 / self.count
                        elapsed = time.time() - start
                        print(f"   {i+1}/{self.count} rows ({pct:.1f}%), {elapsed:.1f}s")

            # Save to temporary file
            with open(temp, "wb") as f:
                pickle.dump(table, f, protocol=pickle.HIGHEST_PROTOCOL)

            # atomic rename
            temp.replace(final)

            if verbose:
                size_mb = final.stat().st_size / (1024 * 1024)
                print(f"[FeedbackMatrix] Build complete in {time.time() - start:.1f}s ({size_mb:.2f} MB)")

        except Exception as e:
            # ensure no half-built file remains
            try:
                if temp.exists():
                    temp.unlink()
            except Exception:
                pass
            raise RuntimeError(f"FeedbackMatrix failed to build: {e}")

        # Final load
        with open(final, "rb") as f:
            self.table = pickle.load(f)

    # ----------------------------------------------

    def _validate(self, path: Path) -> bool:
        """Quick sanity check for a previously saved table."""
        try:
            with open(path, "rb") as f:
                tbl = pickle.load(f)

            if not isinstance(tbl, list) or len(tbl) != self.count:
                return False

            if not all(isinstance(row, list) and len(row) == self.count for row in tbl):
                return False

            # Check encoding range
            for row in tbl:
                for v in row:
                    if not isinstance(v, int) or v < 0:
                        return False
            return True

        except Exception:
            return False

    # ----------------------------------------------

    def get_feedback(self, guess: str, target: str):
        """Return decoded feedback."""
        gi = self.index[guess.lower()]
        ti = self.index[target.lower()]
        return unpack_marks(self.table[gi][ti])

    def get_feedback_idx(self, gi: int, ti: int):
        """Index-based access (fast path)."""
        return unpack_marks(self.table[gi][ti])
