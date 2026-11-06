"""Slide 3.3: which earlier word resolves an ambiguous word? Attention of heads 6.12 (from the ambiguous word)
and 8.8 (from the last token), with resolving and neutral words.

Run from the repo root: .venv/bin/python demos/ambiguity.py
"""
import sys
sys.path.insert(0, ".")
import torch
from llm_helpers import load, encode, BASE

model = load(BASE)
tok = model.tok
HEADS = [(6, 12), (8, 8)]

SENTENCES = [
    ("With his {} over his shoulder, Tom walked down to the bank to", " bank",
     ["fishing rod", "paycheck", "backpack", "guitar"]),
    ("After the long {}, Tom picked up the bat and", " bat", ["baseball practice", "night in the cave", "day at work"]),
    ("Sitting at his {}, Tom reached for the mouse and", " mouse", ["computer", "desk", "table"]),
    ("With his {} over his shoulder, Tom walked along the noisy, crowded street, past the old church and the market, "
     "and finally down to the bank to", " bank", ["fishing rod", "paycheck"]),
]


@torch.no_grad()
def pattern(text, amb):
    ids = encode(model, text)
    toks = [tok.decode(i) for i in ids[0].tolist()]
    att = torch.stack(model(ids, output_attentions=True).attentions)[:, 0].float().cpu()
    p = model(ids).logits[0, -1].float().softmax(-1)
    a = max(i for i, t in enumerate(toks) if t == amb)
    print(f"\n{text!r}")
    print("  next:", [(tok.decode(i), round(v, 2)) for v, i in zip(*[x.tolist() for x in p.topk(5)])])
    for (l, h), q, label in [(HEADS[0], a, "from" + amb), (HEADS[1], len(toks) - 1, "from last")]:
        w = att[l, h, q, : q + 1].tolist()
        top = sorted(range(len(w)), key=lambda k: -w[k])[:4]
        print(f"  {l}.{h} {label}:", ", ".join(f"{toks[k]!r} {w[k]:.0%}" for k in top))


for template, amb, fills in SENTENCES:
    for f in fills:
        pattern(template.format(f), amb)
