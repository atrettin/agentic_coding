"""The retrieval demos (slides 6.5, 6.6, B.8) on an API model, which returns no attention weights.

Run from the repo root: .venv/bin/python demos/api_retrieval.py [list] [recall] [memory] [needle]
(all three without arguments). Requests: list 56, recall 40, memory 4, needle 175; SAIA allows 400 per hour.
"""
import random
import sys
from types import SimpleNamespace

sys.path.insert(0, ".")
sys.path.insert(0, "demos")
sys.argv += ["--distractors", "20"]  # read by lost_in_middle on import
from transformers import AutoTokenizer

from context_list import WINNERS, question
from lost_in_middle import DISTRACTORS, NEEDLES, haystack
from llm_helpers import ALIGNED, api, client

MODEL = "meta-llama-3.1-8b-instruct"
SYSTEM = "You are a helpful assistant."  # without a system prompt, Llama 3.1 starts its answers with an invented tool call


def ask(user, max_tokens=60):
    r = api(client().chat.completions, model=MODEL, max_tokens=max_tokens, temperature=0,
            messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}])
    return r.choices[0].message.content, r.usage.prompt_tokens


def surname(winner):
    return winner.split(" and ")[0].split(",")[0].split()[-1]  # of the first laureate


def nobel_prompt(winners, year):
    lines = "\n".join(f"{y}: {w}" for y, w in winners.items())
    return f"Nobel Prize winners in Physics:\n{lines}\n\n{question(year)}"


def list_task():
    for lo, hi in [(1945, 1960), (1915, 1960)]:
        winners = {y: w for y, w in WINNERS.items() if lo <= y <= hi}
        hits, misses = 0, []
        for year, w in winners.items():
            if w == "not awarded":
                continue
            answer, n = ask(nobel_prompt(winners, year))
            ok = surname(w) in answer
            hits += ok
            if not ok:
                misses.append(f"{year}: {answer[:80]!r}")
        print(f"List {lo}–{hi} ({n} prompt tokens): {hits} of {sum(w != 'not awarded' for w in winners.values())} right")
        for m in misses:
            print("  miss", m)


def recall_task():
    """Which years does the model get wrong from memory alone? Those make the best "put it into the context" demos."""
    for year, w in WINNERS.items():
        if w != "not awarded":
            answer = ask(question(year))[0]
            if surname(w) not in answer:
                print(f"{year} ({w}): {answer[:120]!r}")


def memory_task():
    fake = "Heinrich Vogel"
    for year, lo, hi in [(1951, 1945, 1960), (1921, 1915, 1930)]:
        winners = {y: w for y, w in WINNERS.items() if lo <= y <= hi}
        print(f"{year}, no list:  ", ask(question(year))[0])
        print(f"{year}, fake list:", ask(nobel_prompt({**winners, year: fake}, year))[0])


def needle_task():
    counter = SimpleNamespace(tok=AutoTokenizer.from_pretrained(ALIGNED))  # OLMo's tokenizer, to size the filler
    lengths, depths, needles = [1000, 4000, 16000, 32000], [0.0, 0.25, 0.5, 0.75, 1.0], NEEDLES[:5]
    for q in ["What is the code word for the lab door?", "Which word opens the laboratory?"]:
        print(f"\n{q!r}: right answers out of {len(needles)} (distractor answers in brackets), {len(DISTRACTORS)} distractors")
        print(f"{'tokens':>8}" + "".join(f"{d:>10.0%}" for d in depths))
        for n in lengths:
            row = []
            for depth in depths:
                right = wrong = 0
                for i, needle in enumerate(needles):
                    try:
                        answer, used = ask(f"{haystack(counter, n, depth, needle, random.Random(i))}\n\n{q}", max_tokens=20)
                    except Exception as e:  # e.g. the prompt is longer than the server allows
                        print(f"{n:>8}  failed: {e}")
                        return
                    right += needle in answer.lower()
                    wrong += any(w in answer.lower() for _, w in DISTRACTORS)
                row.append(f"{right} ({wrong})")
            print(f"{used:>8}" + "".join(f"{r:>10}" for r in row))
        if q.startswith("What"):
            lengths = lengths[1:]  # the paraphrase run skips the shortest length to save requests


if __name__ == "__main__":
    tasks = [a for a in sys.argv[1:] if a in ("list", "recall", "memory", "needle")] or ["list", "recall", "memory", "needle"]
    for t in tasks:
        print(f"===== {t} ({MODEL})")
        globals()[f"{t}_task"]()
