# solver/cost_functions.py
from __future__ import annotations
import math
from typing import Dict, Tuple
from .feedback import Mark, Feedback

def compute_entropy(candidates_indices: set[int], guess_idx: int, word_list: list[str], 
                   feedback_table) -> Tuple[float, int, Dict]:

    partitions: Dict[Tuple[Mark, ...], int] = {}
    guess = word_list[guess_idx]
    
    # Partition candidates by feedback pattern
    for idx in candidates_indices:
        target = word_list[idx]
        feedback = feedback_table.get_feedback(guess, target)
        pattern = tuple(feedback)
        partitions[pattern] = partitions.get(pattern, 0) + 1
    
    # Calculate Shannon entropy
    entropy = 0.0
    total = len(candidates_indices)
    largest_partition = 0
    
    for count in partitions.values():
        if count > 0:
            largest_partition = max(largest_partition, count)
            p = count / total
            entropy -= p * math.log2(p)
    
    return entropy, largest_partition, partitions


def cost_constant(before_count: int, after_count: int, word_length: int = 5, 
                 entropy: float = 0.0, max_entropy: float = 1.0, largest_partition: int = 0) -> float:
    return 1.0


def cost_candidate_reduction(before_count: int, after_count: int, word_length: int = 5,
                            entropy: float = 0.0, max_entropy: float = 1.0, largest_partition: int = 0) -> float:
    if before_count == 0:
        return 1.0
    return 1.0 + (after_count / before_count)


def cost_partition_balance(before_count: int, after_count: int, word_length: int = 5,
                          entropy: float = 0.0, max_entropy: float = 1.0, largest_partition: int = 0) -> float:
    if before_count == 0:
        return 1.0
    if largest_partition == 0:
        largest_partition = after_count  # Fallback if not provided
    return 1.0 + (largest_partition / before_count)


def cost_entropy_inverse(before_count: int, after_count: int, word_length: int = 5,
                        entropy: float = 0.0, max_entropy: float = 1.0, largest_partition: int = 0) -> float:
    if max_entropy == 0 or entropy == 0:
        # Fallback: use candidate reduction if entropy not computed
        return 1.0 + (after_count / before_count) if before_count > 0 else 1.0
    
    normalized_entropy = entropy / max_entropy
    return 2.0 - normalized_entropy


COST_FUNCTIONS = {
    "constant": cost_constant,
    "reduction": cost_candidate_reduction,
    "partition": cost_partition_balance,
    "entropy": cost_entropy_inverse,
}