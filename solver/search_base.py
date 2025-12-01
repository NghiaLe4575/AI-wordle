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
        """
        Solve Wordle WITHOUT peeking at the answer during search.
        
        The solver explores hypothetical feedback patterns and only receives
        real feedback when a guess is committed (simulated here by checking
        against answer AFTER the guess is chosen, not during expansion).
        """
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
        answer_lower = answer.lower()

        self.starting_candidates_indices = {
            word_to_idx[w.lower()] for w in starting_candidates if w.lower() in word_to_idx
        }

        # Metrics
        expanded_nodes = 0
        generated_nodes = 0
        inference_ops = 0
        explored_words: list[str] = []
        expanded_order = []

        # Current game state: list of (guess, feedback) after each committed guess
        committed_history: list[tuple[str, Feedback]] = []
        # Candidates still possible given committed history
        possible_indices: set[int] = set(range(len(word_list)))

        for attempt in range(max_attempts):
            # === SELECTION PHASE: Pick the best guess using search (no peeking) ===
            best_guess_idx, search_inferences = self._select_best_guess(
                possible_indices, 
                word_list, 
                feedback_table, 
                attempt
            )
            inference_ops += search_inferences
            expanded_nodes += 1
            
            if best_guess_idx is None:
                # No valid guess found
                break
                
            guess = word_list[best_guess_idx]
            if guess not in explored_words:
                explored_words.append(guess)
            
            generated_nodes += 1

            # === COMMIT PHASE: Now we "play" the guess and get real feedback ===
            real_feedback = feedback_table.get_feedback(guess, answer)
            inference_ops += 1
            
            committed_history.append((guess, real_feedback))
            expanded_order.append(CompactState.from_history(tuple(committed_history), len(possible_indices)))

            # Check if solved
            if guess.lower() == answer_lower:
                return SolverResult(
                    True, tuple(committed_history), inference_ops, 
                    generated_nodes, len(possible_indices),
                    explored_words, [g for g, _ in committed_history], 
                    list(self.starting_candidates_indices), expanded_order
                )

            # === UPDATE PHASE: Filter candidates based on real feedback ===
            new_possible: set[int] = set()
            for idx in possible_indices:
                target = word_list[idx]
                hypo_fb = feedback_table.get_feedback(guess, target)
                inference_ops += 1
                if hypo_fb == real_feedback:
                    new_possible.add(idx)
            
            possible_indices = new_possible
            
            if not possible_indices:
                # No candidates left (shouldn't happen if answer is in word_pool)
                break

        # Failed to solve
        return SolverResult(
            False, tuple(committed_history), inference_ops, 
            generated_nodes, len(possible_indices),
            explored_words, [g for g, _ in committed_history], 
            list(self.starting_candidates_indices), expanded_order
        )

    def _select_best_guess(
        self, 
        possible_indices: set[int], 
        word_list: list[str], 
        feedback_table: FeedbackTable,
        attempt: int
    ) -> tuple[Optional[int], int]:
        """
        Select the best guess from possible candidates WITHOUT knowing the answer.
        Returns (best_guess_idx, number_of_inference_operations).
        
        Strategy: Pick guess that minimizes worst-case or expected remaining candidates.
        """
        inference_count = 0
        
        if not possible_indices:
            return None, inference_count
            
        # On first attempt, prefer starting candidates
        if attempt == 0 and self.starting_candidates_indices:
            available_starters = list(self.starting_candidates_indices & possible_indices)
            if available_starters:
                return available_starters[0], inference_count
        
        # Convert to list for indexing
        candidates = list(possible_indices)
        if attempt != 0: random.shuffle(candidates)

        # If only one candidate left, guess it
        if len(candidates) == 1:
            return candidates[0], inference_count
        
        # Limit candidates to evaluate (for performance)
        candidates_to_eval = candidates[:self.max_branching]
        
        # === Heuristic selection: minimize expected partition size ===
        best_guess = candidates_to_eval[0]
        best_score = float('inf')
        
        for guess_idx in candidates_to_eval:
            guess = word_list[guess_idx]
            
            # Group candidates by the feedback they would produce
            partition_sizes: dict[tuple, int] = {}
            for target_idx in possible_indices:
                target = word_list[target_idx]
                fb = feedback_table.get_feedback(guess, target)
                inference_count += 1
                fb_key = tuple(fb)
                partition_sizes[fb_key] = partition_sizes.get(fb_key, 0) + 1
            
            # Score: worst-case (max partition) or expected (avg partition)
            if self.cost_fn_name in ["entropy", "partition"]:
                # Use expected partition size (sum of squares / total)
                score = sum(s * s for s in partition_sizes.values()) / len(possible_indices)
            else:
                # Use worst-case partition size
                score = max(partition_sizes.values())
            
            if score < best_score:
                best_score = score
                best_guess = guess_idx
        
        return best_guess, inference_count

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
