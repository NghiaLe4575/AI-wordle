# import json
# import matplotlib.pyplot as plt

# # Load JSON
# with open("score_results.json", "r") as f:
#     data = json.load(f)

# # Sort branches numerically
# branches = sorted(int(b) for b in data.keys())

# # Solver list
# solvers = list(next(iter(data.values())).keys())

# # Build time series per solver
# solver_times = {
#     solver: [data[str(b)][solver]["avg_time"] for b in branches]
#     for solver in solvers
# }

# # Plot
# plt.figure(figsize=(14, 8))

# # Distinct markers and line styles
# markers = ['o', 's', '^', 'D', 'v', '*', 'x', '+', 'p']
# linestyles = ['-', '--', '-.', ':', '-', '--', '-.', ':', '-']
# colors = plt.cm.tab10.colors  # 10 distinct colors

# for i, solver in enumerate(solvers):
#     plt.plot(branches, solver_times[solver], 
#              marker=markers[i % len(markers)], 
#              linestyle=linestyles[i % len(linestyles)],
#              color=colors[i % len(colors)],
#              label=solver, linewidth=3, markersize=8)

# plt.xlabel("Max Branch", fontsize=16)
# plt.ylabel("Average Time per Solve (seconds)", fontsize=16)
# plt.title("Average Solving Time vs Max Branch", fontsize=18)
# plt.xticks(branches, fontsize=14)
# plt.yticks(fontsize=14)
# plt.grid(True, linestyle="--", alpha=0.5)
# plt.legend(ncol=2, fontsize=12)
# plt.tight_layout()

# # Zoom y-axis VERY tight to see all lines clearly
# all_times = [t for times in solver_times.values() for t in times]
# y_min, y_max = min(all_times), max(all_times)
# y_margin = (y_max - y_min) * 0.05  # Only 5% margin for super zoomed view
# plt.ylim(y_min - y_margin, y_max + y_margin)

# # Save the figure
# plt.savefig("avg_time_vs_max_branch_super_zoom.png", dpi=300)
# print("Figure saved as avg_time_vs_max_branch_super_zoom.png")




# import json
# import matplotlib.pyplot as plt

# # Load JSON data
# with open("score_results.json", "r") as f:
#     data = json.load(f)

# # Sort branches numerically
# branches = sorted(int(b) for b in data.keys())

# # Solver list
# solvers = list(next(iter(data.values())).keys())

# # Build series for avg_generated per solver
# solver_generated = {
#     solver: [data[str(b)][solver]["avg_generated"] for b in branches]
#     for solver in solvers
# }

# # Plot
# plt.figure(figsize=(14, 8))

# # Colors and markers
# markers = ['o', 's', '^', 'D', 'v', '*', 'x', '+', 'p']
# colors = plt.cm.tab10.colors

# for i, solver in enumerate(solvers):
#     plt.plot(branches, solver_generated[solver],
#              marker=markers[i % len(markers)],
#              color=colors[i % len(colors)],
#              linewidth=3, markersize=8,
#              label=solver)

# plt.xlabel("Max Branch", fontsize=16)
# plt.ylabel("Average Generated Nodes", fontsize=16)
# plt.title("Average Generated Nodes vs Max Branch", fontsize=18)
# plt.xticks(branches)
# plt.yticks(fontsize=14)
# plt.grid(True, linestyle="--", alpha=0.5)
# plt.legend(fontsize=12, ncol=2)

# # Scale y-axis to show lines clearly
# all_generated = [val for vals in solver_generated.values() for val in vals]
# y_min, y_max = min(all_generated), max(all_generated)
# y_margin = (y_max - y_min) * 0.05
# plt.ylim(y_min - y_margin, y_max + y_margin)

# plt.tight_layout()
# plt.savefig("avg_generated_vs_max_branch.png", dpi=300)
# print("Figure saved as avg_generated_vs_max_branch.png")

# import json
# import matplotlib.pyplot as plt

# # Load JSON data from file
# with open("frequency.json", "r") as f:
#     data = json.load(f)

# # Extract solvers and their avg_guesses
# solvers = data["2"].keys()
# avg_guesses_data = {solver: data["2"][solver]["avg_guesses"] for solver in solvers}

# # Plot histogram for each solver
# plt.figure(figsize=(12, 6))
# for solver, guesses in avg_guesses_data.items():
#     plt.hist(guesses, bins=range(min(guesses), max(guesses)+2), alpha=0.5, label=solver, edgecolor='black')

# plt.xlabel("Number of Guesses")
# plt.ylabel("Frequency")
# plt.title("Frequency of Avg Guesses for Each Solver")
# plt.legend()
# plt.grid(axis='y', linestyle='--', alpha=0.7)

# # Save figure
# plt.savefig("avg_guesses_frequency.png", dpi=300)
# plt.show()


import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# Load your JSON file
with open('score_results.json', 'r') as f:  # replace with your filename
    data = json.load(f)

# Prepare data for heatmap
# Rows: problem sizes, Columns: solvers
heatmap_data = {}
for problem_size, solvers in data.items():
    heatmap_data[problem_size] = {solver: metrics['avg_expanded'] for solver, metrics in solvers.items()}

# Convert to DataFrame for seaborn
df = pd.DataFrame.from_dict(heatmap_data, orient='index')
df = df.sort_index()  # sort by problem size

# Plot heatmap
plt.figure(figsize=(12, 6))
sns.heatmap(df, annot=True, fmt=".2f", cmap='viridis', linewidths=.5)
plt.title('Average Expanded Nodes Heatmap')
plt.xlabel('Solvers')
plt.ylabel('Problem Size')
plt.tight_layout()

# Save image
plt.savefig('avg_expanded_heatmap.png', dpi=300)
plt.show()
