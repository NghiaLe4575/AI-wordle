import tkinter as tk
from tkinter import messagebox
import threading
from solver.solvers import OPTIMIZED_SOLVERS

# Configuration
COLOR_CORRECT = "#6aaa64"
COLOR_PRESENT = "#c9b458"
COLOR_ABSENT = "#121213"
COLOR_UNTESTED = "#818384"
COLOR_DEFAULT_BG = "#121213"
COLOR_TEXT = "#ffffff"
COLOR_BORDER = "#3a3a3c"
COLOR_BTN_BG = "#4c4c4e"

class WordleUI:
    def __init__(self, root, engine):
        self.root = root
        self.engine = engine
        
        self.root.title("Python Wordle AI")
        self.root.geometry("650x950") # Increased height slightly for controls
        self.root.configure(bg=COLOR_DEFAULT_BG)
        
        self.current_guess_chars = [] 
        
        # Solver review state
        self.solver_history = []
        self.solver_step_index = 0
        self.is_review_mode = False

        self._setup_layout()
        self._bind_events()

    def _setup_layout(self):
        # 1. Title
        lbl_title = tk.Label(self.root, text="WORDLE AI", font=("Helvetica", 36, "bold"), 
                             bg=COLOR_DEFAULT_BG, fg=COLOR_TEXT)
        lbl_title.pack(pady=(20, 5))

        # 2. Message Area
        self.msg_label = tk.Label(self.root, text="Ready", font=("Helvetica", 14), 
                                  bg=COLOR_DEFAULT_BG, fg=COLOR_PRESENT)
        self.msg_label.pack(pady=(0, 10))

        # 3. Game Grid
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

        # 4. Manual Controls
        controls_frame = tk.Frame(self.root, bg=COLOR_DEFAULT_BG)
        controls_frame.pack(pady=10)
        btn_config = {"font": ("Helvetica", 10, "bold"), "bg": COLOR_BTN_BG, "fg": COLOR_TEXT, "width": 8, "relief": "flat"}
        
        tk.Button(controls_frame, text="ENTER", command=self.submit_guess, **btn_config).pack(side="left", padx=5)
        tk.Button(controls_frame, text="RESET", command=self.reset_ui, **btn_config).pack(side="left", padx=5)

        # 5. AI Solver Menu
        solver_frame = tk.LabelFrame(self.root, text="AI Solvers", font=("Helvetica", 10),
                                     bg=COLOR_DEFAULT_BG, fg=COLOR_UNTESTED, padx=10, pady=5)
        solver_frame.pack(pady=5, fill="x", padx=40)

        solver_btn_config = {"font": ("Helvetica", 9), "bg": "#2c2c2e", "fg": COLOR_TEXT, "width": 6, "relief": "raised"}

        # Algorithm Buttons
        tk.Button(solver_frame, text="BFS", command=lambda: self.run_solver("BFS"), **solver_btn_config).pack(side="left", padx=5)
        tk.Button(solver_frame, text="DFS", command=lambda: self.run_solver("DFS"), **solver_btn_config).pack(side="left", padx=5)
        tk.Button(solver_frame, text="UCS", command=lambda: self.run_solver("UCS"), **solver_btn_config).pack(side="left", padx=5)
        tk.Button(solver_frame, text="A*", command=lambda: self.run_solver("A*"), **solver_btn_config).pack(side="left", padx=5)
        
        tk.Button(solver_frame, text="Bench", command=self.run_benchmark_ui, bg="#8B0000", fg="white", font=("Helvetica", 9, "bold")).pack(side="right", padx=10)

        # 6. Navigation Controls (Hidden by default)
        self.nav_frame = tk.Frame(self.root, bg=COLOR_DEFAULT_BG)
        # We pack it later when needed
        
        nav_btn_config = {"font": ("Helvetica", 12, "bold"), "bg": COLOR_PRESENT, "fg": "black", "width": 4}
        self.btn_prev = tk.Button(self.nav_frame, text="<", command=lambda: self.navigate_solver(-1), **nav_btn_config)
        self.btn_prev.pack(side="left", padx=20)
        
        self.lbl_step = tk.Label(self.nav_frame, text="Step 0/0", font=("Helvetica", 12), bg=COLOR_DEFAULT_BG, fg=COLOR_TEXT)
        self.lbl_step.pack(side="left", padx=10)

        self.btn_next = tk.Button(self.nav_frame, text=">", command=lambda: self.navigate_solver(1), **nav_btn_config)
        self.btn_next.pack(side="left", padx=20)

        # 7. Stats Display
        self.stats_label = tk.Label(self.root, text="", font=("Courier New", 10), justify="left",
                                    bg=COLOR_DEFAULT_BG, fg=COLOR_UNTESTED)
        self.stats_label.pack(pady=5)

        # 8. Keyboard
        self.kb_frame = tk.Frame(self.root, bg=COLOR_DEFAULT_BG)
        self.kb_frame.pack(pady=10)
        self.key_buttons = {}
        for row_keys in ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]:
            row_frame = tk.Frame(self.kb_frame, bg=COLOR_DEFAULT_BG)
            row_frame.pack()
            for char in row_keys:
                btn = tk.Label(row_frame, text=char, font=("Helvetica", 10, "bold"),
                               width=3, height=1, bg=COLOR_UNTESTED, fg=COLOR_TEXT, relief="flat")
                btn.pack(side="left", padx=1, pady=1)
                self.key_buttons[char] = btn
        
    def _bind_events(self):
        self.root.bind("<Key>", self._handle_keypress)
        self.root.bind("<Left>", lambda e: self.navigate_solver(-1))
        self.root.bind("<Right>", lambda e: self.navigate_solver(1))

    def _handle_keypress(self, event):
        if self.is_review_mode:
            if event.keysym == 'Return': self.reset_ui()
            return

        if self.engine.game_over: 
            if event.keysym == 'Return': self.reset_ui()
            return
            
        key = event.keysym.upper()
        if len(key) == 1 and key.isalpha():
            if len(self.current_guess_chars) < 5:
                self.current_guess_chars.append(key)
        elif key == "BACKSPACE":
            if self.current_guess_chars: self.current_guess_chars.pop()
        elif key == "RETURN":
            if len(self.current_guess_chars) == 5: self.submit_guess()
        self._update_grid_preview()

    def _update_grid_preview(self):
        if self.is_review_mode: return
        row_idx = len(self.engine.guesses)
        if row_idx >= 6: return
        chars = self.current_guess_chars
        for col in range(5):
            text = chars[col] if col < len(chars) else ""
            self.cells[row_idx][col]["lbl"].config(text=text)

    def submit_guess(self):
        if self.engine.game_over or self.is_review_mode: return
        guess_str = "".join(self.current_guess_chars)
        if len(guess_str) != 5:
            self.set_message("Not enough letters")
            return
        if not self.engine.is_valid_word(guess_str):
            self.set_message("Not in word list")
            return
        results = self.engine.process_guess(guess_str)
        self._update_ui_after_guess(results)

    def _update_ui_after_guess(self, results):
        row_idx = len(self.engine.guesses) - 1
        # Should not happen if game over logic works, but safety check
        if row_idx >= 6: return 

        for col, status in enumerate(results):
            color = COLOR_ABSENT
            if status == "CORRECT": color = COLOR_CORRECT
            elif status == "PRESENT": color = COLOR_PRESENT
            self.cells[row_idx][col]["lbl"].config(bg=color, text=self.engine.guesses[row_idx][col])
            self.cells[row_idx][col]["frame"].config(bg=color)
        
        self._update_keyboard(self.engine.letter_states)
        self.current_guess_chars = []
        if self.engine.game_over:
            if self.engine.is_win: self.set_message(f"Solved! ({len(self.engine.guesses)} guesses)")
            else: self.set_message(f"Failed. Word: {self.engine.secret_word}")

    def _update_keyboard(self, letter_states):
        # Reset all first
        for btn in self.key_buttons.values():
            btn.config(bg=COLOR_UNTESTED)
            
        for char, state in letter_states.items():
            if char in self.key_buttons:
                color = COLOR_UNTESTED
                if state == "CORRECT": color = COLOR_CORRECT
                elif state == "PRESENT": color = COLOR_PRESENT
                elif state == "ABSENT": color = COLOR_ABSENT 
                self.key_buttons[char].config(bg=color)

    def set_message(self, text):
        self.msg_label.config(text=text)

    def reset_ui(self):
        self.engine.start_game()
        self.current_guess_chars = []
        self.is_review_mode = False
        self.solver_history = []
        self.nav_frame.pack_forget() # Hide nav controls
        
        self.set_message("New Game Started")
        self.stats_label.config(text="")
        
        # Clear grid
        for row in range(6):
            for col in range(5):
                self.cells[row][col]["lbl"].config(text="", bg=COLOR_DEFAULT_BG)
                self.cells[row][col]["frame"].config(bg=COLOR_BORDER)
        
        # Clear keyboard
        for btn in self.key_buttons.values():
            btn.config(bg=COLOR_UNTESTED)

    # --- SOLVER INTEGRATION ---
    def run_solver(self, strategy):
        if self.engine.game_over or self.is_review_mode:
            self.reset_ui()

        strategy_map = {
            "BFS": "bfs-opt",
            "DFS": "dfs-opt",
            "UCS": "ucs-constant",
            "A*": "dumb-random-then-astar"
        }
        solver_key = strategy_map.get(strategy)
        if not solver_key:
            self.set_message(f"Unknown strategy {strategy}")
            return

        solver = OPTIMIZED_SOLVERS[solver_key]

        self.set_message(f"AI ({strategy}) is thinking...")
        self.root.update()

        def solve_thread():
            # Run solver with high attempt limit (ignore standard 6 limit)
            result = solver.solve(
                answer=self.engine.secret_word,
                word_pool=self.engine.word_list,
                max_attempts=20, 
            )

            # Update UI on main thread
            self.root.after(0, lambda: self._on_solver_finished(result, strategy))

        threading.Thread(target=solve_thread, daemon=True).start()

    def _on_solver_finished(self, result, strategy):
        self.is_review_mode = True
        self.solver_history = result.history
        self.solver_step_index = 0
        
        # Display Stats
        stats_text = (
            f"Strategy: {strategy} | Solved: {result.success}\n"
            f"Guesses: {len(result.history)} | Expanded: {result.expanded_nodes}\n"
            f"Generated: {result.generated_nodes} | Frontier Max: {result.frontier_max}\n"
            f"Use arrow keys or buttons to review steps."
        )
        self.stats_label.config(text=stats_text)
        
        # Show Navigation Controls
        self.nav_frame.pack(pady=5, before=self.stats_label)
        
        # Render first step (or empty)
        self._render_solver_state()

    def navigate_solver(self, direction):
        if not self.is_review_mode or not self.solver_history:
            return
            
        new_index = self.solver_step_index + direction
        
        # Clamp index
        # We allow index to go from 0 (before first guess) to len(history) (full view)
        max_idx = len(self.solver_history)
        if 0 <= new_index <= max_idx:
            self.solver_step_index = new_index
            self._render_solver_state()

    def _render_solver_state(self):
        # Determine which slice of history to show
        # current_idx implies how many guesses have been made.
        # If idx=3, we show guesses 0, 1, 2.
        
        guesses_to_show = self.solver_history[:self.solver_step_index]
        total_steps = len(self.solver_history)
        
        self.lbl_step.config(text=f"Step {self.solver_step_index}/{total_steps}")
        
        # Scrolling logic: If we have more than 6 guesses, show the *latest* 6
        start_idx = 0
        if len(guesses_to_show) > 6:
            start_idx = len(guesses_to_show) - 6
            
        visible_guesses = guesses_to_show[start_idx:]
        
        # 1. Clear Grid
        for row in range(6):
            for col in range(5):
                self.cells[row][col]["lbl"].config(text="", bg=COLOR_DEFAULT_BG)
                self.cells[row][col]["frame"].config(bg=COLOR_BORDER)
                
        # 2. Fill Grid with visible slice
        for r, (word, feedback_tuple) in enumerate(visible_guesses):
            for c, mark in enumerate(feedback_tuple):
                # Mark is an Enum or object from feedback.py. 
                # Assuming simple string mapping or direct attribute if using the user's Mark class
                # Based on user files, Mark is likely an Enum. Convert to string key.
                status = str(mark).upper().replace("MARK.", "") # Handle "Mark.CORRECT" -> "CORRECT"
                
                color = COLOR_ABSENT
                if "CORRECT" in status: color = COLOR_CORRECT
                elif "PRESENT" in status: color = COLOR_PRESENT
                
                self.cells[r][c]["lbl"].config(text=word[c], bg=color)
                self.cells[r][c]["frame"].config(bg=color)

        # 3. Update Keyboard (based on ALL guesses up to this point)
        temp_kb_state = {}
        for (word, feedback_tuple) in guesses_to_show:
            for i, char in enumerate(word):
                mark = str(feedback_tuple[i]).upper()
                current = temp_kb_state.get(char, "UNTESTED")
                
                if "CORRECT" in mark:
                    temp_kb_state[char] = "CORRECT"
                elif "PRESENT" in mark and current != "CORRECT":
                    temp_kb_state[char] = "PRESENT"
                elif "ABSENT" in mark and current not in ["CORRECT", "PRESENT"]:
                    temp_kb_state[char] = "ABSENT"
                    
        self._update_keyboard(temp_kb_state)

    def run_benchmark_ui(self):
        self.set_message("Running Benchmark in Console...")
        self.root.update()
        print("Benchmark triggered - implementation would go here.")
        self.set_message("Benchmark Complete. Check Console.")