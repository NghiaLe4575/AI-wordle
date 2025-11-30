# ui/graphic.py - Add this to your existing file

import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import time
import statistics
import random
from solver.solvers import OPTIMIZED_SOLVERS

# Configuration (same as before)
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
        self.root.geometry("650x900")
        self.root.configure(bg=COLOR_DEFAULT_BG)
        
        self.current_guess_chars = []
        self.starting_candidates = [
            'SLATE', 'STARE', 'SPARE', 'STORE', 'AROSE',
            'RAISE', 'STALE', 'STERN', 'STEAL', 'SAVER'
        ]
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
        solver_frame = tk.LabelFrame(self.root, text="AI Solvers & Metrics", font=("Helvetica", 10),
                                     bg=COLOR_DEFAULT_BG, fg=COLOR_UNTESTED, padx=10, pady=5)
        solver_frame.pack(pady=5, fill="x", padx=40)

        solver_btn_config = {"font": ("Helvetica", 9), "bg": "#2c2c2e", "fg": COLOR_TEXT, "width": 8, "relief": "raised"}

        # Algorithm Buttons
        tk.Button(solver_frame, text="BFS", command=lambda: self.run_solver("BFS"), **solver_btn_config).pack(side="left", padx=5)
        tk.Button(solver_frame, text="DFS", command=lambda: self.run_solver("DFS"), **solver_btn_config).pack(side="left", padx=5)
        tk.Button(solver_frame, text="UCS", command=lambda: self.run_solver("UCS"), **solver_btn_config).pack(side="left", padx=5)
        tk.Button(solver_frame, text="A*", command=lambda: self.run_solver("A*"), **solver_btn_config).pack(side="left", padx=5)
        
        # Benchmark Button
        tk.Button(solver_frame, text="Benchmark", command=self.run_benchmark_ui, bg="#8B0000", fg="white", font=("Helvetica", 9, "bold")).pack(side="right", padx=10)

        # 6. Stats Display
        self.stats_label = tk.Label(self.root, text="", font=("Courier New", 10), justify="left",
                                    bg=COLOR_DEFAULT_BG, fg=COLOR_UNTESTED)
        self.stats_label.pack(pady=10)

        # 7. Keyboard
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
        self._bind_events()

    def _bind_events(self):
        self.root.bind("<Key>", self._handle_keypress)

    def _handle_keypress(self, event):
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
        row_idx = len(self.engine.guesses)
        if row_idx >= 6: return
        chars = self.current_guess_chars
        for col in range(5):
            text = chars[col] if col < len(chars) else ""
            self.cells[row_idx][col]["lbl"].config(text=text)

    def submit_guess(self):
        if self.engine.game_over: return
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
        for col, status in enumerate(results):
            color = COLOR_ABSENT
            if status == "CORRECT": color = COLOR_CORRECT
            elif status == "PRESENT": color = COLOR_PRESENT
            self.cells[row_idx][col]["lbl"].config(bg=color, text=self.engine.guesses[row_idx][col])
            self.cells[row_idx][col]["frame"].config(bg=color)
        
        self._update_keyboard()
        self.current_guess_chars = []
        if self.engine.game_over:
            if self.engine.is_win: self.set_message(f"Solved! ({len(self.engine.guesses)} guesses)")
            else: self.set_message(f"Failed. Word: {self.engine.secret_word}")

    def _update_keyboard(self):
        for char, state in self.engine.letter_states.items():
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
        self.set_message("New Game Started")
        self.stats_label.config(text="")
        for row in range(6):
            for col in range(5):
                self.cells[row][col]["lbl"].config(text="", bg=COLOR_DEFAULT_BG)
                self.cells[row][col]["frame"].config(bg=COLOR_BORDER)
        for btn in self.key_buttons.values():
            btn.config(bg=COLOR_UNTESTED)

    # --- SOLVER INTEGRATION ---
    def run_solver(self, strategy):
        if self.engine.game_over:
            self.reset_ui()

        strategy_map = {
            "BFS": "bfs-opt",
            "DFS": "dfs-opt",
            "UCS": "ucs-constant",
            "A*": "astar-constant-log2"
        }
        solver_key = strategy_map.get(strategy)
        if not solver_key:
            self.set_message(f"Unknown strategy {strategy}")
            return

        solver = OPTIMIZED_SOLVERS[solver_key]

        self.set_message(f"AI ({strategy}) is thinking...")
        self.root.update()

        # --- Run solver in background thread ---
        def solve_thread():
            # Run solver
            result = solver.solve(
                answer=self.engine.secret_word,
                word_pool=self.engine.word_list,
                max_attempts=self.engine.max_guesses,
                starting_candidates=self.starting_candidates
            )

            # Animate each guess on the UI thread
            def animate():
                # Clear current guess row
                self.current_guess_chars = []

                for guess, fb in result.history:
                    # Push guess into engine to get UI-compatible Mark objects
                    ui_feedback = self.engine.process_guess(guess)
                    self._update_ui_after_guess(ui_feedback)
                    self.root.update()
                    time.sleep(0.25)

                # Load statistics
                stats_text = (
                    f"Strategy: {strategy}\n"
                    f"Solved:   {'yes' if result.success else 'no'}\n"
                    f"Guesses:  {len(result.history)}\n"
                    f"Expanded: {result.expanded_nodes}\n"
                    f"Generated:{result.generated_nodes}\n"
                    f"Frontier: {result.frontier_max}\n"
                )
                self.stats_label.config(text=stats_text)
                self.set_message("Done.")

            self.root.after(0, animate)

        threading.Thread(target=solve_thread, daemon=True).start()

    # ============ BENCHMARK ============
    def run_benchmark_ui(self):
        """Run benchmark on all solvers and display results in console"""
        self.set_message("⏱️ Benchmark running... (check console output)")
        self.root.update()

        def benchmark_thread():
            # Define all solvers to test
            solver_configs = {
                "BFS": "bfs-opt",
                "DFS": "dfs-opt",
                "UCS-Const": "ucs-constant",
                "UCS-Red": "ucs-reduction",
                "UCS-Part": "ucs-partition",
                "UCS-Ent": "ucs-entropy",
                "A*-Const-Log2": "astar-constant-log2",
                "A*-Red-Log2": "astar-reduction-log2",
                "A*-Const-Partition": "astar-reduction-partition",
                "A*-Red-Partition": "astar-reduction-partition",

            }
            
            num_tests = 20  # Number of random test cases
            test_answers = random.sample(self.engine.word_list, min(num_tests, len(self.engine.word_list)))
            
            print("\n" + "="*80)
            print(f"WORDLE SOLVER BENCHMARK")
            print("="*80)
            print(f"Configuration:")
            print(f"  Dictionary size: {len(self.engine.word_list):,} words")
            print(f"  Test cases: {len(test_answers)}")
            print(f"  Max attempts: {self.engine.max_guesses}")
            print(f"  Starting candidates: {len(self.starting_candidates)}\n")
            
            all_results = {}
            
            # Run each solver
            for solver_label, solver_key in solver_configs.items():
                if solver_key not in OPTIMIZED_SOLVERS:
                    print(f"⚠️ {solver_label}: Not available")
                    continue
                
                solver = OPTIMIZED_SOLVERS[solver_key]
                results = {
                    'guesses': [],
                    'expanded_nodes': [],
                    'generated_nodes': [],
                    'frontier_max': [],
                    'times': [],
                    'successes': 0,
                }
                
                print(f"Testing {solver_label:<15}", end='', flush=True)
                start_time = time.time()
                
                for answer in test_answers:
                    try:
                        t0 = time.time()
                        result = solver.solve(
                            answer=answer,
                            word_pool=self.engine.word_list,
                            max_attempts=self.engine.max_guesses,
                            starting_candidates=self.starting_candidates
                        )
                        elapsed = time.time() - t0
                        
                        if result.success:
                            results['guesses'].append(len(result.history))
                            results['expanded_nodes'].append(result.expanded_nodes)
                            results['generated_nodes'].append(result.generated_nodes)
                            results['frontier_max'].append(result.frontier_max)
                            results['times'].append(elapsed)
                            results['successes'] += 1
                    except Exception as e:
                        print(f"\n  Error on {answer}: {e}")
                        continue
                
                elapsed_total = time.time() - start_time
                
                # Calculate statistics
                if results['successes'] > 0:
                    all_results[solver_label] = {
                        'success_rate': results['successes'] / len(test_answers),
                        'avg_guesses': statistics.mean(results['guesses']),
                        'std_guesses': statistics.stdev(results['guesses']) if len(results['guesses']) > 1 else 0,
                        'min_guesses': min(results['guesses']),
                        'max_guesses': max(results['guesses']),
                        'avg_expanded': statistics.mean(results['expanded_nodes']),
                        'avg_generated': statistics.mean(results['generated_nodes']),
                        'avg_frontier': statistics.mean(results['frontier_max']),
                        'avg_time': statistics.mean(results['times']),
                    }
                    print(f" ✓ ({elapsed_total:.1f}s)")
                else:
                    print(f" ✗ (failed)")
            
            # Print results table
            print("\n" + "="*100)
            print(f"{'Solver':<15} {'Success':<12} {'Avg Guesses':<18} {'Avg Expanded':<16} {'Avg Generated':<16} {'Avg Time':<10}")
            print("="*100)
            
            # Sort by average guesses
            for solver_label in sorted(all_results.keys(), key=lambda x: all_results[x]['avg_guesses']):
                stats = all_results[solver_label]
                print(
                    f"{solver_label:<15} "
                    f"{stats['success_rate']*100:>5.0f}%{'':<6} "
                    f"{stats['avg_guesses']:>6.2f} ± {stats['std_guesses']:>5.2f}  "
                    f"{stats['avg_expanded']:>14,.0f}  "
                    f"{stats['avg_generated']:>14,.0f}  "
                    f"{stats['avg_time']:>8.3f}s"
                )
            
            print("="*100)
            print("\n✓ Benchmark complete!\n")
            
            # Update UI message
            best_solver = min(all_results.items(), key=lambda x: x[1]['avg_guesses'])
            self.set_message(f"✓ Benchmark done! Best: {best_solver[0]} ({best_solver[1]['avg_guesses']:.2f} avg guesses)")

        # Run benchmark in background thread
        threading.Thread(target=benchmark_thread, daemon=True).start()