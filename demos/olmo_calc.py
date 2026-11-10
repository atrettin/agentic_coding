"""Lecture 2: a calculator for the local 1B model, in the same document shape as the Nobel lookup.

The aligned model gets the tool description and the question in one user turn (in a system turn it is ignored),
writes calc(EXPRESSION), the harness evaluates it and returns the result with "Answer the question in a full
sentence using the following information:". Then the documents that break it: the cliffhanger's
"Answer with the number only." and the other instructions that break the lookup (nobel_lookup.py).

Run from the repo root: .venv/bin/python demos/olmo_calc.py
"""
import random
import re
import sys

sys.path.insert(0, ".")
from llm_helpers import ALIGNED, chat_prompt, complete, encode, load, next_token_probs
from nobel_lookup import ANSWER_WITH, turn
from tool_loop import calc

INSTRUCTION = ("You can use a calculator. To compute something, write only calc(EXPRESSION), for example calc(2 + 3), "
               "and nothing else. You will get the result back.")


def answer(model, doc, max_new_tokens=60):
    return complete(model, doc, max_new_tokens=max_new_tokens).split("<|endoftext|>")[0].strip()


def with_calc(model, user_question):
    """The harness: tool description + question in the user turn; run calc() if called; ask again with the result."""
    doc = "<|endoftext|>" + turn("user", INSTRUCTION + "\n\n" + user_question) + "<|assistant|>\n"
    reply = answer(model, doc)
    m = re.search(r"calc\(([^)]*)\)", reply)
    if not m:
        return reply, None, reply
    result = calc(m.group(1))
    doc += m.group(0) + "<|endoftext|>\n" + turn("user", f"{ANSWER_WITH}{m.group(1).strip()} = {result}\n\n{user_question}") + "<|assistant|>\n"
    return m.group(0), result, answer(model, doc)


if __name__ == "__main__":
    model = load(ALIGNED)
    q = "What is 1234567 * 7654321?"
    print("Without a tool:", repr(answer(model, chat_prompt(model.tok, q + " Answer with the number only."))))
    print("Correct:", 1234567 * 7654321, "\n")

    random.seed(0)
    questions = [q, "What is 12 * 13?", "What is 98765 + 43210?"] + \
                [f"What is {random.randint(1000, 99999)} * {random.randint(1000, 99999)}?" for _ in range(17)]
    hits = 0
    for uq in questions:
        call, result, final = with_calc(model, uq)
        ok = str(eval(uq[8:-1])) in final.replace(",", "")
        hits += ok
        print(f"{'ok' if ok else 'NO'} {uq:30} {call!r:28} {final[:80]!r}")
    print(f"{hits} of {len(questions)} right\n")

    calc_id = encode(model, "calc")[0, 0]
    variants = {
        "system turn":              turn("system", INSTRUCTION) + turn("user", q),
        "user turn":                turn("user", INSTRUCTION + "\n\n" + q),
        "user turn, number only":   turn("user", INSTRUCTION + "\n\n" + q + " Answer with the number only."),
        "user turn, one sentence":  turn("user", INSTRUCTION + "\n\n" + q + " Answer in one sentence."),
        "user turn, chained":       turn("user", INSTRUCTION + "\n\n" + q + " Use the calculator first, then answer in a full sentence."),
    }
    for name, head in variants.items():
        doc = "<|endoftext|>" + head + "<|assistant|>\n"
        print(f"{name:25} P('calc') = {next_token_probs(model, doc)[calc_id].item():7.2%}   {answer(model, doc, 25)!r}")

    print("\nQuestions the calculator can't answer:")
    for uq in ["What is the capital of Australia?", "Who won the Nobel Prize in Physics in 1951?",
               "How many r's are in the word strawberry?", "Write a haiku about neutrinos."]:
        print(f"{uq:45} {with_calc(model, uq)}")
