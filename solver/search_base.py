# solver/search_base.py
from __future__ import annotations

import heapq
import random
import math
from collections import deque
from typing import Callable, List, Optional, Sequence, Set, Tuple

from .search_state import SearchState
from .feedback_matrix import FeedbackMatrix
from .letter_feedback import Feedback
from .cost_functions import COST_FUNCTIONS, compute_entropy
from .heuristic_functions import HEURISTIC_FUNCTIONS


class SearchOutcome:
    """Result container for any graph-based Wordle solver."""
    def __init__(
        self,
        success: bool,
        history: Tuple[Tuple[str, Feedback], ...],
        expanded_nodes: int,
        generated_nodes: int,
        max_frontier: int,
        visited_words=None,
        guess_route=None,
        starting_nodes=None,
        expansion_trace=None,
    ):
        self.success = success
        self.history = history
        self.expanded_nodes = expanded_nodes
        self.generated_nodes = generated_nodes
        self.frontier_max = max_frontier
        self.visited_words = visited_words or []
        self.guess_route = guess_route or [w for w, _ in history]
        self.starting_nodes = starting_nodes or []
        self.expansion_trace = expansion_trace or []

    def to_lines(self) -> list[str]:
        out = [
            f"Solved: {'yes' if self.success else 'no'}",
            f"Guesses: {len(self.history)}",
            f"Nodes expanded: {self.expanded_nodes}",
            f"Nodes generated: {self.generated_nodes}",
            f"Max frontier size: {self.max_frontier}",
        ]
        if self.guess_route:
            out.append("Final path: " + " -> ".join(self.guess_route).upper())

        for guess, fb in self.history:
            fb_symbols = "".join(m.to_symbol() for m in fb)
            out.append(f"  {guess.upper()} -> {fb_symbols}")

        return out


class GraphSearchAlgorithm:
    """Generic search engine powering Wordle solvers."""
    _cached_table: FeedbackMatrix | None = None
    _global_wordlist: list[str] = []
    _global_len: int = 0

    def __init__(
        self,
        word_length: int = 5,
        branch_limit: int = 6,
        cost_fn: str = "constant",
        heuristic_fn: str = "log2",
    ):
        self.word_length = word_length
        self.branch_limit = branch_limit

        self.cost_fn_name = cost_fn
        self.cost_function = COST_FUNCTIONS.get(cost_fn, COST_FUNCTIONS["constant"])

        self.heuristic_fn_name = heuristic_fn
        self.heuristic_f = HEURISTIC_FUNCTIONS.get(heuristic_fn, HEURISTIC_FUNCTIONS["log2"])

        self.initial_guess_indices: set[int] = set()

    # --------------------------------------------------
    # Entry point
    # --------------------------------------------------

    def solve(
        self,
        answer: str,
        word_pool: Sequence[str],
        max_turns: int = 6,
        starting_words: Optional[Sequence[str]] = None,
        shared_table: FeedbackMatrix = None,
    ) -> SearchOutcome:

        # Ensure starting list exists
        if starting_words is None:
            starting_words = sorted(word_pool)[:10]

        # Handle cached global lookup table
        if (GraphSearchAlgorithm._cached_table is None or
                GraphSearchAlgorithm._global_len != len(word_pool)):

            GraphSearchAlgorithm._global_wordlist = list(word_pool)
            GraphSearchAlgorithm._global_len = len(word_pool)
            GraphSearchAlgorithm._cached_table = shared_table

        wordlist = GraphSearchAlgorithm._global_wordlist
        table = GraphSearchAlgorithm._cached_table

        lookup = {w.lower(): i for i, w in enumerate(wordlist)}
        answer_idx = lookup[answer.lower()]

        # Index-based starting guesses
        self.initial_guess_indices = {
            lookup[w.lower()]
            for w in starting_words
            if w.lower() in lookup
        }

        # Root state
        root_history = tuple()
        root = SearchState.create(root_history, len(wordlist))

        # Frontier setup
        frontier = self._create_frontier()
        order = 0
        self._push_frontier(frontier, root, root_history, set(range(len(wordlist))), 0.0, order)
        order += 1

        visited_states: set[SearchState] = set()
        visited_words: list[str] = []
        expanded_nodes = 0
        generated_nodes = 0
        max_frontier = 1
        expansion_log = []

        # --------------------------------------------------
        # Search loop
        # --------------------------------------------------
        while not self._frontier_empty(frontier):

            state, history, possible, depth = self._pop_frontier(frontier)

            if state in visited_states:
                continue
            visited_states.add(state)

            expanded_nodes += 1
            expansion_log.append(state)

            # Goal reached?
            if history and lookup[history[-1][0].lower()] == answer_idx:
                path = [w for w, _ in history]
                return SearchOutcome(
                    True,
                    history,
                    expanded_nodes,
                    generated_nodes,
                    max_frontier,
                    visited_words,
                    path,
                    list(self.initial_guess_indices),
                    expansion_log,
                )

            if depth >= max_turns:
                continue

            # Choose next guesses
            guess_indices = self._pick_guesses(possible, depth, wordlist, table)

            for g_idx in guess_indices:
                guess_w = wordlist[g_idx]

                if guess_w not in visited_words:
                    visited_words.append(guess_w)

                fb = table.get_feedback(guess_w, answer)
                narrowed = self._prune_candidates(possible, g_idx, fb, wordlist, table)

                if not narrowed:
                    continue

                new_hist = history + ((guess_w, fb),)
                next_state = SearchState.create(new_hist, len(narrowed))

                # cost-based depth progression
                step_cost = self._calc_step_cost(
                    g_idx, len(possible), len(narrowed),
                    possible, wordlist, table
                )
                new_depth = depth + step_cost

                generated_nodes += 1
                self._push_frontier(frontier, next_state, new_hist, narrowed, new_depth, order)
                order += 1

            max_frontier = max(max_frontier, self._frontier_size(frontier))

        # If frontier empty — failure
        return SearchOutcome(
            False,
            tuple(),
            expanded_nodes,
            generated_nodes,
            max_frontier,
            visited_words,
            [],
            list(self.initial_guess_indices),
            expansion_log,
        )

    # --------------------------------------------------
    # Helper methods
    # --------------------------------------------------

    def _pick_guesses(
        self,
        possible: set[int],
        depth: float,
        words: list[str],
        table: FeedbackMatrix,
    ) -> list[int]:

        if depth == 0:
            candidates = list(self.initial_guess_indices & possible)
        else:
            candidates = list(possible)
            random.shuffle(candidates)

        if len(candidates) <= self.branch_limit:
            return candidates
        return candidates[:self.branch_limit]

    def _calc_step_cost(
        self,
        g_idx: int,
        before: int,
        after: int,
        possible: set[int],
        words: list[str],
        table: FeedbackMatrix,
    ) -> float:

        entropy, largest, parts = compute_entropy(possible, g_idx, words, table)
        max_e = math.log2(max(1, before))

        return float(
            self.cost_function(
                before, after, self.word_length,
                entropy=entropy,
                max_entropy=max_e,
                largest_partition=largest,
            )
        )

    def _prune_candidates(
        self,
        possible: set[int],
        g_idx: int,
        fb: Feedback,
        words: list[str],
        table: FeedbackMatrix,
    ) -> set[int]:

        result: set[int] = set()
        for idx in possible:
            if table.get_feedback_idx(g_idx, idx) == fb:
                result.add(idx)
        return result

    # --------------------------------------------------
    # Frontier interface (implemented by subclasses)
    # --------------------------------------------------

    def _create_frontier(self):
        raise NotImplementedError

    def _push_frontier(self, frontier, state, history, possible, depth, seq):
        raise NotImplementedError

    def _pop_frontier(self, frontier):
        raise NotImplementedError

    def _frontier_empty(self, frontier) -> bool:
        raise NotImplementedError

    def _frontier_size(self, frontier) -> int:
        raise NotImplementedError
