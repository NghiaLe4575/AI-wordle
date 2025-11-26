import math
import time
import tracemalloc
import random
from collections import Counter

class WordleSolver:
    def __init__(self, engine, strategy="UCS"):
        self.engine = engine
        self.strategy = strategy
        self.full_dictionary = engine.word_list  # Non-Shrinking Space
        self.guesses_made = []
        
        # Metrics
        self.nodes_expanded = 0
        self.execution_time = 0
        self.peak_memory = 0
        
        # Current Constraints (The "State")
        self.constraints = {
            "correct": {},    # {index: char}
            "present": set(), # {(char, bad_index)}
            "absent": set()   # {char}
        }
        
        # Pre-calc Static Costs (Rank/Rarity)
        self.static_costs = self._build_static_costs()

    def solve(self, ui_callback=None):
        print(f"--- Solving with {self.strategy} ---")
        self.guesses_made = []
        self.constraints = {"correct": {}, "present": set(), "absent": set()}
        
        # START MEASUREMENT
        start_time = time.perf_counter()
        tracemalloc.start()
        
        while not self.engine.game_over:
            
            # THE CORE SEARCH STEP
            best_word = self._search_entire_space()
            
            if not best_word:
                print("Error: No valid finite-cost words found.")
                break
                
            # Execute
            print(f"Guessing: {best_word}")
            feedback = self.engine.process_guess(best_word)
            self.guesses_made.append(best_word)
            
            # Update UI
            if ui_callback:
                ui_callback(best_word, feedback)

            if self.engine.is_win:
                print(f"WIN! Path: {self.guesses_made}")
                break

            # Update Constraints (State Transition)
            self._update_constraints(best_word, feedback)

        # STOP MEASUREMENT
        end_time = time.perf_counter()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        self.execution_time = end_time - start_time
        self.peak_memory = peak / 1024

        return {
            "strategy": self.strategy,
            "steps": len(self.guesses_made),
            "time": self.execution_time,
            "memory_kb": self.peak_memory,
            "nodes_visited": self.nodes_expanded, # Tracks valid candidates found
            "won": self.engine.is_win
        }

    def _search_entire_space(self):
        """
        Selects the next word based on strategy.
        """
        
        # --- DUMB SOLVERS (BFS/DFS) ---
        # They ignore constraints (infinite weights). 
        # They only care that they don't repeat the same word.
        if self.strategy in ["BFS", "DFS"]:
            # Pure Brute Force: Just get words we haven't tried yet
            candidates = [w for w in self.full_dictionary if w not in self.guesses_made]
            
            self.nodes_expanded += len(candidates)
            if not candidates: return None
            
            if self.strategy == "BFS":
                return candidates[0] # Linear Search from A-Z
            elif self.strategy == "DFS":
                return candidates[-1] # Linear Search from Z-A
        
        
        # --- SMART SOLVERS (UCS/A*) ---
        # They respect constraints (Infinite Weights).
        else:
            valid_candidates = []
            for word in self.full_dictionary:
                # We filter out "Infinite Cost" nodes immediately
                if self._get_constraint_cost(word) < float('inf'):
                    valid_candidates.append(word)
            
            self.nodes_expanded += len(valid_candidates)
            if not valid_candidates: return None

            if self.strategy == "UCS":
                return random.choice(valid_candidates)

            # A*: Minimal f(n) = g(n) + h(n)
            elif self.strategy == "A*":
                # Optimization: Vectorized heuristic calculation
                subset_counts = Counter()
                for w in valid_candidates:
                    subset_counts.update(set(w))
                total_docs = len(valid_candidates)

                def heuristic(w):
                    score = sum(subset_counts[c] for c in set(w))
                    normalized_score = score / total_docs if total_docs > 0 else 0
                    return 5.0 - normalized_score

                return min(valid_candidates, key=lambda w: self.static_costs[w] + heuristic(w))


    def _get_constraint_cost(self, word):
        """ Returns 0 if valid, Infinity if invalid. """
        # 1. Check Correct (Green)
        for i, char in self.constraints["correct"].items():
            if word[i] != char: return float('inf')
            
        # 2. Check Absent (Gray)
        for char in self.constraints["absent"]:
            if char in word: return float('inf')
            
        # 3. Check Present (Yellow)
        for char, bad_idx in self.constraints["present"]:
            if char not in word: return float('inf') # Must exist
            if word[bad_idx] == char: return float('inf') # Wrong spot
            
        return 0 

    def _build_static_costs(self):
        """ Builds the 'Rarity' cost map. """
        counts = Counter("".join(self.full_dictionary))
        total_chars = sum(counts.values())
        cost_map = {}
        
        for word in self.full_dictionary:
            prob = sum(counts[c]/total_chars for c in set(word))
            cost_map[word] = 1 + (1 - prob) # Low Prob = High Cost
            
        return cost_map

    def _update_constraints(self, guess, feedback):
        for i, (char, status) in enumerate(zip(guess, feedback)):
            if status == "CORRECT":
                self.constraints["correct"][i] = char
                # If we previously marked it absent (due to duplicate logic), unmark it
                self.constraints["absent"].discard(char)
            
            elif status == "PRESENT":
                self.constraints["present"].add((char, i))
                self.constraints["absent"].discard(char)
            
            elif status == "ABSENT":
                # CRITICAL: Only ban the letter if it is NOT marked correct/present elsewhere.
                # Example: Guess "EERIE", Secret "SPEED".
                # 1st E: Present, 2nd E: Correct, 3rd E: Absent.
                # We must NOT ban 'E' entirely, just know there are no *more* Es.
                is_safe = (char in self.constraints["correct"].values() or 
                           any(c == char for c, _ in self.constraints["present"]))
                
                if not is_safe:
                    self.constraints["absent"].add(char)

# --- BENCHMARK UTILITY ---
def run_benchmark(engine_class, strategy="UCS", runs=50):
    print(f"\n--- Running Benchmark: {strategy} ({runs} games) ---")
    wins = 0
    total_guesses = 0
    total_time = 0
    
    # Silent Engine
    game = engine_class() 
    solver = WordleSolver(game, strategy)
    
    for i in range(runs):
        game.start_game()
        stats = solver.solve(ui_callback=None) # Disable UI updates
        
        if stats["won"]:
            wins += 1
            total_guesses += stats["steps"]
        
        total_time += stats["time"]
        
    avg_guesses = total_guesses / runs
    avg_time = total_time / runs
    win_rate = (wins / runs) * 100
    
    print("\n" + "="*35)
    print(f"BENCHMARK RESULTS ({strategy})")
    print("="*35)
    print(f"Games Played   : {runs}")
    print(f"Win Rate       : {win_rate:.1f}%")
    print(f"AVG GUESSES    : {avg_guesses:.2f}") # <--- Prioritized Metric
    print(f"Avg Time       : {avg_time:.4f}s")
    print("="*35 + "\n")