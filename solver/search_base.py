# solver/search_base.py
from __future__ import annotations
import heapq
import random
from collections import deque
from typing import Callable, List, Optional, Sequence, Set, Tuple

from .state import CompactState
from .feedback_table import FeedbackTable
from .feedback import Feedback
from .cost_functions import COST_FUNCTIONS
from .heuristic_functions import HEURISTIC_FUNCTIONS

class SolverResult:
    def __init__(
        self,
        success: bool,
        history: Tuple[Tuple[str, Feedback], ...],
        expanded_nodes: int,
        generated_nodes: int,
        frontier_max: int,
        explored_words=None,
        final_path=None,
        starting_candidates=None,
        expanded_order=None      ### PATCH ADDED ###
    ):
        self.success = success
        self.history = history
        self.expanded_nodes = expanded_nodes
        self.generated_nodes = generated_nodes
        self.frontier_max = frontier_max
        self.explored_words = explored_words or []
        self.final_path = final_path or [g for g,_ in history]
        self.starting_candidates = starting_candidates or []
        self.expanded_order = expanded_order or []   ### PATCH ADDED ###

    def to_lines(self) -> list[str]:
        lines = []
        lines.append(f"Solved: {'yes' if self.success else 'no'}")
        lines.append(f"Guesses: {len(self.history)}")
        lines.append(f"Nodes expanded: {self.expanded_nodes}")
        lines.append(f"Nodes generated: {self.generated_nodes}")
        lines.append(f"Max frontier size: {self.frontier_max}")
        if self.final_path:
            lines.append(f"Final path: {' -> '.join(self.final_path).upper()}")
        for guess, fb in self.history:
            sym = ''.join(m.to_symbol() for m in fb)
            lines.append(f"  {guess.upper()} -> {sym}")
        return lines


class OptimizedGraphSearchSolver:
    _shared_feedback_table: FeedbackTable | None = None
    _shared_word_list: list[str] = []

    def __init__(self, word_length: int = 5, max_branching: int = 30, cost_fn: str = "constant", heuristic_fn: str = "log2"):
        self.word_length = word_length
        self.max_branching = max_branching
        self.cost_fn_name = cost_fn
        self.cost_fn = COST_FUNCTIONS.get(cost_fn, COST_FUNCTIONS["constant"])
        self.heuristic_fn_name = heuristic_fn
        self.heuristic_fn = HEURISTIC_FUNCTIONS.get(heuristic_fn, HEURISTIC_FUNCTIONS["log2"])
        self.starting_candidates_indices: set[int] = set()

    def solve(
        self,
        answer: str,
        word_pool: Sequence[str],
        max_attempts: int = 6,
        starting_candidates: Optional[Sequence[str]] = None
    ) -> SolverResult:

        if starting_candidates is None:
            starting_candidates = random.sample(list(word_pool), min(30, len(word_pool)))

        # prepare shared feedback table (cached file)
        if OptimizedGraphSearchSolver._shared_feedback_table is None or OptimizedGraphSearchSolver._shared_word_list != list(word_pool):
            OptimizedGraphSearchSolver._shared_word_list = list(word_pool)
            OptimizedGraphSearchSolver._shared_feedback_table = FeedbackTable(
                OptimizedGraphSearchSolver._shared_word_list,
                max_connections=200
            )

        word_list = OptimizedGraphSearchSolver._shared_word_list
        feedback_table = OptimizedGraphSearchSolver._shared_feedback_table
        word_to_idx = {w.lower(): i for i, w in enumerate(word_list)}
        answer_idx = word_to_idx[answer.lower()]

        self.starting_candidates_indices = {
            word_to_idx[w.lower()] for w in starting_candidates if w.lower() in word_to_idx
        }

        root_state = CompactState.from_history(tuple(), len(word_list))

        frontier = self._create_frontier()
        seq = 0
        self._push_frontier(frontier, root_state, tuple(), set(range(len(word_list))), 0.0, seq)
        seq += 1

        visited: set[CompactState] = set()
        expanded_nodes = 0
        generated_nodes = 0
        frontier_max = 1
        explored_words: list[str] = []

        expanded_order = []        ### PATCH ADDED ###

        while not self._frontier_empty(frontier):
            state, history, possible_indices, depth = self._pop_frontier(frontier)

            if state in visited:
                continue
            visited.add(state)

            expanded_nodes += 1
            expanded_order.append(state)   ### PATCH ADDED ###

            # goal check
            if history and word_to_idx[history[-1][0].lower()] == answer_idx:
                final_path = [g for g,_ in history]
                return SolverResult(
                    True, history, expanded_nodes, generated_nodes, frontier_max,
                    explored_words, final_path, list(self.starting_candidates_indices),
                    expanded_order                        ### PATCH ADDED ###
                )

            if depth >= max_attempts:
                continue

            candidate_indices = self._select_guesses(possible_indices, depth)

            for guess_idx in candidate_indices:
                guess = word_list[guess_idx]
                if guess not in explored_words:
                    explored_words.append(guess)

                feedback = feedback_table.get_feedback(guess, answer)
                new_possible = self._filter_candidates_fast(possible_indices, guess_idx, feedback, word_list, feedback_table)
                if not new_possible:
                    continue

                new_history = history + ((guess, feedback),)
                new_state = CompactState.from_history(new_history, len(new_possible))
                step_cost = self._compute_step_cost(guess, len(possible_indices), len(new_possible))
                new_depth = depth + step_cost

                generated_nodes += 1
                self._push_frontier(frontier, new_state, new_history, new_possible, new_depth, seq)
                seq += 1

            frontier_max = max(frontier_max, self._frontier_size(frontier))

        return SolverResult(
            False, tuple(), expanded_nodes, generated_nodes, frontier_max,
            explored_words, [], list(self.starting_candidates_indices),
            expanded_order                        ### PATCH ADDED ###
        )


    def _select_guesses(self, possible_indices: set[int], depth: float) -> list[int]:
        if depth == 0:
            cand = list(self.starting_candidates_indices & possible_indices)
        else:
            cand = list(possible_indices)
        if len(cand) <= self.max_branching:
            return cand
        return cand[: self.max_branching]

    def _compute_step_cost(self, guess: str, before_count: int, after_count: int) -> float:
        return float(self.cost_fn(before_count, after_count, self.word_length))

    def _filter_candidates_fast(self, possible_indices: set[int], guess_idx: int, feedback: Feedback, word_list: list[str], feedback_table: FeedbackTable) -> set[int]:
        result: set[int] = set()
        guess = word_list[guess_idx]
        for idx in possible_indices:
            target = word_list[idx]
            if feedback_table.get_feedback(guess, target) == feedback:
                result.add(idx)
        return result

    # frontier hooks
    def _create_frontier(self):
        raise NotImplementedError

    def _push_frontier(self, frontier, state, history, possible, depth, sequence):
        raise NotImplementedError

    def _pop_frontier(self, frontier):
        raise NotImplementedError

    def _frontier_empty(self, frontier) -> bool:
        raise NotImplementedError

    def _frontier_size(self, frontier) -> int:
        raise NotImplementedError
