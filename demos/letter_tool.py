"""Exercise 1, Part C: a letter counter for Qwen, with a hand-written system prompt (reference solution).

The model can't count letters: it sees tokens, not letters. count_letter() counts them, and the system prompt
describes the call in the format that tool_loop.by_hand() parses. The bonus adds the optional ignore_case.

Run from the repo root: .venv/bin/python demos/letter_tool.py
"""
import re
import sys

sys.path.insert(0, "demos")
sys.path.insert(0, ".")
from llm_helpers import ask
from tool_loop import by_hand


def count_letter(word, letter, ignore_case=False):
    if ignore_case:
        word, letter = word.lower(), letter.lower()
    return word.count(letter)


SYSTEM = ('You can use a letter counter. To count how often a letter occurs in a word, write '
          '<tool_call>{"name": "count_letter", "arguments": {"word": "...", "letter": "..."}}</tool_call> and stop. '
          'The count will be given to you.')
BONUS = SYSTEM + (' It counts exact matches, so "A" and "a" are different letters. '
                  'To count upper and lower case together, add "ignore_case": true to the arguments.')

LONG = "Donaudampfschifffahrtsgesellschaftskapitän"
QUESTIONS = [  # (question, correct number or None if no call is needed)
    (f"How many times does the letter s occur in the word {LONG}?", 5),
    (f"How many f's are in {LONG}?", 5),
    ("How many e's are in Rindfleischetikettierungsüberwachungsaufgabenübertragungsgesetz?", 9),
    ("How many r's are in the word strawberry?", 3),
    ("How many a's, upper or lower case, are in the word Aachen?", 2),
    ("What is the capital of Australia?", None),
]

if __name__ == "__main__":
    print("Without the tool:", ask(QUESTIONS[0][0], max_tokens=60))
    for name, system in [("basic", SYSTEM), ("bonus", BONUS)]:
      for run in range(2):
        for q, correct in QUESTIONS:
            doc = by_hand(q, system, {"count_letter": count_letter})
            model_part = doc.split("<|im_start|>assistant\n", 1)[1]  # skip the example call in the system prompt
            calls = re.findall(r"<tool_call>(.*?)</tool_call>", model_part, re.S)
            answer = doc.rsplit("<|im_start|>assistant\n", 1)[1].strip()
            ok = (not calls and "Canberra" in answer) if correct is None else str(correct) in answer
            print(f"{name} run {run} {'ok' if ok else 'NO'} {q[:60]:60} calls={calls} answer={answer[:70]!r}")
