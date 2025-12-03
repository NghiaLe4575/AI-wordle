# solver/solvers.py
from __future__ import annotations

import heapq
from collections import deque
from typing import Dict

from .search_base import GraphSearchAlgorithm
from .cost_functions import compute_entropy
import math


# --------------------------------------------------
# BFS implementation
# --------------------------------------------------
class BFS(GraphSearchAlgorithm):
    label = "bfs"

    def _create_frontier(self):
        return deque()

    def _push_frontier(self, frontier, state, history, possible, depth, seq):
        frontier.append((state, history, possible, depth))

    def _pop_frontier(self, frontier):
        return frontier.popleft()

    def _frontier_empty(self, frontier):
        return not frontier

    def _frontier_size(self, frontier):
        return len(frontier)


# --------------------------------------------------
# DFS implementation
# --------------------------------------------------
class DFS(GraphSearchAlgorithm):
    label = "dfs"

    def _create_frontier(self):
        return []

    def _push_frontier(self, frontier, state, history, possible, depth, seq):
        frontier.append((state, history, possible, depth))

    def _pop_frontier(self, frontier):
        return frontier.pop()

    def _frontier_empty(self, frontier):
        return not frontier

    def _frontier_size(self, frontier):
        return len(frontier)


# --------------------------------------------------
# Uniform-Cost Search
# --------------------------------------------------
class UCS(GraphSearchAlgorithm):
    label = "ucs"

    def _create_frontier(self):
        return []

    def _push_frontier(self, frontier, state, history, possible, depth, seq):
        # Use (cost, seq) ordering for stability
        heapq.heappush(
            frontier, (depth, seq, state, history, possible, depth)
        )

    def _pop_frontier(self, frontier):
        _, _, state, history, possible, depth = heapq.heappop(frontier)
        return state, history, possible, depth

    def _frontier_empty(self, frontier):
        return not frontier

    def _frontier_size(self, frontier):
        return len(frontier)


# --------------------------------------------------
# A* Search
# --------------------------------------------------
class AStar(GraphSearchAlgorithm):
    label = "astar"

    def __init__(self, word_length=5, branch_limit=6, cost_fn="constant", heuristic_fn="log2"):
        super().__init__(word_length, branch_limit, cost_fn, heuristic_fn)

    def _create_frontier(self):
        return []

    def _push_frontier(self, frontier, state, history, possible, depth, seq):
        # Heuristic calculation requires a representative guess index
        full_list = GraphSearchAlgorithm._global_wordlist
        fbt = GraphSearchAlgorithm._cached_table

        if possible:
            sample_idx = next(iter(possible))
            entropy_val, largest_block, _ = compute_entropy(
                possible, sample_idx, full_list, fbt
            )
        else:
            largest_block = 0

        heuristic = self.heuristic_f(
            len(possible),
            self.word_length,
            largest_partition=largest_block,
        )

        priority = depth + heuristic

        heapq.heappush(
            frontier,
            (priority, seq, state, history, possible, depth)
        )

    def _pop_frontier(self, frontier):
        _, _, state, history, possible, depth = heapq.heappop(frontier)
        return state, history, possible, depth

    def _frontier_empty(self, frontier):
        return not frontier

    def _frontier_size(self, frontier):
        return len(frontier)


# --------------------------------------------------
# Registry builder
# --------------------------------------------------
def _build_registry(branch_limit=2) -> Dict[str, GraphSearchAlgorithm]:
    reg: Dict[str, GraphSearchAlgorithm] = {}

    reg["bfs"] = BFS(branch_limit=branch_limit)
    reg["dfs"] = DFS(branch_limit=branch_limit)

    # UCS variants
    for cost_mode in ["constant", "reduction", "partition", "entropy"]:
        solver = UCS(branch_limit=branch_limit, cost_fn=cost_mode)
        solver.label = f"ucs-{cost_mode}"
        reg[solver.label] = solver

    # A* variants
    for cost_mode in ["constant", "reduction", "partition", "entropy"]:
        for heur in ["log2", "partition", "entropy"]:
            solver = AStar(
                branch_limit=branch_limit,
                cost_fn=cost_mode,
                heuristic_fn=heur,
            )
            solver.label = f"astar-{cost_mode}-{heur}"
            reg[solver.label] = solver

    return reg


GRAPH_SOLVERS = _build_registry()
