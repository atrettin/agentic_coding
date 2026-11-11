"""Render Mermaid diagrams (*.mmd) to PNG with mermaidx: no browser, no Node.js.

Run:  .venv/bin/python lectures/figures/render_diagrams.py                # every .mmd in this folder
      .venv/bin/python lectures/figures/render_diagrams.py loop_agent.mmd # only these
Each PNG is written next to its .mmd, at 3x scale on white (as mmdc -s 3 -b white).

mermaidx measures and paints text with its bundled DejaVu Sans, so the font is set to that here; any other font
is measured in DejaVu but painted in another face, and the text no longer fits its box. Two limits:
- <small> in a label is ignored (the text keeps the normal size), and a css= rule squeezes text instead of
  shrinking it. Use a plain <br/> line instead.
- The PNGs differ from the ones made with mmdc (Helvetica, smaller subtitles), which the Lecture 2 slides use.
  To reproduce those exactly:  mmdc -i X.mmd -o X.png -c mermaid_config.json -s 3 -b white
  (with -p pointing puppeteer at an installed Chrome if mmdc can't find its own).
"""
import json
import sys
from pathlib import Path

import mermaidx

HERE = Path(__file__).parent
config = json.loads((HERE / "mermaid_config.json").read_text())
config["themeVariables"]["fontFamily"] = "DejaVu Sans"

for mmd in [HERE / name for name in sys.argv[1:]] or sorted(HERE.glob("*.mmd")):
    mermaidx.render(mmd.read_text(), config=config).save(str(mmd.with_suffix(".png")), scale=3, background="#ffffff")
    print("wrote", mmd.with_suffix(".png"))
