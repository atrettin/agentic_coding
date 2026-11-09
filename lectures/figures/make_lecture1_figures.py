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


if __name__ == "__main__":
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
    print("wrote chart_tum.png, chart_aus.png, heatmap_1951.png")
