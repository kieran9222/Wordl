"""
Wordle simulator results visualizer.

Produces two PNG files in the same directory as this script:
  scatter.png  — histograms of guess distribution per starting word
  barchart.png — text lists of target words averaging 7 or 2 guesses
"""
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines

HERE = Path(__file__).parent

# ── Load & precompute ────────────────────────────────────────────────────────

df = pd.read_csv(HERE / "results.csv")

STARTING_WORDS = sorted(df["starting_word"].unique())
N = len(STARTING_WORDS)

word_stats = df.groupby("starting_word").agg(
    mean=("guesses", "mean"),
    win_pct=("guesses", lambda s: (s <= 6).mean() * 100),
).reindex(STARTING_WORDS)

target_avg = df.groupby("target_word")["guesses"].mean()

# ── Image 1: Histograms ──────────────────────────────────────────────────────

GUESS_VALUES = list(range(1, 8))
BAR_COLORS = ["steelblue"] * 6 + ["red"]

ncols = 5
nrows = int(np.ceil(N / ncols))
fig, axes = plt.subplots(nrows, ncols, figsize=(18, nrows * 3.5))
axes = axes.flatten()

for i, word in enumerate(STARTING_WORDS):
    ax = axes[i]
    sub = df[df["starting_word"] == word]["guesses"]
    avg = word_stats.loc[word, "mean"]
    win_pct = word_stats.loc[word, "win_pct"]

    counts = sub.value_counts().reindex(GUESS_VALUES, fill_value=0)
    ax.bar(GUESS_VALUES, counts.values, color=BAR_COLORS, width=0.8,
           edgecolor="white", linewidth=0.5)
    ax.axvline(avg, color="black", lw=2, zorder=5)

    ax.set_title(f"{word}  ({win_pct:.1f}% win)", fontsize=9, fontweight="bold")
    ax.set_xticks(GUESS_VALUES)
    ax.set_xticklabels(["1", "2", "3", "4", "5", "6", "7\n(loss)"], fontsize=7)
    ax.set_ylabel("Count", fontsize=7)
    ax.tick_params(axis="y", labelsize=7)
    ax.yaxis.grid(True, ls=":", alpha=0.4)
    ax.set_axisbelow(True)

    ax.text(avg + 0.08, ax.get_ylim()[1] * 0.95, f"avg {avg:.2f}",
            va="top", fontsize=7, color="black")

# hide any unused subplots
for j in range(N, len(axes)):
    axes[j].set_visible(False)

legend_handles = [
    mpatches.Patch(color="steelblue", label="Win (≤ 6 guesses)"),
    mpatches.Patch(color="red",       label="Loss (7 guesses)"),
    mlines.Line2D([], [], color="black", lw=2, label="Mean"),
]
fig.legend(handles=legend_handles, loc="lower center", ncol=3, fontsize=9,
           bbox_to_anchor=(0.5, -0.02))

fig.suptitle("Wordle Solver — Guess Distribution per Starting Word", fontsize=13, y=1.01)
plt.tight_layout()
fig.savefig(HERE / "scatter.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved scatter.png")

# ── Image 2: Word lists (avg rounds to 7 or 2) ──────────────────────────────

sevens = sorted(target_avg[target_avg.round() == 7].index.tolist())
twos   = sorted(target_avg[target_avg.round() == 2].index.tolist())

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, max(len(sevens), len(twos)) * 0.28 + 2))

for ax in (ax1, ax2):
    ax.axis("off")

ax1.set_title(f"Words averaging 7 guesses  ({len(sevens)} total)",
              color="#e74c3c", fontweight="bold", fontsize=11, pad=12)
ax2.set_title(f"Words averaging 2 guesses  ({len(twos)} total)",
              color="#27ae60", fontweight="bold", fontsize=11, pad=12)

ax1.text(0.5, 0.97, "\n".join(sevens) if sevens else "(none)",
         transform=ax1.transAxes, va="top", ha="center",
         fontsize=9, fontfamily="monospace", color="#e74c3c")
ax2.text(0.5, 0.97, "\n".join(twos) if twos else "(none)",
         transform=ax2.transAxes, va="top", ha="center",
         fontsize=9, fontfamily="monospace", color="#27ae60")

fig.suptitle("Target Words by Rounded Average Guess Count", fontsize=12, y=1.02)
plt.tight_layout()
fig.savefig(HERE / "barchart.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved barchart.png")
