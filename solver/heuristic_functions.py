# solver/heuristic_functions.py
from __future__ import annotations
import math

def heuristic_log2(remaining: int, word_length: int = 5) -> float:
    return math.log2(max(1, remaining))

def heuristic_partition(remaining: int, word_length: int = 5, largest_partition: int = 0) -> float:
    effective = largest_partition if largest_partition > 0 else remaining
    return math.log2(max(1, effective))

HEURISTIC_FUNCTIONS = {
    "log2": heuristic_log2,
    "partition": heuristic_partition,
}
