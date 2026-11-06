"""Slide 6.6 and the needle exercise: is a fact in the middle of a long context lost?

A made-up fact (the needle) is hidden at different depths of filler text of different lengths,
together with distractors of the same shape. We check whether the model's greedy answer
contains the needle, or a distractor instead.

Run from the repo root: .venv/bin/python demos/lost_in_middle.py [--distractors N] [--paraphrase]
"""
import random
import sys

sys.path.insert(0, ".")
from llm_helpers import ALIGNED, chat_prompt, complete, load

LENGTHS = [250, 500, 1000, 2000, 3500]  # filler tokens; OLMo 2 1B's context is 4096
DEPTHS = [0.0, 0.25, 0.5, 0.75, 1.0]  # where the needle sits: 0 = start, 1 = end
NEEDLES = ["pelican", "lantern", "violin", "marble", "cactus", "falcon", "anchor", "penguin", "saffron", "glacier"]
ROOMS = ["kitchen", "archive", "workshop", "library", "garage", "cellar", "office", "studio", "attic", "gym",
         "chapel", "boathouse", "greenhouse", "laundry", "pantry", "vault", "tower", "stable", "theatre", "clinic"]
WORDS = ["walnut", "harbor", "comet", "tulip", "copper", "meadow", "thunder", "basil", "ember", "orchid",
         "quartz", "willow", "badger", "canyon", "dolphin", "maple", "nectar", "pebble", "raven", "tundra"]
# --distractors N: how many same-shaped facts about other doors (default 4)
N_DISTRACTORS = int(sys.argv[sys.argv.index("--distractors") + 1]) if "--distractors" in sys.argv else 4
DISTRACTORS = list(zip(ROOMS, WORDS))[:N_DISTRACTORS]
# --paraphrase: the question shares no words with the needle, so the model can't just match tokens
QUESTION, ANSWER = (("Which word opens the laboratory?", "The word that opens the laboratory is") if "--paraphrase" in sys.argv
                    else ("What is the code word for the lab door?", "The code word for the lab door is"))

SUBJECTS = ["The baker", "A tourist", "The old teacher", "My neighbour", "The farmer", "A student", "The mayor", "Her cousin"]
VERBS = ["repaired", "painted", "sold", "found", "described", "photographed", "carried", "ignored"]
OBJECTS = ["a red bicycle", "the wooden fence", "an old map", "the broken clock", "a basket of apples", "the blue door", "a heavy suitcase"]
PLACES = ["near the river", "behind the station", "in the market square", "after lunch", "on Tuesday", "at the edge of town", "during the storm"]


def filler(model, n_tokens, rng):
    sentences, total = [], 0
    while total < n_tokens:
        s = f"{rng.choice(SUBJECTS)} {rng.choice(VERBS)} {rng.choice(OBJECTS)} {rng.choice(PLACES)}."
        sentences.append(s)
        total += len(model.tok(" " + s, add_special_tokens=False).input_ids)
    return sentences


def haystack(model, n_tokens, depth, needle, rng):
    sentences = filler(model, n_tokens, rng)
    for room, word in DISTRACTORS:  # same shape as the needle, at random places
        sentences.insert(rng.randrange(len(sentences) + 1), f"The code word for the {room} door is {word}.")
    sentences.insert(round(depth * len(sentences)), f"The code word for the lab door is {needle}.")
    return " ".join(sentences)


if __name__ == "__main__":
    model = load(ALIGNED)
    # greedy answer, checked for the word: the first token is often a quote mark, so its probability says little
    print(f"right answers out of {len(NEEDLES)} needles (distractor answers in brackets); rows: filler length, columns: depth\n")
    print(f"{'tokens':>8}" + "".join(f"{d:>10.0%}" for d in DEPTHS))
    for n in LENGTHS:
        row = []
        for depth in DEPTHS:
            right = wrong = 0
            for i, needle in enumerate(NEEDLES):
                rng = random.Random(i)  # the same filler for every depth, so only the position changes
                user = f"{haystack(model, n, depth, needle, rng)}\n\n{QUESTION}"
                answer = complete(model, chat_prompt(model.tok, user) + ANSWER, max_new_tokens=6)
                right += needle in answer
                wrong += any(w in answer for _, w in DISTRACTORS)
            row.append(f"{right} ({wrong})")
        print(f"{n:>8}" + "".join(f"{r:>10}" for r in row))
