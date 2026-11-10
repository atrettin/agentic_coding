"""Plots of the monthly statistics."""
import datetime as dt

import matplotlib

matplotlib.use("Agg")  # write files, no window
import matplotlib.pyplot as plt


def plot_monthly(series, ylabel, path):
    """Line plot of monthly values, saved to path."""
    fig, ax = plt.subplots(figsize=(10, 4))
    for label, values in series.items():
        ax.plot([dt.date(y, m, 15) for y, m in values], list(values.values()), marker="o", label=label)
    ax.set_ylabel(ylabel)
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
