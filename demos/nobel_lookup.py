"""Lecture 2: a database tool for the local 1B model, against the whole list in the context.

The aligned model gets the question and a description of one tool, lookup(YEAR), both in the user turn.
The harness (this script) parses the call, queries a SQLite database, and puts the one matching row back
into the conversation. OLMo's chat template has no tool role, so the row comes back as a user turn.
For comparison, the same question with the whole list (as in Lecture 1, slide 6.5) in the context.
Both answers count as right when they name a laureate of that year (surname).

Run from the repo root: .venv/bin/python demos/nobel_lookup.py [first_year last_year]
"""
import csv
import os
import re
import sqlite3
import sys

sys.path.insert(0, ".")
from llm_helpers import ALIGNED, complete, load

db = sqlite3.connect(":memory:")
db.execute("CREATE TABLE physics (year INTEGER, laureates TEXT, motivation TEXT)")
with open(os.path.join(os.path.dirname(__file__), "nobel_physics.csv")) as f:
    db.executemany("INSERT INTO physics VALUES (?, ?, ?)", list(csv.reader(f))[1:])

INSTRUCTION = ("You can look up the Nobel Prize in Physics in a database. To look up a year, write only "
               "lookup(YEAR), for example lookup(1903), and nothing else. You will get the database row back.")


# The harness adds this when it returns the row. The 1B model can't follow a chained instruction in the question
# ("look up the data first, then answer in a full sentence": it answers from memory), but it follows this one.
ANSWER_WITH = "Answer the question in a full sentence using the following information: "


def question(year):
    return f"Who won the Nobel Prize in Physics in {year}?"


def lookup(year):
    """The tool. year is whatever the model wrote between the brackets (not always a year), or a number from the API."""
    row = db.execute("SELECT * FROM physics WHERE year = ?", (str(year).strip(),)).fetchone()
    return f"{row[0]} | {row[1]} | {row[2]}" if row else f"No entry for {year}."


def turn(role, text):
    return f"<|{role}|>\n{text}\n"


def with_tool(model, user_question):
    """The harness: wrap the user's question in the tool instruction, call the model, run the tool call
    if there is one, and call the model again with the result.
    The instruction goes into the user turn: in a system turn, the 1B model ignores it. An extra
    "Answer in one sentence." in the question makes it answer from memory instead of calling the tool."""
    doc = "<|endoftext|>" + turn("user", INSTRUCTION + "\n\n" + user_question) + "<|assistant|>\n"
    reply = complete(model, doc, max_new_tokens=60).split("<|endoftext|>")[0].strip()
    m = re.search(r"lookup\(([^)]*)\)", reply)
    if not m:
        return reply, None, reply  # no tool call: the reply is the answer
    result = lookup(m.group(1))
    doc += m.group(0) + "<|endoftext|>\n" + turn("user", f"{ANSWER_WITH}{result}\n\n{user_question}") + "<|assistant|>\n"
    return m.group(0), result, complete(model, doc, max_new_tokens=60).split("<|endoftext|>")[0].strip()


def surnames(laureates):
    return [name.split()[-1] for name in re.split(r", | and ", laureates)]


def with_list(model, user_question, years):
    rows = "\n".join(f"{y}: {db.execute('SELECT laureates FROM physics WHERE year = ?', (y,)).fetchone()[0]}" for y in years)
    doc = "<|endoftext|>" + turn("user", f"Nobel Prize winners in Physics:\n{rows}\n\n{user_question}") + "<|assistant|>\n"
    return complete(model, doc, max_new_tokens=60).split("<|endoftext|>")[0].strip()


if __name__ == "__main__":
    nums = [int(a) for a in sys.argv[1:] if a.isdigit()]
    lo, hi = nums if nums else (1915, 1960)
    years = range(lo, hi + 1)
    model = load(ALIGNED)
    calls = tool_hits = list_hits = n = 0
    for year in years:
        laureates = db.execute("SELECT laureates FROM physics WHERE year = ?", (year,)).fetchone()[0]
        if laureates == "not awarded":
            continue
        n += 1
        call, result, answer = with_tool(model, question(year))
        listed = with_list(model, question(year), years)
        ok_tool = any(s in answer for s in surnames(laureates))
        ok_list = any(s in listed for s in surnames(laureates))
        calls += call == f"lookup({year})"
        tool_hits += ok_tool
        list_hits += ok_list
        print(f"{year} call {call!r:18} tool {'ok' if ok_tool else 'NO'}  list {'ok' if ok_list else 'NO'}\n"
              f"     tool: {answer}\n     list: {listed}")
    print(f"\n{n} years: {calls} calls with the right year, tool {tool_hits} right, whole list {list_hits} right "
          "(right = names a laureate of that year)")
