"""Slide figures for Lecture 2. Numbers from lectures/02_lecture_plan.md, 2.4.

Run:  python lectures/figures/make_lecture2_figures.py
Sized for the object area of the "Title, Bullets & Object" layout (860 x 716 pt -> 8.6 x 7.16 in).
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).parent

fig, ax = plt.subplots(figsize=(8.6, 7.16), dpi=200)
labels, vals = ["Whole list\n(46 lines)", "lookup(year)\n(one row)"], [16, 40]
ax.bar(labels, vals, color=["#999999", "#7B2FF7"], width=0.55)
for i, v in enumerate(vals):
    ax.text(i, v + 0.8, f"{v} of 40", ha="center", fontsize=22, color="#222")
ax.set_ylim(0, 45)
ax.set_yticks([])
ax.tick_params(axis="x", length=0, labelsize=20, colors="#222")
for s in ["top", "right", "left"]:
    ax.spines[s].set_visible(False)
ax.set_title("OLMo 2 1B: names a laureate of the right year", fontsize=18, loc="left", color="#222", pad=14)
fig.text(0.02, 0.02, "Nobel Prize in Physics, 1915–1960, 40 years with a prize", fontsize=13, color="#666")
fig.tight_layout(rect=(0, 0.04, 1, 1))
fig.savefig(HERE / "nobel_bars.png")
