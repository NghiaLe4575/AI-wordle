import random
from collections import Counter

class WordleEngine:
    def __init__(self, word_file="words.txt"):
        self.word_list = self._load_words(word_file)
        self.secret_word = ""
        self.guesses = []  # History of guesses
        self.max_guesses = 6
        self.word_length = 5
        self.game_over = False
        self.is_win = False
        
        # Tracks status of alphabet: 'UNTESTED', 'ABSENT', 'PRESENT', 'CORRECT'
        self.letter_states = {chr(i): 'UNTESTED' for i in range(65, 91)}
        
        self.start_game()

    def _load_words(self, filepath):
        try:
            with open(filepath, 'r') as f:
                # Filter for 5 letter words and uppercase them
                return [w.strip().upper() for w in f.readlines() if len(w.strip()) == 5]
        except FileNotFoundError:
            print("Error: words.txt not found. Using fallback list.")
            return ["APPLE", "BEACH", "CRANE", "DRIVE", "EAGLE"]

    def start_game(self):
        self.guesses = []
        self.game_over = False
        self.is_win = False
        self.letter_states = {chr(i): 'UNTESTED' for i in range(65, 91)}
        if self.word_list:
            self.secret_word = random.choice(self.word_list)
        print(f"DEBUG: Secret word is {self.secret_word}") # Remove this line in production

    def is_valid_word(self, word):
        return len(word) == 5 and word in self.word_list

    def process_guess(self, guess):
        """
        Returns a list of status codes for each letter in the guess:
        ['CORRECT', 'PRESENT', 'ABSENT']
        """
        guess = guess.upper()
        if len(guess) != 5:
            return None
            
        self.guesses.append(guess)
        
        # Convert strings to lists for mutable operations
        guess_chars = list(guess)
        secret_chars = list(self.secret_word)
        result = ["ABSENT"] * 5
        
        # Track available letters in secret word to handle duplicates correctly
        secret_counts = Counter(secret_chars)

        # PASS 1: Find Greens (CORRECT)
        for i in range(5):
            if guess_chars[i] == secret_chars[i]:
                result[i] = "CORRECT"
                secret_counts[guess_chars[i]] -= 1
                self._update_letter_state(guess_chars[i], "CORRECT")

        # PASS 2: Find Yellows (PRESENT)
        for i in range(5):
            if result[i] == "ABSENT": # If not already marked green
                char = guess_chars[i]
                if secret_counts[char] > 0:
                    result[i] = "PRESENT"
                    secret_counts[char] -= 1
                    self._update_letter_state(char, "PRESENT")
                else:
                    self._update_letter_state(char, "ABSENT")

        # Check Game End
        if guess == self.secret_word:
            self.game_over = True
            self.is_win = True
        elif len(self.guesses) >= self.max_guesses:
            self.game_over = True
            
        return result

    def _update_letter_state(self, char, new_state):
        # Priority: CORRECT > PRESENT > ABSENT > UNTESTED
        # We don't want to downgrade a 'CORRECT' letter to 'PRESENT'
        current = self.letter_states[char]
        if current == "CORRECT":
            return
        if current == "PRESENT" and new_state == "ABSENT":
            return
        self.letter_states[char] = new_state