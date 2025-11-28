# solver/solvers.py
from __future__ import annotations
from collections import deque
import heapq
from .search_base import OptimizedGraphSearchSolver
from typing import Dict

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
    def _create_frontier(self): return []
    def _push_frontier(self, frontier, state, history, possible, depth, sequence):
        heuristic = self.heuristic_fn(len(possible), self.word_length)
        priority = depth + heuristic
        heapq.heappush(frontier, (priority, sequence, state, history, possible, depth))
    def _pop_frontier(self, frontier):
        _, _, state, history, possible, depth = heapq.heappop(frontier)
        return state, history, possible, depth
    def _frontier_empty(self, frontier): return not frontier
    def _frontier_size(self, frontier): return len(frontier)

# Build registry
def _build_registry() -> Dict[str, OptimizedGraphSearchSolver]:
    registry: Dict[str, OptimizedGraphSearchSolver] = {}
    registry["bfs-opt"] = OptimizedBFS(max_branching=30)
    registry["dfs-opt"] = OptimizedDFS(max_branching=30)
    # UCS variants
    for cost_name in ["constant", "reduction", "partition", "entropy"]:
        r = OptimizedUCS(max_branching=30, cost_fn=cost_name)
        r.name = f"ucs-{cost_name}"
        registry[r.name] = r
    # A* variants
    for cost_name in ["constant", "reduction", "partition", "entropy"]:
        for heuristic_name in ["log2", "partition"]:
            r = OptimizedAStar(max_branching=30, cost_fn=cost_name, heuristic_fn=heuristic_name)
            r.name = f"astar-{cost_name}-{heuristic_name}"
            registry[r.name] = r
    return registry

OPTIMIZED_SOLVERS = _build_registry()
