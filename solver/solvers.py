# solver/solvers.py
from __future__ import annotations
from collections import deque
import heapq
from .search_base import OptimizedGraphSearchSolver
from typing import Dict
from .cost_functions import compute_entropy
import math

class OptimizedBFS(OptimizedGraphSearchSolver):
    name = "bfs-opt"
    def _create_frontier(self): return deque()
    def _push_frontier(self, frontier, state, history, possible, depth, sequence):
        frontier.append((state, history, possible, depth))
    def _pop_frontier(self, frontier):
        return frontier.popleft()
    def _frontier_empty(self, frontier): return not frontier
    def _frontier_size(self, frontier): return len(frontier)

class OptimizedDFS(OptimizedGraphSearchSolver):
    name = "dfs-opt"
    def _create_frontier(self): return []
    def _push_frontier(self, frontier, state, history, possible, depth, sequence):
        frontier.append((state, history, possible, depth))
    def _pop_frontier(self, frontier): return frontier.pop()
    def _frontier_empty(self, frontier): return not frontier
    def _frontier_size(self, frontier): return len(frontier)

class OptimizedUCS(OptimizedGraphSearchSolver):
    name = "ucs-opt"
    def _create_frontier(self): return []
    def _push_frontier(self, frontier, state, history, possible, depth, sequence):
        heapq.heappush(frontier, (depth, sequence, state, history, possible, depth))
    def _pop_frontier(self, frontier):
        _, _, state, history, possible, depth = heapq.heappop(frontier)
        return state, history, possible, depth
    def _frontier_empty(self, frontier): return not frontier
    def _frontier_size(self, frontier): return len(frontier)


class OptimizedAStar(OptimizedGraphSearchSolver):
    name = "astar-opt"
    
    def __init__(self, word_length: int = 5, max_branching: int = 30, cost_fn: str = "constant", heuristic_fn: str = "log2"):
        super().__init__(word_length, max_branching, cost_fn, heuristic_fn)
    
    def _create_frontier(self):
        return []
    
    def _push_frontier(self, frontier, state, history, possible, depth, sequence):
        # Compute entropy info for heuristic evaluation
        # We need to pick a guess to evaluate; use the first candidate
        # For a* to work properly, we need to estimate remaining cost
        
        word_list = OptimizedGraphSearchSolver._shared_word_list
        feedback_table = OptimizedGraphSearchSolver._shared_feedback_table
        
        # Pick a representative guess (e.g., first in possible set)
        # This is a heuristic estimate of the partition quality
        if possible:
            guess_idx = next(iter(possible))
            entropy, largest_partition, _ = compute_entropy(possible, guess_idx, word_list, feedback_table)
            #max_entropy = math.log2(max(1, len(possible)))
        else:
            entropy = 0.0
            largest_partition = 0
            #max_entropy = 0.0
        
        # Call heuristic with all required parameters
        heuristic = self.heuristic_fn(
            len(possible), 
            self.word_length,
            largest_partition=largest_partition,
        )
        
        priority = depth + heuristic
        heapq.heappush(frontier, (priority, sequence, state, history, possible, depth))
    
    def _pop_frontier(self, frontier):
        _, _, state, history, possible, depth = heapq.heappop(frontier)
        return state, history, possible, depth
    
    def _frontier_empty(self, frontier):
        return not frontier
    
    def _frontier_size(self, frontier):
        return len(frontier)

# Build registry
def _build_registry(max_branching_no = 6) -> Dict[str, OptimizedGraphSearchSolver]:
    registry: Dict[str, OptimizedGraphSearchSolver] = {}
    registry["bfs-opt"] = OptimizedBFS(max_branching=max_branching_no)
    registry["dfs-opt"] = OptimizedDFS(max_branching=max_branching_no)
    # UCS variants
    for cost_name in ["constant", "reduction", "partition", "entropy"]:
        r = OptimizedUCS(max_branching=max_branching_no, cost_fn=cost_name)
        r.name = f"ucs-{cost_name}"
        registry[r.name] = r
    # A* variants
    for cost_name in ["constant", "reduction", "partition", "entropy"]:
        for heuristic_name in ["log2", "partition","entropy"]:
            r = OptimizedAStar(max_branching=max_branching_no, cost_fn=cost_name, heuristic_fn=heuristic_name)
            r.name = f"astar-{cost_name}-{heuristic_name}"
            registry[r.name] = r
    return registry

OPTIMIZED_SOLVERS = _build_registry()