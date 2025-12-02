# solver/feedback_table.py
from __future__ import annotations
import hashlib
import pickle
from pathlib import Path
from typing import Sequence
import time

from .feedback import evaluate_guess, Mark

def encode_feedback(fb) -> int:
    """Encode N feedback marks as a base-3 integer (0..3^N-1)."""
    out = 0
    for m in fb:
        out = out * 3 + int(m)   # Mark is IntEnum 0/1/2
    return out

def decode_feedback(code: int, length: int = 5):
    """Decode base-3 integer (0..242) into list[Mark]."""
    out = [Mark.MISS] * length
    for i in range(length - 1, -1, -1):
        out[i] = Mark(code % 3)
        code //= 3
    return out

class FeedbackTable:
    """
    Compact feedback table backed by pickle-compressed base-3 encoded integers.
    - Each entry is a uint8 encoding of feedback in base-3.
    - Uses pickle for space efficiency.
    - Uses a temp file + atomic replace to avoid partial/poisoned files.
    """

    def __init__(self, word_list: Sequence[str], cache_dir: Path | None = None, verbose: bool = True):
        self.word_list = [w.lower() for w in word_list]
        self.word_to_idx = {w: i for i, w in enumerate(self.word_list)}
        self.n = len(self.word_list)
        self.verbose = verbose

        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent / ".cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        wl_sorted = sorted(self.word_list)
        word_hash = hashlib.md5("".join(wl_sorted).encode()).hexdigest()[:8]
        final_path = cache_dir / f"fbtable_{self.n}_{word_hash}.pkl"
        tmp_path = cache_dir / f"fbtable_{self.n}_{word_hash}.pkl.tmp"

        # Clean up any .broken files from previous failed attempts
        for broken_file in cache_dir.glob(f"fbtable_{self.n}_{word_hash}.pkl*"):
            if ".broken" in str(broken_file):
                try:
                    broken_file.unlink()
                except Exception:
                    pass

        # If final file exists, validate and load it
        if final_path.exists():
            if self._is_valid_pickle(final_path):
                if self.verbose:
                    print(f"[FeedbackTable] Loading cache: {final_path.name}")
                with open(final_path, 'rb') as f:
                    self.table = pickle.load(f)
                return
            else:
                # corrupted / old format: remove it
                bad_path = final_path.with_suffix('.pkl.broken')
                try:
                    final_path.replace(bad_path)
                    if self.verbose:
                        print(f"[FeedbackTable] Found invalid cache; moved {final_path.name} -> {bad_path.name}")
                except Exception:
                    try:
                        final_path.unlink()
                        if self.verbose:
                            print(f"[FeedbackTable] Removed invalid cache: {final_path.name}")
                    except Exception as e:
                        raise RuntimeError(f"Cannot remove invalid cache file {final_path}: {e}")

        # If temp file exists (previous partial build), remove it
        if tmp_path.exists():
            try:
                tmp_path.unlink()
                if self.verbose:
                    print(f"[FeedbackTable] Removed leftover tmp file: {tmp_path.name}")
            except Exception:
                try:
                    tmp_inspect = tmp_path.with_suffix('.tmp.broken')
                    tmp_path.replace(tmp_inspect)
                    if self.verbose:
                        print(f"[FeedbackTable] Renamed leftover tmp -> {tmp_inspect.name}")
                except Exception:
                    pass

        # Build into tmp file then atomically rename to final_path
        if self.verbose:
            print(f"[FeedbackTable] Building feedback table ({self.n}×{self.n}) -> {final_path.name} ...")
        start = time.time()
        
        try:
            # Build table as 2D list of encoded integers
            table = []
            for i, guess in enumerate(self.word_list):
                row = []
                for j, target in enumerate(self.word_list):
                    fb = evaluate_guess(target, guess)
                    row.append(encode_feedback(fb))
                table.append(row)

                # provide progress every 100 rows or on final
                if (i + 1) % 100 == 0 or (i + 1) == self.n:
                    elapsed = time.time() - start
                    rows_done = i + 1
                    pct = rows_done / self.n * 100
                    if self.verbose:
                        print(f"  built rows {rows_done}/{self.n} ({pct:.1f}%) elapsed {elapsed:.1f}s")

            # Write to tmp file with pickle (highest compression)
            with open(tmp_path, 'wb') as f:
                pickle.dump(table, f, protocol=pickle.HIGHEST_PROTOCOL)

            # atomic replace: move tmp -> final
            tmp_path.replace(final_path)
            if self.verbose:
                elapsed = time.time() - start
                final_size_mb = final_path.stat().st_size / (1024 * 1024)
                print(f"[FeedbackTable] Build complete ({elapsed:.1f}s). Saved to {final_path.name} ({final_size_mb:.2f} MB)")

        except Exception as e:
            # ensure we don't leave a corrupted tmp file
            try:
                if tmp_path.exists():
                    tmp_path.unlink()
            except Exception:
                pass
            raise RuntimeError(f"[FeedbackTable] Failed building table: {e}") from e

        # Load final file
        try:
            with open(final_path, 'rb') as f:
                self.table = pickle.load(f)
        except Exception as e:
            try:
                final_path.unlink()
            except Exception:
                pass
            raise RuntimeError(
                f"[FeedbackTable] Failed loading newly built cache. "
                f"Deleted {final_path.name}. Try building again.\n"
                f"Original error: {e}"
            ) from e

    def _is_valid_pickle(self, path: Path) -> bool:
        """
        Quick validation: try loading the pickle file and check structure.
        Returns True if it's a valid feedback table.
        """
        try:
            with open(path, 'rb') as f:
                table = pickle.load(f)
            
            # Check if it's a list of lists with correct dimensions
            if not isinstance(table, list) or len(table) != self.n:
                if self.verbose:
                    print(f"[FeedbackTable] Cache row count mismatch: found {len(table) if isinstance(table, list) else '?'}, expected {self.n}")
                return False
            
            if not all(isinstance(row, list) and len(row) == self.n for row in table):
                if self.verbose:
                    print(f"[FeedbackTable] Cache column count or structure mismatch")
                return False
            
            # Quick check that values are reasonable (0-242 for base-3 encoding of 5 marks)
            for row in table:
                for val in row:
                    if not isinstance(val, int) or val < 0 or val > 242:
                        if self.verbose:
                            print(f"[FeedbackTable] Cache contains invalid feedback value: {val}")
                        return False
            
            return True
        except Exception as e:
            if self.verbose:
                print(f"[FeedbackTable] Cache invalid/unreadable: {e}")
            return False

    def get_feedback(self, guess: str, target: str):
        """Return list[Mark] for strings (same API as before)."""
        gi = self.word_to_idx[guess.lower()]
        ti = self.word_to_idx[target.lower()]
        encoded = self.table[gi][ti]
        return decode_feedback(encoded)

    def get_feedback_idx(self, gi: int, ti: int):
        """Return list[Mark] using integer indices (faster)."""
        encoded = self.table[gi][ti]
        return decode_feedback(encoded)