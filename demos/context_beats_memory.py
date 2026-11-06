"""Backup slide B.8: the context beats memory.

The list from context_list.py, with one entry replaced by a made-up name. Does the model copy the
fake name, even for a year it "knows" well (1921, Einstein)?

Run from the repo root: .venv/bin/python demos/context_beats_memory.py
"""
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "demos")
from context_list import WINNERS, check, prompt, question
from llm_helpers import ALIGNED, chat, chat_prompt, load, next_token_probs

FAKE = "Heinrich Vogel"

if __name__ == "__main__":
    model = load(ALIGNED)
    for year, lo, hi in [(1951, 1945, 1960), (1921, 1915, 1930)]:
        true_first = " " + WINNERS[year].split()[0]
        ids = {name: model.tok(name, add_special_tokens=False).input_ids[0] for name in [true_first, " " + FAKE.split()[0]]}
        no_list = next_token_probs(model, chat_prompt(model.tok, question(year)) + f"The Nobel Prize in Physics in {year} was awarded to")
        print(f"--- {year}: true {WINNERS[year]!r}, fake {FAKE!r}")
        print("  without list:", "  ".join(f"{n!r} {no_list[i]:.1%}" for n, i in ids.items()))
        for label, override in [("true list", {}), ("fake list", {year: FAKE})]:
            winners = {y: override.get(y, w) for y, w in WINNERS.items() if lo <= y <= hi}
            text, lines = prompt(model, year, winners)
            p = next_token_probs(model, text)
            first, right, _, (l, h, m), _ = check(model, year, winners)
            print(f"  {label}:", "  ".join(f"{n!r} {p[i]:.1%}" for n, i in ids.items()),
                  f"  head {l}.{h}: {m:.0%} on the {year} line")
            print("    greedy:", chat(model, f"Nobel Prize winners in Physics:\n{lines}\n\n{question(year)}", max_new_tokens=40))
