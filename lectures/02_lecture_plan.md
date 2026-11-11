# Lecture 2: From tool calls to coding agents — slide plan

Working draft, iteration 1.
Each slide gives what the slide shows (pictures and examples, not text to read), and speaker notes.
`[DEMO]` means a switch to the live notebook (`lectures/02_tools_and_agents.ipynb`; the calculator behind Part 1 is `demos/olmo_calc.py`, the Nobel Prize database behind Part 2 is `demos/nobel_lookup.py`) or, in Parts 6–7, to OpenCode.

**Where the students should be at the end**

1. A tool call is text in an agreed format. The program around the model parses it, runs the tool, and puts the result into the context.
2. When you ask a model a question, the harness wraps it in additional context: tool descriptions, instructions, tool results. A model that wasn't trained for harnesses works only as long as the question fits the wrapping; a model whose chat template and training include tool calls decides by itself when to call, however the question is phrased.
3. A small model with the one relevant fact in its context beats the same model with a long list. Tools are a way to put little, relevant information into the context.
4. A harness is a program that puts information into a model's context and acts on its structured output. An agent is a model in a harness loop, with tools, until the task is done.
5. They can write an `AGENTS.md`, a skill and a custom agent for OpenCode, and say what each one costs in context.
6. They work in this order: plan, iterate on the plan, implement. They keep one session per self-contained feature, keep the code in independent modules that fit into the context, and compact or restart when old tool outputs are no longer relevant. They can explain why with Lecture 1: irrelevant and long context degrades the answers.

**Structure and rough minutes (total ≈ 89, target 90; the rest is buffer for questions and demos)**

| Part | Topic | Min |
| --- | --- | --- |
| 0 | Recap: the chat is a document; who puts information there? | 3 |
| 1 | A calculator for the 1B model | 10 |
| 2 | A database for the 1B model | 10 |
| 3 | Where the 1B model breaks, and why: the templates | 10 |
| 4 | A model trained for tools: Qwen, native tool calling | 8 |
| 5 | The harness, and what an agent is | 5 |
| 6 | OpenCode: custom tools, AGENTS.md, skills, agents | 25 |
| 7 | Working with an agent: plan, scope, modules, compact | 15 |
| 8 | Wrap-up | 3 |

---

## Part 0 — Recap (3 min)

### 0.1 The chat is one document
- The Lecture 1 chat template again (OLMo: `<|user|>`, `<|assistant|>`), with the user's question and the model's answer in one block of text.

> Notes: The model only ever continues a document. The "conversation" is something the program around it writes. Today, that program writes more than our messages into the document.

### 0.2 Who puts the information there?
- Lecture 1, slide 6.7 again: the context window, with information coming from you (pasting) or from a program (a search, a file read, a calculator).
- The cliffhanger: 1234567 × 7654321. The 1B model, asked for the number only: "The answer is 6000000000." Correct: 9449772114007.

> Notes: Two problems from last time. The model can't compute: each digit is a guess. And it doesn't know facts it rarely saw (1951 Nobel Prize). In Lecture 1 we fixed the second by pasting a list by hand. Today a program does both, first for the same small model.

---

## Part 1 — A calculator for the 1B model (10 min)

Concepts used: chat template, sampling, context. New: tool call, tool result, the harness.

### 1.1 The deal `[DEMO]`
- The document, in full: `<|user|>` "You can use a calculator. To compute something, write only calc(EXPRESSION), for example calc(2 + 3), and nothing else. You will get the result back." + the question "What is 1234567 * 7654321?" + `<|assistant|>`.

> Notes: Nothing special: one paragraph of text that describes a format, in front of the user's question, in the same user turn. The harness writes the whole document, so nothing is hidden. Why in the user turn and not in a system prompt: Part 3.

### 1.2 The model writes the call `[DEMO]`
- The model's output: `calc(1234567 * 7654321)<|endoftext|>`. P(`calc`) as the first token: 91%.

> Notes: The model didn't multiply. It wrote text in the agreed format, because that is the most likely continuation of a document that offers a calculator and asks for a product. This is a Lecture 1 continuation, nothing else. `<|endoftext|>` is written by the model too: it ends its turn, generation stops, and the harness takes over.

### 1.3 The harness does the work `[DEMO]`
- The harness finds `calc(...)`, computes 9449772114007, and writes a new user turn: "Answer the question in a full sentence using the following information: 1234567 * 7654321 = 9449772114007", the question again, and `<|assistant|>`.
- The model continues: "The calculation of 1234567 * 7654321 equals 9449772114007." Correct.
- Slide picture: the document, growing in four colours: the user, the harness, the model, the tool.
- `demos/olmo_calc.py`: 20 of 20 calls, 19 of 20 answers right (the cliffhanger, 12 × 13, a sum, 17 random five-digit products). The miss copies a 10-digit result wrongly.

> Notes: The answer is correct because the model copies a number from its context, which it does well (Lecture 1, 6.5); but copying is sampled too, so not perfectly. Point at the colours: the model wrote only the green parts. Everything else is the program. The harness also added a second instruction ("…in a full sentence…"): without it, the model's answers drift.

### 1.4 Never run the model's text unchecked
- The two lines in `calc()`: a check that the expression has only digits and `+ - * / ( )`, then `eval`.

> Notes: The tool call is text the model sampled. If our tool were "run this Python", a wrong or manipulated sample would run on our machine (Lecture 1, B.8: the model follows the context, including text written to mislead it). Coding agents run shell commands, so they ask for permission. This comes back in Part 6.

---

## Part 2 — A database for the 1B model (10 min)

Concepts used: retrieval from the context (Lecture 1, 6.5–6.6), the harness from Part 1. New: a tool that puts facts into the context.

### 2.1 Last time: the whole list `[DEMO]`
- The local 1B model with the list 1915–1960 (46 lines) in the context, and the question "Who won the Nobel Prize in Physics in {year}?". It names a laureate of that year in 16 of 40 years. Most misses name a neighbouring line.
- 1947 with the list: "…awarded to Wolfgang Pauli … his discovery of the neutrino" (Pauli was 1945; correct: Edward Appleton).

> Notes: Reminder of the problem. Even a short list is too much for this model: attention picks the wrong line, and the reasons are invented, because they aren't in the list. (16 of 40 counts any laureate's surname in the free answer; Lecture 1's 14 of 40 counted only the first token; same picture.)

### 2.2 A database and a tool
- The table (SQLite, from `demos/nobel_physics.csv`, the official Nobel Prize data): `year | laureates | motivation`, three rows on the slide.
- The tool: `lookup(YEAR)` runs `SELECT * FROM physics WHERE year = ?` and returns one row.

> Notes: Structured data: the program finds the row exactly. The model only has to write the year.

### 2.3 The harness wraps your question `[DEMO]`
- `with_tool("Who won the Nobel Prize in Physics in 1947?", show=True)`: the same harness as Part 1, as one function. Yellow: the one line the user typed. Grey: the harness (the tool description in front, "Answer the question in a full sentence using the following information:" after the call). Green: the model (`lookup(1947)<|endoftext|>`, then the answer). Blue: the database row.
- The answer: "Edward V. Appleton won the Nobel Prize in Physics in 1947 for his investigations of the physics of the upper atmosphere especially for the discovery of the so-called Appleton layer."

> Notes: The message of this slide: when you ask a model a question, your question is wrapped in additional context by the harness. The user typed one line; the model saw a document three times as long. The reason is right now, because it is in the context. With only "Database row:" in front of the row, the answers are bare names ("Edward Victor Appleton").

### 2.4 Does it help? `[DEMO]`
- All 40 years (1915–1960): a call with the right year in 40 of 40; the answer names a laureate and gives the database's reason in 40 of 40 (some shortened: "Max Planck … for his discovery of energy quanta"). Whole list: a laureate in 16 of 40, reasons invented.
- Slide picture: two bars, 16/40 and 40/40.

> Notes: Same model, same question. The only change: the context holds the one relevant row instead of 46 lines. That's the U-curve lesson put to use: give the model what it needs, and no more.

---

## Part 3 — Where the 1B model breaks (10 min)

Concepts used: prompting as conditioning, the chat template. New: why a model has to be trained for tools.

### 3.1 One more sentence breaks it `[DEMO]`
- The user adds "Answer in one sentence." to the 1947 question. The harness treats it exactly the same way. No call; the model answers from memory: "…awarded to William Henry Brattain for his discovery of the transistor." (Brattain: 1956.)
- The calculator with the cliffhanger's wording, "…? Answer with the number only.": no call, "The answer is 69314720."
- Why: the probability of the call as the first token.

  | Instruction in | Question ends with | P(`calc`), 1234567 × 7654321 | P(`lookup`), 1947 | Calls (lookup, of 40 years) |
  | --- | --- | --- | --- | --- |
  | system turn | "…?" | 36% (then writes a result itself: `calc(…) = 8000000000`) | 0.16% | 0 |
  | user turn | "…?" | 91% | 96% | 40 |
  | user turn | "…? Answer with the number only." | 7% | — | — |
  | user turn | "…? Answer in one sentence." | 0.11% | 0.00% | 0 |
  | user turn | "…? {Use the calculator / Look up the data} first, then answer in a full sentence." | 22% | 0.31% | 0 |

- OLMo's chat template has no tool role either: a `tool` message is dropped without an error.

> Notes: Lecture 1's main point again: the model writes what is likely, given the document. "Answer with the number only." and "Answer in one sentence." ask for an answer right away and win over the tool; so does a chained instruction ("first this, then that"). The model card's chat format has no system block, so the model mostly ignores a system turn. Ask the students first which document will work; most expect the system prompt. Every harness is built for the models it runs; the 2.4 result holds only as long as the user asks in the way the harness expects.

### 3.2 Questions the tools can't answer `[DEMO]`
- The harness wraps every question in the tool instruction, whatever the user asks:

  | Tool | Question | Call | Tool says | Answer |
  | --- | --- | --- | --- | --- |
  | calc | What is the capital of Australia? | `calc( Canberra )` | error: only numbers … | "The capital of Australia is Canberra, which is an error: only numbers and + - * / ( ) are allowed." |
  | calc | How many r's are in the word strawberry? | `calc(5)` | 5 | "The word strawberry contains the letters r and s exactly 5 times." |
  | lookup | What is 12 * 13? | `lookup(12)` | No entry for 12. | "There is no entry for 12 in the Nobel Prize in Physics database, so I cannot provide the answer…" |
  | lookup | Who discovered the neutron? | `lookup(1931)` | 1931: not awarded | "The neutron was not awarded the Nobel Prize in Physics in 1931." |
  | lookup | Who won the Nobel Prize in Chemistry in 1911? | `lookup(1911)` | 1911 (Physics): Wilhelm Wien | "Wilhelm Wien won the Nobel Prize in Chemistry in 1911…" (correct: Marie Curie) |
  | both | Write a haiku about neutrinos. | none | — | a haiku |

> Notes: The instruction says "use the tool", so the model uses it, even for a capital, a product or a letter count. What happens next depends on the tool's reply: the model falls back on its own knowledge (Canberra, with the error message glued on), gives up (12 × 13), or turns a wrong result into a confident answer (strawberry, Chemistry 1911). A coding agent has the same problem at a larger scale: every task comes wrapped in tool descriptions, and a model that isn't good at deciding when *not* to use them makes up work.

### 3.3 Why: the documents a model was trained on
- Slide, left and right: the same exchange in OLMo's template (`<|user|>\nWhat is 12 * 13?\n<|assistant|>\n156<|endoftext|>`) and in Qwen's (`<|im_start|>user\nWhat is 12 * 13?<|im_end|>\n<|im_start|>assistant\n156<|im_end|>`). Different tokens, same shape.
- Below: Qwen's template with a tool. A system block "# Tools … You are provided with function signatures within `<tools></tools>` XML tags: `<tools>`{the schema}`</tools>` … return a json object … within `<tool_call></tool_call>` XML tags", then the user turn.

> Notes: OLMo reliably writes chat answers because it was trained on many `<|user|>`/`<|assistant|>` documents: autocompleting one is what it does best. It was never trained on documents with tool descriptions, calls and results, so a tool call is only likely when our document happens to make it likely, and any extra sentence tips the balance. Models like Qwen have a tool block in their template and were trained on many documents of exactly this shape. Prediction for Part 4: Qwen won't break on the sentences from 3.1.

---

## Part 4 — A model trained for tools (8 min)

### 4.1 Tool calling by hand, in Qwen's format `[DEMO]`
- The API model can't multiply either: 9449999999999.
- A hand-written system prompt: "You can use a calculator. To use it, write `<tool_call>{"name": "calc", "arguments": {"expression": "..."}}</tool_call>` and stop. The result will be given to you." We send the whole document to the raw `/completions` endpoint and tell the server to stop at `</tool_call>`.
- The model writes `<tool_call>{"name": "calc", "arguments": {"expression": "1234567 * 7654321"}}</tool_call>`; the server stops. The script appends `<tool_response>9449772114007</tool_response>` in a user turn; the model answers "9,449,772,114,007".

> Notes: The same loop as Part 1, in the format this model knows. The system prompt works here: Qwen was trained with system prompts. The stop string is model output too: the model writes `</tool_call>`, and the server stops there.

### 4.2 The `tools` field `[DEMO]`
- In the notebook: the calculator as a JSON schema (name, description, parameters), sent with `/chat/completions`.
- The response has no text, only `tool_calls: [{"name": "calc", "arguments": "{\"expression\": \"1234567 * 7654321\"}"}]`. We append a message with role `tool`.

- `show_template(messages)`: the document the server builds. It is the document from 4.1: the tool block from 3.3, then `<tool_call>`, then `<tool_response>` in a user turn.

> Notes: This is how every real program does it. It looks like a different mechanism. It isn't: the server writes the tool description into the system prompt and parses the `<tool_call>` text out of the answer. Our hand-written version worked because we used nearly the same format.

### 4.3 The loop
- The ten lines of `agent()` on the slide: call the model; if it made tool calls, run each, append the results, and repeat; else return the answer.

> Notes: This loop is the core of every coding agent. Keep this slide in mind for Part 6.

### 4.4 A trained model decides by itself `[DEMO]`
- The API model with `lookup(year)`:
  - "Who won … in 1953?" → one call, `{"year": 1953}`, answer: Frits Zernike, "for his demonstration of the phase contrast method…".
  - "… in 1951 and 1952, and for what?" → two calls in one turn, both answered from the rows.
  - "What is the capital of Australia?" → no call, "Canberra".
  - "Who won the Nobel Prize in Chemistry in 1911?" → no call, "Marie Curie" from memory (contrast with 3.2). In another run it refused: "None of the available functions can provide information about the Nobel Prize in Chemistry in 1911." Too careful, but it still doesn't misuse the tool.

> Notes: Contrast with 3.2. This model was trained on tool use in this format, so we only describe the tool, and it calls when a tool helps, and not when it doesn't.

### 4.5 It isn't confused by other instructions `[DEMO]`
- The sentences that broke the 1B model in 3.1, with both tools (`calc` and `lookup`) offered:

  | Question | Call | Answer |
  | --- | --- | --- |
  | "What is 1234567 * 7654321? Answer with the number only." | `calc` | "9449772114007" |
  | "Who won … in 1947? Answer in one sentence." | `lookup(1947)` | "Edward V. Appleton won the Nobel Prize in Physics in 1947 for his investigations of the physics of the upper atmosphere…" |
  | "Who won … in 1947? Look up the data first, then answer in a full sentence." | `lookup(1947)` | the same sentence |

- Same in two runs (`demos/tool_loop.py`, `robustness()`).

> Notes: Every call is made, and with the right tool. The extra instruction shapes the answer (a bare number, one sentence), not the decision to call. This is what tool training buys: the decision to call doesn't depend on how the user phrases the question.

---

## Part 5 — The harness, and what an agent is (5 min)

### 5.1 The harness
- One sentence: "A harness is a program that puts information into a model's context and acts on structured output from the model."
- Diagram: the loop. User → harness builds the context (system prompt, tool descriptions, messages, results) → model → text or tool call → harness runs the tool → result into the context → model → … → answer.

> Notes: Everything we wrote today was a harness: `with_calc()`, `with_tool()`, `agent()`. The model is the same function from Lecture 1. All the behaviour we built came from the program around it.

### 5.2 What an agent is
- "Agent = model + harness + tools, in a loop until the task is done."
- What the harness decides: which tools exist, what goes into the context and when, which calls need permission, when to stop.
- Diagram (`lectures/figures/loop_agent.mmd`): the loop until the task is done, with the four decisions where they happen: the context box (what goes in, step limit), the model (sees only the tools that exist), "Harness: permitted?" between the call and the tool (a refusal goes back into the context).

> Notes: "Agent" is no new kind of model. A coding agent is the loop from 4.3 with tools that read files, edit files and run commands. The quality depends on the model *and* on what the harness puts into the context.

---

## Part 6 — OpenCode (25 min)

Model: Qwen3.8 27B on SAIA (`qwen3.8-27b`).

### 6.1 A coding agent is a harness `[DEMO]`
- Live OpenCode session on a small demo repo: "Add a test for function X and run it." Expand the tool calls: `read`, `grep`, `edit`, `bash`, with their outputs.
- The same loop diagram as 5.1, now with file and terminal tools.

> Notes: Point at the tool calls as they happen: each output lands in the context. The agent reads before it edits because its system prompt tells it to. It asks before running a command because the harness has a permission rule.

### 6.2 Your own tools `[DEMO]`
- Question left over from Part 4: how do we give OpenCode our calculator? With a custom tool: a file in `.opencode/tools/` (or `~/.config/opencode/tools/` for all projects). The tool can run a script in any language. Our `calc()` from 1.4 as a Python script, and its definition (after the docs' "add two numbers" example; files in `demos/opencode_tools/`):

  ```python
  # .opencode/tools/calc.py
  import re
  import sys

  expression = sys.argv[1]
  if not re.fullmatch(r"[\d\s+\-*/().]+", expression):  # only arithmetic: never eval text from a model unchecked
      print("error: only numbers and + - * / ( ) are allowed")
  else:
      print(eval(expression))
  ```

  ```ts
  // .opencode/tools/calc.ts
  import { tool } from "@opencode-ai/plugin"
  import path from "path"

  export default tool({
    description: "Evaluate an arithmetic expression exactly.",
    args: {
      expression: tool.schema.string().describe("The expression, e.g. 1234567 * 7654321"),
    },
    async execute(args, context) {
      const script = path.join(context.worktree, ".opencode/tools/calc.py")
      const result = await Bun.$`python3 ${script} ${args.expression}`.text()
      return result.trim()
    },
  })
  ```

- Build step: arrows from the definition to our `TOOLS` schema from 4.2. `description` → `description`; `args` → `parameters`; the file name → `name` (the tool is called `calc`); `execute` → our `calc()`, which the harness runs when the model writes a call.
- Demo, without any instruction to use the tool: "What is (1234567 * 7654321 - 98765) / 4321?" → `calc {"expression": "(1234567 * 7654321 - 98765) / 4321"}` → `2186940989.4103217`. "What is 2 + 2?" → no call, "4".
- Build step: the same question with `calc.ts` removed. The agent runs `python3 -c "print((1234567 * 7654321 - 98765) / 4321)"` with `bash`.

> Notes: Nothing new: OpenCode turns `description` and `args` into the same JSON schema we wrote by hand, puts it into the tool block of the template, and runs `execute` when the model writes a call. The model decides by itself, as in 4.4: it calls for the hard expression and not for 2 + 2, and "Answer with the number only." (3.1) doesn't stop the call. Without our tool, it finds a calculator of its own: Python through the shell. That works, but it is the 1.4 problem: the model writes a command and the harness runs it. A narrow tool runs only arithmetic, and a shell command needs a permission rule. Each custom tool also adds its description to every request (next slide). OpenCode installs `@opencode-ai/plugin` into `.opencode/` by itself; Python only needs to be on the path. Tested with OpenCode 1.18.27 and Qwen3.8 27B: 10 of 10 calls for five questions with large numbers (two runs each), including a word problem; no call for 2 + 2 (2 runs); `bash` with Python without the tool (2 of 2).

### 6.3 What is in the context before you type
- Stacked bar of the context at the start of a session: system prompt, tool descriptions (built-in and custom), `AGENTS.md`, the list of skills (names and descriptions), then your message.

> Notes: Everything in this bar is in every request of the session. That is the budget we'll spend in the next three slides.

### 6.4 `AGENTS.md`
- What it is: a Markdown file in the project root that OpenCode puts into the context of every session. (A global one lives at `~/.config/opencode/AGENTS.md`. OpenCode reads `CLAUDE.md` if there is no `AGENTS.md`.)
- `/init`: the agent scans the repo and writes or improves the file. Commit it.
- Example on the slide, short:
  ```markdown
  # Project
  Simulation of X. Python 3.12, numpy, pytest.

  ## Commands
  - Tests: `.venv/bin/pytest -q`
  - Lint: `.venv/bin/ruff check .`

  ## Conventions
  - Units: SI everywhere; document units in docstrings.
  - Never edit `data/raw/`; it is the only copy of the measurements.
  - New physics goes into `model/`, plotting into `plots/`.
  ```
- What goes in: commands, conventions, decisions, traps the agent can't see from the code. What stays out: what the agent can read itself (the file tree, the code), long documentation, wishes ("write clean code").

> Notes: Every line costs context in every request, and every irrelevant line is the "irrelevant context" from Lecture 1, 6.6. Rule of thumb: a line belongs here if the agent got it wrong without it. Grow the file from mistakes, don't write it up front.

### 6.5 Skills
- A skill is a folder with a `SKILL.md`: `.opencode/skills/<name>/SKILL.md` (project) or `~/.config/opencode/skills/<name>/SKILL.md` (global).
- Example:
  ```markdown
  ---
  name: new-experiment
  description: Sets up a new numerical experiment in experiments/. Use when the user asks for a new run, scan or parameter study.
  ---
  1. Copy experiments/_template/ to experiments/<date>_<short-name>/.
  2. Write the parameters into config.toml, never into the script.
  3. Run it with `make run EXP=<dir>` and check that results/ is not empty.
  ```
- How it works: only the `name` and `description` of each skill are in the context. When a task fits, the agent calls the `skill` tool, and the full text is loaded then.
- Real example: the `add-paper` skill used to prepare this course (finds a paper on arXiv, converts it, handles failures).

> Notes: The trick is context economy. Ten skills cost ten lines until one is needed. The `description` decides *when* the skill is loaded, so it must say when to use it, not only what it does. Same mechanism as tools: a description in the context, the content on demand.

### 6.6 Agents
- Built-in: `build` (default, all tools) and `plan` (no file edits); switch with **Tab**. Subagents: `explore` (read-only search) and `general`. The primary agent starts a subagent through a tool call, or you write `@explore …`.
- A subagent gets a fresh context and returns only its final report. Slide picture: the main context with one short report in it, next to the subagent's long context full of file reads.
- A custom agent: a Markdown file in `.opencode/agents/<name>.md`; the body is its system prompt.
  ```markdown
  ---
  description: Reviews a diff for bugs and missing tests. Use after an implementation step.
  mode: subagent
  permission:
    edit: deny
    bash: ask
  ---
  You review code changes. Read the diff with `git diff`. For each problem,
  give the file, the line, what goes wrong and a test that would catch it.
  Do not fix anything.
  ```
- Real example: the `paper-scout` agent, which reads one paper in full and reports only the relevant locations (`mode: subagent`, edit and bash denied).

> Notes: Two reasons for an agent of your own. A fixed role with fixed permissions: a reviewer that can't edit can't "fix" the tests to pass. And context: the long reading happens in the subagent's context, and only the result lands in yours. That is the U-curve lesson applied to the agent itself. Hidden built-in agents show the same idea: OpenCode's compaction and title are agents too, each a model call with its own prompt.

---

## Part 7 — Working with an agent (15 min)

### 7.1 Plan first `[DEMO]`
- Tab to `plan`: "Add X. Make a plan." The agent reads the code and writes a plan, without editing files.
- Iterate: correct the plan in two or three messages (a wrong file, a missing test, a simpler approach).
- Tab to `build`: "Implement the plan."

> Notes: A plan is cheap to change and code is expensive. The plan also lands in the context as a short, relevant summary of what to do, instead of a long trail of trial and error. Caveat: `plan` blocks file edits, but by default it follows your normal permission rules for shell commands, so a command could still change files. Set `bash: ask` for `plan` if that matters.

### 7.2 One session, one feature
- Slide picture: the 16/40 vs 40/40 bars from 2.4 and the U-curve from Lecture 1, 6.6, next to a long session's context: three finished features' worth of file reads and test output.

> Notes: Here is why. Each old tool output is still in the context, in every request. It is irrelevant to the next feature, and Lecture 1 showed what irrelevant context does: attention spreads, the relevant piece gets lost, and answers get worse. Practical rule: one session per self-contained feature. Start a new one with `/new`.

### 7.3 Code the agent can hold
- Slide picture: a grid of tiles, each tile a file or chunk of code, and a frame (the context window) that holds only a few tiles. Build steps:
  1. A small project: all tiles fit into the frame. The agent sees everything it needs.
  2. The project grows: the grid is much larger than the frame. The agent reads the tiles for its task into the frame.
  3. Spaghetti: lines connect each tile to tiles all over the grid. The tile being edited calls code outside the frame. In the outside tiles, a ghost tile with a made-up name: `parse_config(strict=True)`, a function that doesn't exist.
  4. Modules: the same grid in a few boxes with one narrow interface each. One box fits into the frame, together with the interfaces of its neighbours. The agent can safely change everything inside the box.

> Notes: What isn't in the context doesn't exist for the model, and it fills the gap with what is likely (Lecture 1, 6.1: `tolerance_mode`). In a small project that rarely happens, because everything fits. In a large, tangled project, every change touches code the agent hasn't read, so it invents function calls and breaks callers it never saw, and each fix tangles the code more. That's why the old rules of software design matter more with agents, not less: independent modules with small interfaces are pieces of code an agent can hold in its context. Same lesson as 7.2, for the code instead of the session: one session per feature works only if a feature fits into one module.

### 7.4 Compaction
- `/compact` (or `ctrl+x c`): the hidden compaction agent writes a summary of the session, and the summary replaces the history.
- OpenCode compacts automatically when the context is full (`compaction.auto`, on by default). `compaction.prune` removes old tool outputs (off by default).
- Compact when the past is no longer needed in detail (after the exploration, before the implementation). Start a new session when the next task is unrelated.

> Notes: Compaction is lossy: the summary is a model's choice of what matters. Exact error messages and file contents are gone. Compact on purpose at a good point, not automatically in the middle of a debugging session.

### 7.5 Trust, but verify
- Checklist: run the tests, read every diff, watch for invented APIs (Lecture 1, 6.1: `tolerance_mode`), commit after each working step (so that `/undo` and git can take it back).

> Notes: The model is indifferent to truth (Lecture 1, 6.4). Tests and compilers are not. Put the test command into `AGENTS.md` so the agent runs it itself.

---

## Part 8 — Wrap-up (3 min)

### 8.1 Two lectures in one picture
- The loop diagram from 5.1, each part labelled with its lecture: the model samples tokens (L1); the context conditions it, and less, relevant context works better (L1, L2); the harness turns text into actions and results into context (L2).
- The working rules: plan → iterate → implement; one session per feature; modules small enough to fit into the context; compact when the past is irrelevant; verify with tests.

---

## Backup

### B.1 A small change in wording `[DEMO]`
- "Who won the Nobel Prize in Physics in {year}, and for what?" with the instruction in the user turn: 38 of 40 calls. In 1917 and 1927 the model answers from memory ("…awarded to Wilhelm Conrad Ro…").

> Notes: The working document from 2.3 is fragile: three extra words cost two calls. A small model needs its document exactly right; this is why tool calling is trained into larger models.

### B.2 The call can be wrong too `[DEMO]`
- "Who won … ten years after the transistor prize?" → the API model calls `lookup(1957)` and answers Yang and Lee, "ten years after the 1947 Nobel Prize … awarded to the inventors of the transistor". The transistor prize was 1956 (the invention was 1947), so the right year is 1966.
- Stable in two runs. Don't use "… the year after Albert Einstein won it?": at temperature 0 it gave `lookup(1922)` (right) in one run and `lookup(1923)` in the other (the 1921 prize was awarded in 1922).

> Notes: The tool is exact, but the arguments are sampled text, and here they come from the model's memory. A wrong fact before the call gives a confident, well-sourced, wrong answer. In a coding agent: the agent runs the right test command on the wrong file.

### B.3 Forcing a call `[DEMO]`
- `tool_choice="required"`: the API makes the model call a tool. Asked "What is the capital of Australia?" with only the calculator, the model calls `calc("2 + 2")`.

> Notes: A harness doesn't have to trust the model to decide: APIs can force a call, and grammars can constrain the output to valid JSON. But forcing is blunt. The model has to call something, so it calls something.

### B.4 MCP
- One slide: the Model Context Protocol is a standard way to offer tools to any harness. An MCP server is a program with tools; OpenCode is configured to call it.

---

## Exercises (homework slot, ~90 min)

| Exercise | Deepens | Status |
| --- | --- | --- |
| 1 (Tasks 6–8, bonus) A letter counter for Qwen: students write the system prompt around a given `count_letter()`; bonus: an optional `ignore_case` (`exercises/01_llms_and_tools.ipynb`, reference `demos/letter_tool.py`) | Part 4.1 | Built |
| 2 OpenCode on `exercises/weather_station/`: fix a bug from its symptom (plan, then build), `AGENTS.md` with conventions, the same feature with and without it, a custom tool `data_summary`, a skill `monthly-report`, a subagent `convention-reviewer` (`exercises/02_opencode.md`, reference `demos/weather_solution/`) | Parts 6, 7 | Built |
| – Build a tool loop: complete the harness (parse the call, run it, append the result) | Parts 1, 4 | Idea (`demos/olmo_calc.py` and `demos/tool_loop.py` are solutions) |
| – Context window trap: questions about a long text, then with a search tool | Part 2 | Idea |
| – Give OpenCode the Nobel database: a custom tool `lookup` that runs a Python script with the year | Parts 2, 6 | Idea |

## Open questions

- **Demo repo for Parts 6–7:** `exercises/weather_station/` (Exercise 2) could serve; it has tests, a bug and a feature to add, but no `calc` tool yet. Otherwise not built yet. Needs tests, a helper module, one small feature to add, and `.opencode/tools/` with `calc.py` and `calc.ts` from `demos/opencode_tools/` (6.2). The script path uses `context.worktree` (the git root), so the demo repo must be its own git repository.
- **OpenCode model:** Qwen3.8 27B "works in practice" but this plan's demos are not tested with it yet; `qwen3-coder-next` is untested. Check the rate limits (10 requests per 10 s) during a live session.
- **Course plan:** the Lecture 2 table in the course plan has a "context window" segment (a truncated document). This plan replaces it with the Nobel database (Part 2); update the course plan if this holds.
- **Cut candidates (if time gets short):**
  - 3.2: show only the database cases. The calculator cases teach the same thing. Saves ~1–2 min.
  - Merge 7.4 into 7.2 as one bullet ("compact or `/new`"). Saves ~1 min.
