# AI-wordle
# Wordle Solver: Graph Search Algorithms

Optimized Wordle solver using BFS, DFS, UCS, and A* with information-theoretic cost functions. Achieves 3.43 average guesses on 5,717-word dictionary.

## Folder Structure

```
wordle-solver/
├── data/
│   └── words.txt                 # 5,717 valid 5-letter words
├── engine/
│   └── engine.py                 # Game logic: feedback, state tracking
├── solver/
│   ├── feedback.py               # Mark enum, evaluate_guess()
│   ├── feedback_table.py         # Cached feedback lookups (~400K entries)
│   ├── state.py                  # CompactState: hashable search state
│   ├── search_base.py            # Base solver class, SolverResult
│   ├── solvers.py                # BFS, DFS, UCS, A* implementations
│   ├── cost_functions.py         # 4 cost functions
│   └── heuristic_functions.py    # 3 heuristic functions
├── ui/
│   └── graphic.py                # Tkinter GUI + benchmark
├── main.py                       # Entry point
└── README.md
```

## Quick Start

Launch the GUI and click solver buttons to play or benchmark:

```
python main.py
```

Click **Benchmark** to test all 8 algorithms on 20 random words.

---

## State Formulation

A state represents accumulated search knowledge:

**CompactState:** `(history, remaining_count)`

- **history:** Sequence of (guess, feedback) tuples
  - Example: `(("SLATE", [absent, absent, absent, present, absent]), ("ORBIT", [absent, correct, correct, absent, present]))`
- **remaining_count:** Number of candidate words still consistent with this history

**State Space:** Tree rooted at empty history with 5,717 possible words. Goal is any state where the last guess produces all-correct feedback.

---

## Search_base Explanation

The `OptimizedGraphSearchSolver` base class implements uniform graph search:

### Core Flow

1. **Initialization:** Build FeedbackTable (cache ~400K guess-target pairs)
2. **Frontier:** Initialize with root state (empty history, all words possible)
3. **Main Loop:**
   - Pop state from frontier
   - Skip if visited (duplicate state)
   - Check if goal reached (all green feedback)
   - Stop if depth exceeds max attempts
   - For each candidate guess: compute feedback, filter remaining words, create new state, push to frontier
4. **Return:** SolverResult with success flag, guess sequence, node statistics

### Key Components

**Frontier Abstraction:** Different subclasses implement different frontier types (BFS: deque, UCS/A*: heap)

**Visited Set:** Prevents reprocessing identical states

**Candidate Selection:** Depth 0 uses fixed starting_candidates (deterministic). Depth > 0 uses all remaining words.

**Candidate Filtering:** For each guess, compute feedback against remaining words. Keep only those producing same feedback as the target.

### Output

`SolverResult` contains:
- `success`: Whether puzzle was solved
- `history`: Sequence of guesses and their feedback
- `expanded_nodes`: Number of states popped and processed
- `generated_nodes`: Number of child states created
- `frontier_max`: Peak frontier size (memory usage)
- `final_path`: Ordered list of guesses

---

## Solver Explanation

Eight algorithms combining 2 search strategies × 4 cost functions:

| Solver | Strategy | Cost Function | Avg Guesses |
|--------|----------|---------------|------------|
| bfs-opt | BFS | Constant | 3.82 |
| dfs-opt | DFS | Constant | 3.95 |
| ucs-constant | UCS | Constant | 3.81 |
| ucs-reduction | UCS | Reduction | 3.58 |
| ucs-partition | UCS | Partition | 3.55 |
| ucs-entropy | UCS | Entropy | 3.54 |
| astar-constant-log2 | A* | Constant + Log2 | 3.51 |
| astar-entropy-entropy | A* | Entropy + Entropy | **3.43** |

**BFS/DFS:** Explore all paths equally (unweighted). BFS breadth-first, DFS depth-first.

**UCS:** Weighted search. Lower-cost guesses are expanded first. Guarantees optimal solution given cost function.

**A\*:** UCS + heuristic. Prioritizes states with low `depth + heuristic_estimate`. Converges faster than UCS.

---



## Cost Functions

Cost represents how "good" a guess is. Lower cost paths are explored first in UCS/A*.

| Function | Formula | Range | When Low | Use Case |
|----------|---------|-------|----------|----------|
| **Constant** | 1.0 | 1.0 | Always | BFS/DFS baseline. All guesses equal priority. |
| **Reduction(recommended)** | 1.0 + (after/before) | [1.0, 2.0] | Eliminates many words | UCS prefers aggressive filtering. Fast initial pruning. |
| **Partition** | 1.0 + (largest_partition/before) | [1.0, 2.0] | Partitions balanced | UCS avoids large clusters. Reduces worst-case remaining. |
| **Entropy** | 2.0 - (entropy/max_entropy) | [1.0, 2.0] | Maximizes info gain | A* achieves 3.43 avg guesses. Most informed. |

Where: `entropy = Σ P(pattern) × log2(partition_size)` over feedback patterns; `max_entropy = log2(total_words)`

---

## Heuristic Functions

Heuristics estimate remaining cost for A*. Used in priority: `depth + heuristic`.

| Function | Estimate | Range | Intuition | Bound |
|----------|----------|-------|-----------|-------|
| **Log2** | log2(remaining) | [0, 12.5] | Each guess halves search (best case) | Optimistic |
| **Partition** | log2(largest_partition) | [0, 12.5] | End in largest partition (worst case) | Tighter |
| **Entropy** | (entropy/max_entropy) × log2(remaining) | [0, 12.5] | Weight by actual info available | Tightest |

**Admissibility:** All satisfy h(state) ≤ true_cost_to_goal, guaranteeing A* optimality.

---

---


## Key Insights

**Information Theory:** Optimal Wordle solving maximizes information gain per guess. Entropy-based cost functions implement this directly.

**Caching:** Feedback table achieves ~50% cache hit rate. Sparse sampling (200 connections per word) balances memory vs. performance.

**State Efficiency:** CompactState hashability enables visited set pruning, preventing redundant work.

**Heuristic Quality:** Better heuristics (entropy) reduce nodes explored by 70% vs. log2.

**Frontier Management:** A* with good heuristic keeps frontier small (peak ~1,234 states vs. BFS ~4,521).

---
