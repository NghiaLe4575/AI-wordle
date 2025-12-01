# ui/graphic.py - Add this to your existing file

import tkinter as tk
from tkinter import ttk
import threading
from solver.solvers import OPTIMIZED_SOLVERS

# ============== MODERN LIGHT THEME ==============
COLORS = {
    # Main backgrounds
    'bg_primary': '#FFFFFF',        # White background
    'bg_secondary': '#F7F7F7',      # Light gray panels
    'bg_tertiary': '#E8E8E8',       # Slightly darker for contrast
    
    # Cell colors
    'correct': '#6AAA64',           # Green
    'present': '#C9B458',           # Yellow/Gold
    'absent': '#787C7E',            # Gray
    'empty': '#FFFFFF',             # White empty cell
    'empty_border': '#D3D6DA',      # Light border for empty cells
    
    # Text colors
    'text_primary': '#1A1A1B',      # Dark text
    'text_secondary': '#5A5A5A',    # Medium gray text
    'text_light': '#FFFFFF',        # White text (on colored backgrounds)
    'text_accent': '#538D4E',       # Green accent text
    
    # Button colors
    'btn_primary': '#538D4E',       # Green buttons
    'btn_secondary': '#878A8C',     # Gray buttons
    'btn_danger': '#DC3545',        # Red buttons
    'btn_hover': '#6AAA64',         # Hover state
    
    # Keyboard
    'key_default': '#D3D6DA',       # Default key
    'key_text': '#1A1A1B',          # Key text
}

class WordleUI:
    def __init__(self, root, engine):
        self.root = root
        self.engine = engine
        
        self.root.title("Wordle AI Solver")
        self.root.geometry("1100x700")  # Landscape orientation
        self.root.configure(bg=COLORS['bg_primary'])
        self.root.resizable(True, True)
        
        self.current_guess_chars = []
        self.solver_history = []
        self.solver_step_index = 0
        self.is_review_mode = False

        self._setup_styles()
        self._setup_layout()
        self._bind_events()

    def _setup_styles(self):
        """Configure ttk styles for modern look"""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Button styles
        self.style.configure('Primary.TButton',
            font=('Segoe UI', 11, 'bold'),
            padding=(15, 8),
            background=COLORS['btn_primary'],
            foreground=COLORS['text_light']
        )
        self.style.configure('Secondary.TButton',
            font=('Segoe UI', 10),
            padding=(12, 6),
            background=COLORS['btn_secondary']
        )

    def _setup_layout(self):
        """Create landscape layout with left game area and right controls"""
        
        # Main container with padding
        main_container = tk.Frame(self.root, bg=COLORS['bg_primary'], padx=20, pady=15)
        main_container.pack(fill='both', expand=True)
        
        # ===== LEFT PANEL: Game Grid + Keyboard =====
        left_panel = tk.Frame(main_container, bg=COLORS['bg_primary'])
        left_panel.pack(side='left', fill='both', expand=True)
        
        # Title
        title_frame = tk.Frame(left_panel, bg=COLORS['bg_primary'])
        title_frame.pack(pady=(0, 10))
        
        tk.Label(title_frame, text="WORDLE", 
                 font=('Segoe UI Black', 32, 'bold'),
                 bg=COLORS['bg_primary'], 
                 fg=COLORS['text_primary']).pack()
        tk.Label(title_frame, text="AI SOLVER", 
                 font=('Segoe UI', 12),
                 bg=COLORS['bg_primary'], 
                 fg=COLORS['text_secondary']).pack()
        
        # Message Area
        self.msg_label = tk.Label(left_panel, text="Type a word or select an AI solver", 
                                  font=('Segoe UI', 12),
                                  bg=COLORS['bg_primary'], 
                                  fg=COLORS['text_accent'])
        self.msg_label.pack(pady=(5, 15))
        
        # Game Grid Container
        grid_container = tk.Frame(left_panel, bg=COLORS['bg_primary'])
        grid_container.pack(pady=10)
        
        self.cells = []
        for row in range(6):
            row_cells = []
            for col in range(5):
                # Outer frame for border effect
                cell_frame = tk.Frame(grid_container, 
                                      width=62, height=62,
                                      bg=COLORS['empty_border'],
                                      highlightthickness=0)
                cell_frame.grid(row=row, column=col, padx=3, pady=3)
                cell_frame.pack_propagate(False)
                
                # Inner label
                cell_lbl = tk.Label(cell_frame, text="", 
                                    font=('Segoe UI Black', 26, 'bold'),
                                    bg=COLORS['empty'],
                                    fg=COLORS['text_primary'])
                cell_lbl.pack(expand=True, fill='both', padx=2, pady=2)
                row_cells.append({"frame": cell_frame, "lbl": cell_lbl})
            self.cells.append(row_cells)
        
        # Keyboard
        self.kb_frame = tk.Frame(left_panel, bg=COLORS['bg_primary'])
        self.kb_frame.pack(pady=20)
        
        self.key_buttons = {}
        keyboard_rows = [
            list("QWERTYUIOP"),
            list("ASDFGHJKL"),
            ["ENTER"] + list("ZXCVBNM") + ["⌫"]
        ]
        
        for row_keys in keyboard_rows:
            row_frame = tk.Frame(self.kb_frame, bg=COLORS['bg_primary'])
            row_frame.pack(pady=4)
            
            for key in row_keys:
                if key in ["ENTER", "⌫"]:
                    width = 65
                    font_size = 11
                else:
                    width = 44
                    font_size = 14
                
                btn = tk.Button(row_frame, text=key,
                               font=('Segoe UI', font_size, 'bold'),
                               width=0,
                               bg=COLORS['key_default'],
                               fg=COLORS['key_text'],
                               activebackground=COLORS['bg_tertiary'],
                               relief='flat',
                               bd=0,
                               highlightthickness=0,
                               cursor='hand2')
                btn.configure(width=width//10, height=2 if key not in ["ENTER", "⌫"] else 2)
                
                # Bind click events
                if key == "ENTER":
                    btn.configure(command=self.submit_guess)
                elif key == "⌫":
                    btn.configure(command=self._backspace)
                else:
                    btn.configure(command=lambda k=key: self._key_click(k))
                
                btn.pack(side='left', padx=3)
                
                if key not in ["ENTER", "⌫"]:
                    self.key_buttons[key] = btn
        
        # ===== RIGHT PANEL: Controls + Stats =====
        right_panel = tk.Frame(main_container, bg=COLORS['bg_secondary'], width=320)
        right_panel.pack(side='right', fill='y', padx=(20, 0))
        right_panel.pack_propagate(False)
        
        # Right panel inner padding
        right_inner = tk.Frame(right_panel, bg=COLORS['bg_secondary'], padx=20, pady=20)
        right_inner.pack(fill='both', expand=True)
        
        # Section: Game Controls
        tk.Label(right_inner, text="GAME CONTROLS",
                font=('Segoe UI', 10, 'bold'),
                bg=COLORS['bg_secondary'],
                fg=COLORS['text_secondary']).pack(anchor='w', pady=(0, 10))
        
        game_btns = tk.Frame(right_inner, bg=COLORS['bg_secondary'])
        game_btns.pack(fill='x', pady=(0, 20))
        
        self._create_button(game_btns, "NEW GAME", self.reset_ui, COLORS['btn_primary']).pack(fill='x', pady=3)
        
        # Separator
        ttk.Separator(right_inner, orient='horizontal').pack(fill='x', pady=15)
        
        # Section: AI Solvers
        tk.Label(right_inner, text="AI SOLVERS",
                font=('Segoe UI', 10, 'bold'),
                bg=COLORS['bg_secondary'],
                fg=COLORS['text_secondary']).pack(anchor='w', pady=(0, 10))
        
        solver_grid = tk.Frame(right_inner, bg=COLORS['bg_secondary'])
        solver_grid.pack(fill='x', pady=(0, 10))
        
        # Solver buttons in 2x2 grid
        solvers = [("BFS", "BFS"), ("DFS", "DFS"), ("UCS", "UCS"), ("A*", "A*")]
        for i, (label, strategy) in enumerate(solvers):
            btn = self._create_button(solver_grid, label, 
                                      lambda s=strategy: self.run_solver(s),
                                      COLORS['btn_secondary'])
            btn.grid(row=i//2, column=i%2, padx=3, pady=3, sticky='ew')
        
        solver_grid.columnconfigure(0, weight=1)
        solver_grid.columnconfigure(1, weight=1)
        
        # Benchmark button
        self._create_button(right_inner, "⏱ RUN BENCHMARK", self.run_benchmark_ui, 
                           COLORS['btn_danger']).pack(fill='x', pady=(10, 0))
        
        # Separator
        ttk.Separator(right_inner, orient='horizontal').pack(fill='x', pady=15)
        
        # Section: Navigation (hidden by default)
        self.nav_frame = tk.Frame(right_inner, bg=COLORS['bg_secondary'])
        
        nav_row = tk.Frame(self.nav_frame, bg=COLORS['bg_secondary'])
        nav_row.pack(fill='x', pady=10)
        
        self.btn_prev = tk.Button(nav_row, text="◀ PREV", 
                                  font=('Segoe UI', 10, 'bold'),
                                  bg=COLORS['btn_secondary'],
                                  fg=COLORS['text_light'],
                                  relief='flat',
                                  cursor='hand2',
                                  command=lambda: self.navigate_solver(-1))
        self.btn_prev.pack(side='left', expand=True, fill='x', padx=(0, 5))
        
        self.btn_next = tk.Button(nav_row, text="NEXT ▶",
                                  font=('Segoe UI', 10, 'bold'),
                                  bg=COLORS['btn_secondary'],
                                  fg=COLORS['text_light'],
                                  relief='flat',
                                  cursor='hand2',
                                  command=lambda: self.navigate_solver(1))
        self.btn_next.pack(side='right', expand=True, fill='x', padx=(5, 0))
        
        self.lbl_step = tk.Label(self.nav_frame, text="Step 0/0",
                                 font=('Segoe UI', 12, 'bold'),
                                 bg=COLORS['bg_secondary'],
                                 fg=COLORS['text_primary'])
        self.lbl_step.pack(pady=5)
        
        # Section: Statistics
        tk.Label(right_inner, text="STATISTICS",
                font=('Segoe UI', 10, 'bold'),
                bg=COLORS['bg_secondary'],
                fg=COLORS['text_secondary']).pack(anchor='w', pady=(0, 10))
        
        self.stats_label = tk.Label(right_inner, text="No solver run yet",
                                    font=('Consolas', 9),
                                    bg=COLORS['bg_secondary'],
                                    fg=COLORS['text_secondary'],
                                    justify='left',
                                    anchor='nw')
        self.stats_label.pack(fill='both', expand=True)

    def _create_button(self, parent, text, command, color):
        """Create a styled button"""
        btn = tk.Button(parent, text=text,
                       font=('Segoe UI', 10, 'bold'),
                       bg=color,
                       fg=COLORS['text_light'],
                       activebackground=COLORS['btn_hover'],
                       activeforeground=COLORS['text_light'],
                       relief='flat',
                       bd=0,
                       padx=15, pady=8,
                       cursor='hand2',
                       command=command)
        return btn

    def _key_click(self, key):
        """Handle virtual keyboard click"""
        if len(self.current_guess_chars) < 5:
            self.current_guess_chars.append(key)
            self._update_grid_preview()

    def _backspace(self):
        """Handle backspace"""
        if self.current_guess_chars:
            self.current_guess_chars.pop()
            self._update_grid_preview()

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
            self.set_message("⚠ Not enough letters")
            return
        if not self.engine.is_valid_word(guess_str):
            self.set_message("⚠ Not in word list")
            return
        results = self.engine.process_guess(guess_str)
        self._update_ui_after_guess(results)

    def _update_ui_after_guess(self, results):
        row_idx = len(self.engine.guesses) - 1
        if row_idx >= 6: return 

        for col, status in enumerate(results):
            if status == "CORRECT":
                bg_color = COLORS['correct']
                fg_color = COLORS['text_light']
            elif status == "PRESENT":
                bg_color = COLORS['present']
                fg_color = COLORS['text_light']
            else:
                bg_color = COLORS['absent']
                fg_color = COLORS['text_light']
            
            self.cells[row_idx][col]["lbl"].config(bg=bg_color, fg=fg_color,
                                                   text=self.engine.guesses[row_idx][col])
            self.cells[row_idx][col]["frame"].config(bg=bg_color)
        
        self._update_keyboard(self.engine.letter_states)
        self.current_guess_chars = []
        
        if self.engine.game_over:
            if self.engine.is_win:
                self.set_message(f"🎉 Solved in {len(self.engine.guesses)} guesses!")
            else:
                self.set_message(f"❌ The word was: {self.engine.secret_word}")

    def _update_keyboard(self, letter_states):
        for btn in self.key_buttons.values():
            btn.config(bg=COLORS['key_default'], fg=COLORS['key_text'])
            
        for char, state in letter_states.items():
            if char in self.key_buttons:
                if state == "CORRECT":
                    self.key_buttons[char].config(bg=COLORS['correct'], fg=COLORS['text_light'])
                elif state == "PRESENT":
                    self.key_buttons[char].config(bg=COLORS['present'], fg=COLORS['text_light'])
                elif state == "ABSENT":
                    self.key_buttons[char].config(bg=COLORS['absent'], fg=COLORS['text_light'])

    def set_message(self, text):
        self.msg_label.config(text=text)

    def reset_ui(self):
        self.engine.start_game()
        self.current_guess_chars = []
        self.is_review_mode = False
        self.solver_history = []
        self.nav_frame.pack_forget()
        
        self.set_message("New game started! Type a word or select an AI solver")
        self.stats_label.config(text="No solver run yet")
        
        for row in range(6):
            for col in range(5):
                self.cells[row][col]["lbl"].config(text="", 
                                                   bg=COLORS['empty'],
                                                   fg=COLORS['text_primary'])
                self.cells[row][col]["frame"].config(bg=COLORS['empty_border'])
        
        for btn in self.key_buttons.values():
            btn.config(bg=COLORS['key_default'], fg=COLORS['key_text'])

    # --- SOLVER INTEGRATION ---
    # --- SOLVER INTEGRATION ---
    def run_solver(self, strategy):
        if self.engine.game_over or self.is_review_mode:
            self.reset_ui()

        strategy_map = {
            "BFS": "bfs-opt",
            "DFS": "dfs-opt",
            "UCS": "ucs-entropy",
            "A*": "astar-reduction-log2"
        }
        solver_key = strategy_map.get(strategy)
        if not solver_key:
            self.set_message(f"⚠ Unknown strategy: {strategy}")
            return

        solver = OPTIMIZED_SOLVERS[solver_key]
        self.set_message(f"🤖 AI ({strategy}) is thinking...")
        self.root.update()

        def solve_thread():
            result = solver.solve(
                answer=self.engine.secret_word,
                word_pool=self.engine.word_list,
                max_attempts=20,
            )
            self.root.after(0, lambda: self._on_solver_finished(result, strategy))

        threading.Thread(target=solve_thread, daemon=True).start()

    def _on_solver_finished(self, result, strategy):
        self.is_review_mode = True
        self.solver_history = result.history
        self.solver_step_index = 0
        
        stats_text = (
            f"Strategy: {strategy}\n"
            f"Result: {'✓ Solved' if result.success else '✗ Failed'}\n"
            f"─────────────────\n"
            f"Guesses:    {len(result.history)}\n"
            f"Expanded:   {result.expanded_nodes:,}\n"
            f"Generated:  {result.generated_nodes:,}\n"
            f"Max Front:  {result.frontier_max:,}\n"
            f"─────────────────\n"
            f"Use ◀ ▶ to step through"
        )
        self.stats_label.config(text=stats_text)
        
        self.nav_frame.pack(fill='x', pady=(0, 15))
        self._render_solver_state()

    def navigate_solver(self, direction):
        if not self.is_review_mode or not self.solver_history:
            return
        new_index = self.solver_step_index + direction
        max_idx = len(self.solver_history)
        if 0 <= new_index <= max_idx:
            self.solver_step_index = new_index
            self._render_solver_state()

    def _render_solver_state(self):
        guesses_to_show = self.solver_history[:self.solver_step_index]
        total_steps = len(self.solver_history)
        
        self.lbl_step.config(text=f"Step {self.solver_step_index} / {total_steps}")
        
        start_idx = 0
        if len(guesses_to_show) > 6:
            start_idx = len(guesses_to_show) - 6
        visible_guesses = guesses_to_show[start_idx:]
        
        # Clear Grid
        for row in range(6):
            for col in range(5):
                self.cells[row][col]["lbl"].config(text="", 
                                                   bg=COLORS['empty'],
                                                   fg=COLORS['text_primary'])
                self.cells[row][col]["frame"].config(bg=COLORS['empty_border'])
                
        # Fill Grid
        for r, (word, feedback_tuple) in enumerate(visible_guesses):
            for c, mark in enumerate(feedback_tuple):
                status = str(mark).upper().replace("MARK.", "")
                
                if "CORRECT" in status:
                    bg_color = COLORS['correct']
                elif "PRESENT" in status:
                    bg_color = COLORS['present']
                else:
                    bg_color = COLORS['absent']
                
                self.cells[r][c]["lbl"].config(text=word[c], bg=bg_color, fg=COLORS['text_light'])
                self.cells[r][c]["frame"].config(bg=bg_color)

        # Update Keyboard
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
        import time, statistics, random, tracemalloc
        self.set_message("⏱ Benchmark running... check console")
        self.root.update()

        def benchmark_thread():
            solver_configs = {
                "BFS": "bfs-opt",
                "DFS": "dfs-opt",
                "UCS-Const": "ucs-constant",
                "UCS-Red": "ucs-reduction",
                "UCS-Part": "ucs-partition",
                "UCS-Ent": "ucs-entropy",
                "A*-Const-Log2": "astar-constant-log2",
                "A*-Red-Log2": "astar-reduction-log2",
                "A*-Const-Part": "astar-constant-partition",
                "A*-Red-Part": "astar-reduction-partition",
            }
            num_tests = 20
            test_answers = random.sample(self.engine.word_list, min(num_tests, len(self.engine.word_list)))

            print("\n" + "="*100)
            print("  WORDLE SOLVER BENCHMARK")
            print("="*100)
            print(f"  Dictionary: {len(self.engine.word_list):,} words | Tests: {len(test_answers)} | Max attempts: {self.engine.max_guesses}\n")

            all_results = {}

            for solver_label, solver_key in solver_configs.items():
                if solver_key not in OPTIMIZED_SOLVERS:
                    print(f"  ⚠ {solver_label}: Not available")
                    continue
                solver = OPTIMIZED_SOLVERS[solver_key]
                results = {
                    'guesses': [], 'expanded_nodes': [], 'generated_nodes': [],
                    'frontier_max': [], 'times': [], 'memories': [], 'successes': 0,
                }
                print(f"  Testing {solver_label:<15}", end='', flush=True)
                start_time = time.time()
                tracemalloc.start()
                for answer in test_answers:
                    try:
                        t0 = time.time()
                        snapshot_before = tracemalloc.take_snapshot()
                        result = solver.solve(
                            answer=answer,
                            word_pool=self.engine.word_list,
                            max_attempts=self.engine.max_guesses,
                            starting_candidates=['SLATE', 'STARE', 'SPARE', 'STORE', 'AROSE',
                                                'RAISE', 'STALE', 'STERN', 'STEAL', 'SAVER']
                        )
                        elapsed = time.time() - t0
                        snapshot_after = tracemalloc.take_snapshot()
                        mem_diff = snapshot_after.compare_to(snapshot_before, 'filename')
                        mem_usage = sum([stat.size_diff for stat in mem_diff]) / 1024
                        if result.success:
                            results['guesses'].append(len(result.history))
                            results['expanded_nodes'].append(result.expanded_nodes)
                            results['generated_nodes'].append(result.generated_nodes)
                            results['frontier_max'].append(result.frontier_max)
                            results['times'].append(elapsed)
                            results['memories'].append(mem_usage)
                            results['successes'] += 1
                    except Exception as e:
                        print(f"\n    Error on {answer}: {e}")
                        continue
                tracemalloc.stop()
                elapsed_total = time.time() - start_time
                if results['successes'] > 0:
                    all_results[solver_label] = {
                        'success_rate': results['successes'] / len(test_answers),
                        'avg_guesses': statistics.mean(results['guesses']),
                        'std_guesses': statistics.stdev(results['guesses']) if len(results['guesses']) > 1 else 0,
                        'avg_expanded': statistics.mean(results['expanded_nodes']),
                        'avg_generated': statistics.mean(results['generated_nodes']),
                        'avg_frontier': statistics.mean(results['frontier_max']),
                        'avg_time': statistics.mean(results['times']),
                        'avg_memory': statistics.mean(results['memories']),
                    }
                    print(f" ✓ ({elapsed_total:.1f}s)")
                else:
                    print(f" ✗ (failed)")

            print("\n" + "="*120)
            print(f"  {'Solver':<16} {'Success':>8} {'Avg Guess':>12} {'Expanded':>14} {'Generated':>12} {'Frontier':>12} {'Time':>10}")
            print("="*120)
            for solver_label in sorted(all_results.keys(), key=lambda x: all_results[x]['avg_guesses']):
                s = all_results[solver_label]
                print(f"  {solver_label:<16} {s['success_rate']*100:>7.0f}% "
                      f"{s['avg_guesses']:>6.2f}±{s['std_guesses']:<4.2f} "
                      f"{s['avg_expanded']:>14,.0f} {s['avg_generated']:>12,.0f} "
                      f"{s['avg_frontier']:>12,.0f} {s['avg_time']:>9.3f}s")
            print("="*120)
            print("\n  ✓ Benchmark complete!\n")
            
            best = min(all_results.items(), key=lambda x: x[1]['avg_guesses'])
            self.set_message(f"✓ Done! Best: {best[0]} ({best[1]['avg_guesses']:.2f} avg)")

        threading.Thread(target=benchmark_thread, daemon=True).start()
