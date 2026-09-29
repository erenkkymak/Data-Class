"""plot_p1.py - one log-log chart: rows (x) vs time (y), one line per query. Reads p1_measurements.csv."""
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rows = list(csv.DictReader(open("p1_measurements.csv", encoding="utf-8")))
series = {
    "Q1 commission (SUM)": ("Q1 total commission (linear scan)", "#2a78d6"),
    "Q2 naive (compare)": ("Q2 naive: every order vs every other", "#d6452a"),
    "Q3 grouping (GROUP BY)": ("Q3 GROUP BY (customer, day)", "#1f9e6e"),
}
fig, ax = plt.subplots(figsize=(8, 5.2), dpi=150)
for key, (label, color) in series.items():
    for run, style in (("warm", "-"), ("cold", ":")):
        pts = [(int(r["n"]), float(r["Time (median, s)"])) for r in rows if r["Method"] == key and r["Run"] == run]
        if not pts:
            continue
        xs, ys = zip(*pts)
        ax.plot(xs, ys, style, marker="o" if run == "warm" else None, color=color, lw=2 if run == "warm" else 1.2,
                label=f"{label} ({run})")

# Q2 extrapolation (not run) from the measured doubling pattern
import math
w = [(int(r["n"]), float(r["Time (median, s)"])) for r in rows if r["Method"] == "Q2 naive (compare)" and r["Run"] == "warm"]
k = math.log(w[-1][1] / w[0][1]) / math.log(w[-1][0] / w[0][0])
ex = [w[-1][0], 100_000, 1_000_000]
ax.plot(ex, [w[-1][1] * (n / w[-1][0]) ** k for n in ex], "--", color="#d6452a", alpha=.6,
        label=f"Q2 extrapolated, not run (time ~ n^{k:.2f})")

ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlabel("rows (n)"); ax.set_ylabel("time, median (s)")
ax.set_title("P1 — how time grows with data (log–log, seed 42)")
ax.grid(True, which="both", alpha=.25)
ax.legend(fontsize=7.5, loc="upper left")
fig.tight_layout()
fig.savefig("p1_chart.png")
print("wrote p1_chart.png")
