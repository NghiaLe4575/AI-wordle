# solver/cost_functions.py
from __future__ import annotations
import math

def cost_constant(before_count: int, after_count: int, word_length: int = 5) -> float:
    return 1.0

def cost_candidate_reduction(before_count: int, after_count: int, word_length: int = 5) -> float:
    if before_count == 0:
        return 1.0
    return 1.0 + (after_count / before_count)

def cost_partition_balance(before_count: int, after_count: int, word_length: int = 5, largest_partition: int = 0) -> float:
    if before_count == 0:
        return 1.0
    effective = largest_partition if largest_partition > 0 else after_count
    return 1.0 + (effective / before_count)

def cost_entropy_inverse(before_count: int, after_count: int, word_length: int = 5, entropy: float = 0.0, max_entropy: float = 1.0) -> float:
    if max_entropy == 0:
        return 1.0
    return 2.0 - (entropy / max_entropy)

COST_FUNCTIONS = {
    "constant": cost_constant,
    "reduction": cost_candidate_reduction,
    "partition": cost_partition_balance,
    "entropy": cost_entropy_inverse,
}
