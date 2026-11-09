"""Slide figures for Lecture 1, made from the saved outputs of 01_what_an_llm_does.ipynb.

Run the notebook first, then:  python lectures/figures/make_lecture1_figures.py
Writes PNGs next to this script, sized for the object area of the "Title, Bullets & Object"
layout (860 x 716 pt -> 8.6 x 7.16 in).
"""
import base64, json, re
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
NB = json.loads((HERE.parent / "01_what_an_llm_does.ipynb").read_text())


def outputs(source_snippet):
    """Outputs of the first code cell whose source contains the snippet."""
    for c in NB["cells"]:
        if c["cell_type"] == "code" and source_snippet in "".join(c["source"]):
            return c["outputs"]
    raise KeyError(source_snippet)


def show_top_rows(source_snippet):
    """Parse show_top's text output: '  8.5%  ████   '190'' -> [('190', 8.5), ...]."""
    text = "".join("".join(o.get("text", "")) for o in outputs(source_snippet))
    return [(tok, float(p)) for p, tok in re.findall(r"^\s*([\d.]+)%.*?'(.*)'\s*$", text, re.M)]


def bars(fname, prompt, data, note):
    toks = [t for t, _ in data][::-1]
    p = [v for _, v in data][::-1]
    fig, ax = plt.subplots(figsize=(8.6, 7.16), dpi=200)
    ax.barh(range(len(p)), p, color="#7B2FF7", height=0.62)
    ax.set_yticks(range(len(p)), [repr(t) for t in toks], fontfamily="Menlo", fontsize=17)
    for i, v in enumerate(p):
        ax.text(v + max(p) * 0.015, i, f"{v:.1f}%", va="center", fontsize=16, color="#333")
    ax.set_xlim(0, max(p) * 1.18)
    ax.set_xticks([])
    for s in ["top", "right", "bottom"]:
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color("#999")
    ax.tick_params(axis="y", length=0, colors="#222")
    ax.set_title(prompt, fontsize=17, loc="left", fontfamily="Menlo", color="#222", pad=14)
    fig.text(0.02, 0.02, note, fontsize=13, color="#666")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(HERE / fname)
    plt.close(fig)


# 0.1: ChatGPT active users in millions, from the table "ChatGPT active users 2022 to 2026 (mm)",
# https://www.businessofapps.com/data/chatgpt-statistics/ (copied by hand, 9 Nov 2026; the site blocks scripts).
CHATGPT_USERS = [("2022-12", 1), ("2023-01", 57), ("2023-02", 100), ("2023-09", 150), ("2024-08", 200),
                 ("2024-10", 250), ("2024-12", 300), ("2025-03", 500), ("2025-09", 700), ("2025-10", 800),
                 ("2026-02", 900), ("2026-08", 1000), ("2026-10", 1200)]


def users_chart(fname):
    """Wide line chart for the bottom of the 'November 2022' slide (1720 x 420 pt)."""
    from datetime import date
    d = [date(int(m[:4]), int(m[5:]), 15) for m, _ in CHATGPT_USERS]
    u = [v for _, v in CHATGPT_USERS]
    fig, ax = plt.subplots(figsize=(17.2, 4.2), dpi=200)
    ax.plot(d, u, color="#7B2FF7", lw=3, marker="o", ms=8, zorder=3)
    ax.axvline(date(2022, 11, 30), color="#999", lw=1.5, ls="--")
    ax.text(date(2022, 12, 20), 1150, "Launch, 30 Nov 2022", fontsize=15, color="#666", va="top")
    for i, txt, off, ha in [(2, "100M by Feb 2023", (-6, 22), "left"), (7, "500M", (-10, 10), "right"),
                            (12, "1.2 billion", (-12, 6), "right")]:
        ax.annotate(txt, (d[i], u[i]), xytext=off, textcoords="offset points",
                    ha=ha, va="bottom", fontsize=17, color="#222")
    ax.set_xticks([date(y, 1, 1) for y in range(2023, 2027)], [str(y) for y in range(2023, 2027)])
    ax.set_ylim(0, 1300)
    ax.set_yticks([0, 400, 800, 1200], ["0", "400M", "800M", "1.2B"])
    ax.set_xlim(date(2022, 10, 1), date(2026, 12, 31))
    ax.grid(axis="y", color="#e5e5e5", lw=1)
    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#999")
    ax.tick_params(length=0, labelsize=15, colors="#444")
    ax.set_title("ChatGPT active users", fontsize=19, loc="left", color="#222")
    ax.text(1, 1.02, "Source: businessofapps.com/data/chatgpt-statistics", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=12, color="#888")
    fig.tight_layout()
    fig.savefig(HERE / fname)
    plt.close(fig)


if __name__ == "__main__":
    users_chart("chatgpt_users.png")
    tum = show_top_rows('show_top(base, "The Technical University of Munich was founded in ")')
    aus = show_top_rows('show_top(base, "The capital of Australia is")')
    assert len(tum) == 10 and len(aus) == 10, (tum, aus)
    bars("chart_tum.png", '"…Munich was founded in "', tum,
         "Next-token probabilities, OLMo 2 1B base, top 10. Correct: 1868.")
    bars("chart_aus.png", '"The capital of Australia is"', aus,
         "Next-token probabilities, OLMo 2 1B base, top 10.")

    # 6.3: the notebook's own heatmap of attention on "1951"
    png = next(o["data"]["image/png"] for o in outputs("share of attention on the year") if "image/png" in o.get("data", {}))
    (HERE / "heatmap_1951.png").write_bytes(base64.b64decode(png))
    print("wrote chatgpt_users.png, chart_tum.png, chart_aus.png, heatmap_1951.png")
