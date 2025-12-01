# solver/heuristic_functions.py
from __future__ import annotations
import math
from typing import Dict, Tuple

def heuristic_log2(remaining: int, word_length: int = 5, largest_partition: int = 0) -> float:
    return math.log2(max(1, remaining))


def heuristic_partition(remaining: int, word_length: int = 5, largest_partition: int = 0) -> float:
    if largest_partition == 0:
        largest_partition = remaining
    return math.log2(max(1, largest_partition))


def heuristic_entropy(remaining: int, word_length: int = 5, largest_partition: int = 0,
                     entropy: float = 0.0, max_entropy: float = 1.0) -> float:
    if max_entropy == 0 or entropy == 0:
        return math.log2(max(1, remaining))
    
    # Weighted: high entropy → higher heuristic estimate
    return (entropy / max_entropy) * math.log2(max(1, remaining))


HEURISTIC_FUNCTIONS = {
    "log2": heuristic_log2,
    "partition": heuristic_partition,
    "entropy": heuristic_entropy,
}