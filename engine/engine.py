# engine/engine.py
import random
from collections import Counter

class WordleEngine:
    """
    Wordle Game Engine
    
    Handles:
    - Word validation
    - Feedback generation (CORRECT, PRESENT, ABSENT)
    - Game state tracking
    - Letter state management
    """
    
    def __init__(self, word_file="data/words.txt"):
        self.word_list = self._load_words(word_file)
        self.secret_word = ""
        self.guesses = []  # History of guesses made
        self.max_guesses = 6
        self.word_length = 5
        self.game_over = False
        self.is_win = False
        
        # Tracks status of alphabet: 'UNTESTED', 'ABSENT', 'PRESENT', 'CORRECT'
        self.letter_states = {chr(i): 'UNTESTED' for i in range(65, 91)}
        
        self.start_game()

    def _load_words(self, filepath):
        """Load 5-letter words from file"""
        try:
            with open(filepath, 'r') as f:
                words = [w.strip().upper() for w in f.readlines() if len(w.strip()) == 5]
                print(f"✓ Loaded {len(words)} words from {filepath}")
                return words
        except FileNotFoundError:
            print(f"⚠ Error: {filepath} not found. Using fallback list.")
            return ["APPLE", "BEACH", "CRANE", "DRIVE", "EAGLE", "FLAME", "GRAPE",
                    "HOUSE", "IMAGE", "JELLY", "KNIFE", "LEMON", "MOUSE", "NOBLE",
                    "OCEAN", "PEARL", "QUEEN", "RIVER", "SNAKE", "TABLE", "ULTRA",
                    "VAULT", "WHALE", "XENON", "YIELD", "ZEBRA"]

    def start_game(self):
        """Initialize a new game"""
        self.guesses = []
        self.game_over = False
        self.is_win = False
        self.letter_states = {chr(i): 'UNTESTED' for i in range(65, 91)}
        if self.word_list:
            self.secret_word = random.choice(self.word_list)
        print(f"🎮 New game started. Secret word: {self.secret_word}")

    def is_valid_word(self, word):
        """Check if word is in the word list and correct length"""
        return len(word) == 5 and word.upper() in self.word_list

    def process_guess(self, guess):
        """
        Process a guess and return feedback
        
        Args:
            guess (str): 5-letter guess
            
        Returns:
            list: Feedback for each position ['CORRECT', 'PRESENT', 'ABSENT']
            
        Example:
            >>> engine.process_guess('SLATE')
            ['ABSENT', 'ABSENT', 'ABSENT', 'PRESENT', 'ABSENT']
        """
        guess = guess.upper()
        
        if len(guess) != 5:
            return None
        
        if guess not in self.word_list:
            return None
            
        self.guesses.append(guess)
        
        # Convert to lists for mutable operations
        guess_chars = list(guess)
        secret_chars = list(self.secret_word)
        result = ["ABSENT"] * 5
        
        # Track available letters in secret word to handle duplicates correctly
        secret_counts = Counter(secret_chars)

        # PASS 1: Find Greens (CORRECT positions)
        # Must be done first to avoid double-counting letters
        for i in range(5):
            if guess_chars[i] == secret_chars[i]:
                result[i] = "CORRECT"
                secret_counts[guess_chars[i]] -= 1
                self._update_letter_state(guess_chars[i], "CORRECT")

        # PASS 2: Find Yellows (PRESENT but wrong position)
        # Only check letters not already marked as correct
        for i in range(5):
            if result[i] == "ABSENT":  # Not already marked correct
                char = guess_chars[i]
                if secret_counts[char] > 0:
                    # Letter exists in secret word and count is available
                    result[i] = "PRESENT"
                    secret_counts[char] -= 1
                    self._update_letter_state(char, "PRESENT")
                else:
                    # Letter not in secret word or already used up
                    self._update_letter_state(char, "ABSENT")

        # Check game end conditions
        if guess == self.secret_word:
            self.game_over = True
            self.is_win = True
            print(f"🎉 Solved in {len(self.guesses)} guesses!")
        elif len(self.guesses) >= self.max_guesses:
            self.game_over = True
            self.is_win = False
            print(f"💀 Game Over. The word was: {self.secret_word}")
            
        return result

    def _update_letter_state(self, char, new_state):
        """
        Update letter state with priority:
        CORRECT > PRESENT > ABSENT > UNTESTED
        
        Never downgrade a letter's state (e.g., CORRECT -> PRESENT)
        """
        current = self.letter_states[char]
        
        # Priority levels
        priority = {
            'UNTESTED': 0,
            'ABSENT': 1,
            'PRESENT': 2,
            'CORRECT': 3
        }
        
        if priority[new_state] > priority[current]:
            self.letter_states[char] = new_state

    def get_game_state(self):
        """
        Get current game state as dictionary
        
        Returns:
            dict: Current game state
        """
        return {
            'secret_word': self.secret_word,
            'guesses': self.guesses,
            'game_over': self.game_over,
            'is_win': self.is_win,
            'attempts_left': self.max_guesses - len(self.guesses),
            'letter_states': self.letter_states.copy()
        }

    def reset_game(self):
        """Reset to start a new game"""
        self.start_game()

    def __repr__(self):
        return (f"WordleEngine(word_list_size={len(self.word_list)}, "
                f"guesses={len(self.guesses)}, secret={self.secret_word}, "
                f"game_over={self.game_over})")