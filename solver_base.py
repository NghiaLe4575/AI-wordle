import math
from collections import Counter

class WordleSearch:
    def __init__(self, engine, strategy="BFS"):
        self.engine = engine
        self.strategy = strategy
        self.candidates = list(engine.word_list) # State: List of valid words
        self.guesses_made = []
        
        # PRE-CALCULATION FOR UCS/A* (Internal Frequency)
        # We calculate the probability of every letter based on the dictionary itself.
        #for example: if the letter e and n are the most used word in the english vocabulaty, so the they have the highest frequency.
                
        self.letter_counts = Counter()
        for word in self.candidates:
            self.letter_counts.update(set(word)) # Use set to count presence, not frequency ('queer' only have one 'e')
        self.total_words = len(self.candidates)

    def solve(self):
        print(f"\n--- Starting Solver: {self.strategy} ---")
        
        while not self.engine.game_over:
            # 1. SEARCH STEP: Select the best action (word) based on strategy
            guess = self._select_next_node()
            
            if not guess:
                print("Error: Search Space Exhausted.")
                break
            
            # 2. EXECUTE ACTION
            print(f"Guessing: {guess} | Candidates: {len(self.candidates)}")
            feedback = self.engine.process_guess(guess)
            self.guesses_made.append(guess)
            
            if self.engine.is_win:
                print(f"Goal Reached! Path Cost: {len(self.guesses_made)}")
                return self.guesses_made

            # 3. TRANSITION (Sub-CSP): Update State Space
            self._prune_state_space(guess, feedback)

    def _select_next_node(self):
        """
        Determines which node to expand next based on the search strategy.
        """
        if not self.candidates: return None
        
        # --- BLIND SEARCH STRATEGIES ---
        
        # 2.2 BFS:
        if self.strategy == "BFS":
            return self.candidates[0]

        # 2.3 DFS:
        elif self.strategy == "DFS":
            return self.candidates[-1]

        # --- HEURISTIC SEARCH STRATEGIES ---

        # 2.4 UCS:
        # Cost = 1 (step) + Rarity Penalty.
        elif self.strategy == "UCS":
            return min(self.candidates, key=lambda w: self._calculate_cost(w))

        # 2.5 A*:
        # Logic: Balance Safety (Cost) with Information Gain (Heuristic).
        elif self.strategy == "A*":
            return min(self.candidates, key=lambda w: self._calculate_astar_score(w))
            
        return self.candidates[0]

    def _calculate_cost(self, word):
        
        #Calculates g(n): The cost of the node. Cost here is 'Risk'.
        #A word composed of very common letters (e.g., E, A, R) has LOW risk.
        #A word with rare letters (e.g., X, Q, Z) has HIGH risk.
        
        prob_sum = 0
        for char in set(word):
            prob_sum += self.letter_counts.get(char, 0) / self.total_words
        return 1 + (5.0 - prob_sum)

    def _calculate_astar_score(self, word):
        """
        Calculates f(n) = g(n) + h(n)
        """
        g = self._calculate_cost(word) # The Risk
        
        # h(n): Heuristic
        # We estimate distance to goal based on State Space Entropy.
        # Ideally, we want a word that splits the space.
        # Since we can't simulate splits easily in A*, we use a proxy:
        # We assume the "Distance" is proportional to the log of candidates remaining.
        # (This is constant for all words in the current step, effectively making A* # behave like UCS with a Tie-Breaker)
        
        h = self._heuristic_dynamic_entropy(word)
        
        return g + h

    def _heuristic_dynamic_entropy(self, word):
        # Calculate how well this word represents the CURRENT remaining candidates.
        # Lower score = Better representative (Closer to the 'center' of the cluster)
        subset_counts = Counter("".join(self.candidates))
        total_chars = len(self.candidates) * 5
        
        score = 0
        for char in set(word):
            # If char is common in candidates, heuristic cost is low.
            freq = subset_counts[char] / total_chars
            score += (1 - freq)
            
        return score

    def _prune_state_space(self, guess, feedback):
        # Implementation of the Transition Function (Filtering)
        new_candidates = []
        for word in self.candidates:
             if self._is_consistent(word, guess, feedback):
                 new_candidates.append(word)
        self.candidates = new_candidates
        
        #dynamic UCS
        # self.total_words = len(self.candidates)

    def _is_consistent(self, word, guess, feedback):
        # (Insert your standard checking logic here)
        # Placeholder for brevity
        return True