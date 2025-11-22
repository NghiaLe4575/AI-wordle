import tkinter as tk
from tkinter import messagebox

# Configuration
COLOR_CORRECT = "#6aaa64"   # Green
COLOR_PRESENT = "#c9b458"   # Yellow
COLOR_ABSENT = "#121213"    # Black
COLOR_UNTESTED = "#818384"  # Grey
COLOR_DEFAULT_BG = "#121213"
COLOR_TEXT = "#ffffff"
COLOR_BORDER = "#3a3a3c"
COLOR_BTN_BG = "#4c4c4e"    # Button Background

class WordleUI:
    def __init__(self, root, engine):
        self.root = root
        self.engine = engine
        
        self.root.title("Python Wordle")
        self.root.geometry("650x850") # Increased height for new controls
        self.root.configure(bg=COLOR_DEFAULT_BG)
        
        # Current input buffer
        self.current_guess_chars = [] 

        self._setup_layout()
        self._bind_events()

    def _setup_layout(self):
        # 1. Title
        lbl_title = tk.Label(self.root, text="WORDLE", font=("Helvetica", 36, "bold"), 
                             bg=COLOR_DEFAULT_BG, fg=COLOR_TEXT)
        lbl_title.pack(pady=(20, 5))

        # 2. Message Area (Replaces Popups)
        self.msg_label = tk.Label(self.root, text="Good Luck!", font=("Helvetica", 16), 
                                  bg=COLOR_DEFAULT_BG, fg=COLOR_PRESENT)
        self.msg_label.pack(pady=(0, 10))

        # 3. Game Grid Frame
        self.grid_frame = tk.Frame(self.root, bg=COLOR_DEFAULT_BG)
        self.grid_frame.pack(pady=5)

        self.cells = []
        for row in range(6):
            row_cells = []
            for col in range(5):
                frame = tk.Frame(self.grid_frame, width=60, height=60, bg=COLOR_BORDER)
                frame.grid(row=row, column=col, padx=3, pady=3)
                frame.pack_propagate(False)
                
                lbl = tk.Label(frame, text="", font=("Helvetica", 24, "bold"), 
                               bg=COLOR_DEFAULT_BG, fg=COLOR_TEXT)
                lbl.pack(expand=True, fill="both", padx=2, pady=2)
                
                row_cells.append({"frame": frame, "lbl": lbl})
            self.cells.append(row_cells)

        # 4. Manual Controls (Submit / Reset)
        controls_frame = tk.Frame(self.root, bg=COLOR_DEFAULT_BG)
        controls_frame.pack(pady=15)

        btn_config = {"font": ("Helvetica", 12, "bold"), "bg": COLOR_BTN_BG, "fg": COLOR_TEXT, "width": 10, "relief": "flat"}
        
        self.btn_submit = tk.Button(controls_frame, text="ENTER", command=self.submit_guess, **btn_config)
        self.btn_submit.pack(side="left", padx=5)

        self.btn_reset = tk.Button(controls_frame, text="RESET", command=self.reset_ui, **btn_config)
        self.btn_reset.pack(side="left", padx=5)

        # 5. Keyboard Frame
        self.kb_frame = tk.Frame(self.root, bg=COLOR_DEFAULT_BG)
        self.kb_frame.pack(pady=15, padx=10)
        
        self.key_buttons = {}
        keys_layout = [
            "QWERTYUIOP",
            "ASDFGHJKL",
            "ZXCVBNM"
        ]
        
        for row_keys in keys_layout:
            row_frame = tk.Frame(self.kb_frame, bg=COLOR_DEFAULT_BG)
            row_frame.pack()
            for char in row_keys:
                btn = tk.Label(row_frame, text=char, font=("Helvetica", 12, "bold"),
                               width=4, height=2, bg=COLOR_UNTESTED, fg=COLOR_TEXT,
                               relief="flat")
                btn.pack(side="left", padx=2, pady=2)
                self.key_buttons[char] = btn
                btn.bind("<Button-1>", lambda e, c=char: self._handle_virtual_click(c))

        # 6. AI Solver Menu
        # Using a LabelFrame to group the solver options
        solver_frame = tk.LabelFrame(self.root, text="AI Solvers", font=("Helvetica", 10),
                                     bg=COLOR_DEFAULT_BG, fg=COLOR_UNTESTED, padx=10, pady=10)
        solver_frame.pack(pady=10, fill="x", padx=50)

        solver_btn_config = {"font": ("Helvetica", 10), "bg": "#2c2c2e", "fg": COLOR_TEXT, "width": 8, "relief": "raised"}

        # Solver Buttons (Placeholders for now)
        tk.Button(solver_frame, text="BFS", command=lambda: self.run_solver("BFS"), **solver_btn_config).pack(side="left", padx=5, expand=True)
        tk.Button(solver_frame, text="DFS", command=lambda: self.run_solver("DFS"), **solver_btn_config).pack(side="left", padx=5, expand=True)
        tk.Button(solver_frame, text="UCS", command=lambda: self.run_solver("UCS"), **solver_btn_config).pack(side="left", padx=5, expand=True)
        tk.Button(solver_frame, text="A*", command=lambda: self.run_solver("A*"), **solver_btn_config).pack(side="left", padx=5, expand=True)

    def _bind_events(self):
        self.root.bind("<Key>", self._handle_keypress)

    def _handle_virtual_click(self, char):
        if self.engine.game_over: return
        if len(self.current_guess_chars) < 5:
            self.current_guess_chars.append(char)
            self._update_grid_preview()

    def _handle_keypress(self, event):
        if self.engine.game_over: 
            if event.keysym == 'Return':
                self.reset_ui()
            return

        key = event.keysym.upper()
        
        if len(key) == 1 and key.isalpha():
            if len(self.current_guess_chars) < 5:
                self.current_guess_chars.append(key)
        
        elif key == "BACKSPACE":
            if self.current_guess_chars:
                self.current_guess_chars.pop()
        
        elif key == "RETURN":
            if len(self.current_guess_chars) == 5:
                self.submit_guess()
            else:
                self.set_message("Not enough letters")

        self._update_grid_preview()

    def _update_grid_preview(self):
        row_idx = len(self.engine.guesses)
        if row_idx >= 6: return

        chars = self.current_guess_chars
        for col in range(5):
            text = chars[col] if col < len(chars) else ""
            self.cells[row_idx][col]["lbl"].config(text=text)
            
            border = "#888888" if text else COLOR_BORDER
            self.cells[row_idx][col]["frame"].config(bg=border)

    def submit_guess(self):
        if self.engine.game_over: return

        guess_str = "".join(self.current_guess_chars)
        
        if len(guess_str) != 5:
            self.set_message("Not enough letters")
            return
        
        if not self.engine.is_valid_word(guess_str):
            self.set_message("Not in word list")
            # Shake animation could go here
            return

        # Process Guess
        results = self.engine.process_guess(guess_str)
        
        # Update UI
        row_idx = len(self.engine.guesses) - 1
        for col, status in enumerate(results):
            color = COLOR_ABSENT
            if status == "CORRECT": color = COLOR_CORRECT
            elif status == "PRESENT": color = COLOR_PRESENT
            
            self.cells[row_idx][col]["lbl"].config(bg=color)
            self.cells[row_idx][col]["frame"].config(bg=color)
        
        self._update_keyboard()
        self.current_guess_chars = []
        self.set_message("") 

        if self.engine.game_over:
            if self.engine.is_win:
                self.set_message("Splendid! You Won!")
            else:
                self.set_message(f"Game Over. Word: {self.engine.secret_word}")

    def _update_keyboard(self):
        for char, state in self.engine.letter_states.items():
            if char in self.key_buttons:
                color = COLOR_UNTESTED
                if state == "CORRECT": color = COLOR_CORRECT
                elif state == "PRESENT": color = COLOR_PRESENT
                elif state == "ABSENT": color = COLOR_ABSENT 
                
                self.key_buttons[char].config(bg=color)

    def set_message(self, text):
        """Updates the on-screen message label."""
        self.msg_label.config(text=text)
        if text in ["Not in word list", "Not enough letters"]:
            self.root.after(1500, lambda: self.msg_label.config(text="") if self.msg_label.cget("text") == text else None)

    def reset_ui(self):
        self.engine.start_game()
        self.current_guess_chars = []
        self.set_message("New Game Started")
        
        for row in range(6):
            for col in range(5):
                self.cells[row][col]["lbl"].config(text="", bg=COLOR_DEFAULT_BG)
                self.cells[row][col]["frame"].config(bg=COLOR_BORDER)
        
        for btn in self.key_buttons.values():
            btn.config(bg=COLOR_UNTESTED)

    def run_solver(self, algorithm_name):
        """Placeholder for connecting the solvers later"""
        if self.engine.game_over:
            self.set_message("Reset game to use AI")
            return
            
        print(f"DEBUG: Starting {algorithm_name} Solver...")
        self.set_message(f"Running {algorithm_name} Solver...")
        # In the future, you will call: self.solver_module.solve(algorithm_name)