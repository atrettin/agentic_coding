# Lecture 2: From tool calls to coding agents — slide plan

Working draft, iteration 1.
Each slide gives what the slide shows (pictures and examples, not text to read), and speaker notes.
`[DEMO]` means a switch to the live notebook (`lectures/02_tools_and_agents.ipynb`; the Nobel Prize database behind Part 2 is `demos/nobel_lookup.py`) or, in Parts 5–6, to OpenCode.

**Where the students should be at the end**

1. A tool call is text in an agreed format. The program around the model parses it, runs the tool, and puts the result into the context.
2. When you ask a model a question, the harness wraps it in additional context: tool descriptions, instructions, tool results. A model that wasn't trained for harnesses works only as long as the question fits the wrapping; a model trained on tool calls decides by itself when to call. A harness can also force a call.
3. A small model with the one relevant fact in its context beats the same model with a long list. Tools are a way to put little, relevant information into the context.
4. A harness is a program that puts information into a model's context and acts on its structured output. An agent is a model in a harness loop, with tools, until the task is done.
5. They can write an `AGENTS.md`, a skill and a custom agent for OpenCode, and say what each one costs in context.
6. They work in this order: plan, iterate on the plan, implement. They keep one session per self-contained feature and compact or restart when old tool outputs are no longer relevant. They can explain why with Lecture 1: irrelevant and long context degrades the answers.

**Structure and rough minutes (total ≈ 82, target 90; the rest is buffer for questions and demos)**

| Part | Topic | Min |
| --- | --- | --- |
| 0 | Recap: the chat is a document; who puts information there? | 4 |
| 1 | Tool calling by hand: the calculator | 12 |
| 2 | A database for the 1B model | 14 |
| 3 | Native tool calling | 9 |
| 4 | The harness, and what an agent is | 6 |
| 5 | OpenCode: AGENTS.md, skills, agents | 22 |
| 6 | Working with an agent: plan, scope, compact | 12 |
| 7 | Wrap-up | 3 |

---

## Part 0 — Recap (4 min)

### 0.1 The chat is one document
- The Lecture 1 chat template again (OLMo: `<|user|>`, `<|assistant|>`), with the user's question and the model's answer in one block of text.

> Notes: The model only ever continues a document. The "conversation" is something the program around it writes. Today, that program writes more than our messages into the document.

### 0.2 Who puts the information there?
- Lecture 1, slide 6.7 again: the context window, with information coming from you (pasting) or from a program (a search, a file read, a calculator).
- The cliffhanger: 1234567 × 7654321. The API model, asked for the number only: 9447500700000. Correct: 9449772114007.

> Notes: Two problems from last time. The model can't compute: each digit is a guess. And it doesn't know facts it rarely saw (1951 Nobel Prize). In Lecture 1 we fixed the second by pasting a list by hand. Today a program does both.

---

## Part 1 — Tool calling by hand (12 min)

Concepts used: chat template, sampling, context. New: tool call, tool result, the loop.

### 1.1 The deal `[DEMO]`
- The system prompt, in full: "You can use a calculator. To use it, write `<tool_call>{"name": "calc", "arguments": {"expression": "..."}}</tool_call>` and stop. The result will be given to you."
- The question: "What is 1234567 * 7654321?"

> Notes: Nothing special: one paragraph of text that describes a format. We send the whole document to the raw `/completions` endpoint, so nothing is hidden. We tell the server to stop at `</tool_call>`.

### 1.2 The model writes the call `[DEMO]`
- In the notebook, one cell per step: we send the document, the server stops at `</tool_call>`. The model's first output: `<tool_call>{"name": "calc", "arguments": {"expression": "1234567 * 7654321"}}`, then it stops.

> Notes: The model didn't multiply. It wrote text in the agreed format, because that is the most likely continuation of a document that offers a calculator and asks for a product. This is a Lecture 1 continuation, nothing else.

### 1.3 The script does the work `[DEMO]`
- The script parses the JSON, computes 9449772114007, and appends `<tool_response>9449772114007</tool_response>` and a new `<|im_start|>assistant`.
- The model continues: "9,449,772,114,007". Correct.
- Slide picture: the document, growing in three colours: written by us, written by the model, written by the script.

> Notes: The answer is correct because the model copies a number from its context, which it does well (Lecture 1, 6.5). Point at the colours: the model wrote only the green parts. Everything else is the program.

### 1.4 Never run the model's text unchecked
- The two lines in `calc()`: a check that the expression has only digits and `+ - * / ( )`, then `eval`.

> Notes: The tool call is text the model sampled. If our tool were "run this Python", a wrong or manipulated sample would run on our machine (Lecture 1, B.8: the model follows the context, including text written to mislead it). Coding agents run shell commands, so they ask for permission. This comes back in Part 5.

---

## Part 2 — A database for the 1B model (14 min)

Concepts used: retrieval from the context (Lecture 1, 6.5–6.6), the chat template, prompting as conditioning. New: a tool for a model with no tool training.

### 2.1 Last time: the whole list `[DEMO]`
- The local 1B model with the list 1915–1960 (46 lines) in the context, and the question "Who won the Nobel Prize in Physics in {year}?". It names a laureate of that year in 16 of 40 years. Most misses name a neighbouring line.
- 1947 with the list: "…awarded to Wolfgang Pauli … his discovery of the neutrino" (Pauli was 1945; correct: Edward Appleton).

> Notes: Reminder of the problem. Even a short list is too much for this model: attention picks the wrong line, and the reasons are invented, because they aren't in the list. (16 of 40 counts any laureate's surname in the free answer; Lecture 1's 14 of 40 counted only the first token; same picture.)

### 2.2 A database and a tool
- The table (SQLite, from `demos/nobel_physics.csv`, the official Nobel Prize data): `year | laureates | motivation`, three rows on the slide.
- The tool: `lookup(YEAR)` runs `SELECT * FROM physics WHERE year = ?` and returns one row.

> Notes: Structured data: the program finds the row exactly. The model only has to write the year. Ask: will the 1B model use it?

### 2.3 The harness wraps your question `[DEMO]`
- `with_tool("Who won the Nobel Prize in Physics in 1947?", show=True)`: the document in four colours. Yellow: the one line the user typed. Grey: the harness (the tool description in front, "Answer the question in a full sentence using the following information:" after the call). Green: the model (`lookup(1947)`, then the answer). Blue: the database row.
- The answer: "Edward V. Appleton won the Nobel Prize in Physics in 1947 for his investigations of the physics of the upper atmosphere especially for the discovery of the so-called Appleton layer."

> Notes: The message of this slide: when you ask a model a question, your question is wrapped in additional context by the harness. The user typed one line; the model saw a document three times as long. The harness did three jobs: it described the tool, it turned the model's text into a database query, and it added the second instruction ("…in a full sentence…") when it returned the row. The reason is right now, because it is in the context. With only "Database row:" in front of the row, the answers are bare names ("Edward Victor Appleton").

### 2.4 Does it help? `[DEMO]`
- All 40 years (1915–1960): a call with the right year in 40 of 40; the answer names a laureate and gives the database's reason in 40 of 40 (some shortened: "Max Planck … for his discovery of energy quanta"). Whole list: a laureate in 16 of 40, reasons invented.
- Slide picture: two bars, 16/40 and 40/40.

> Notes: Same model, same question. The only change: the context holds the one relevant row instead of 46 lines. That's the U-curve lesson put to use: give the model what it needs, and no more.

### 2.5 One more sentence breaks it `[DEMO]`
- The user adds "Answer in one sentence." to the same question. The harness treats it exactly the same way. No call; the model answers from memory: "…awarded to William Henry Brattain for his discovery of the transistor." (Brattain: 1956.)
- Why: the probability of `lookup` as the first token, for the 1947 question in five documents:

  | Instruction in | Question ends with | P(`lookup`) | Calls (of 40 years) |
  | --- | --- | --- | --- |
  | system turn | "…? Answer in one sentence." | 0.00% | 0 |
  | system turn | "…?" | 0.16% | 0 |
  | user turn | "…? Answer in one sentence." | 0.00% | 0 |
  | user turn | "…?" | 96% | 40 |
  | user turn | "…? Look up the data first, then answer in a full sentence." | 0.31% | 0 |

- OLMo's chat template has no tool role either: a `tool` message is dropped without an error.

> Notes: Lecture 1's main point again: the model writes what is likely, given the document. "Answer in one sentence." asks for an answer right away and wins over the tool; so does a chained instruction ("first this, then that"). The model card's chat format has no system block, so the model ignores a system turn. Ask the students first which document will work; most expect the system prompt. The reason: the 1B Instruct model was trained to follow instructions in a chat, not to work inside a harness. The API model in Part 3 was trained on exactly these documents (tool descriptions, calls, results), so it doesn't break this way. Every harness is built for the models it runs; the 2.4 result holds only as long as the user asks in the way the harness expects.

### 2.6 Questions the database can't answer `[DEMO]`
- The harness wraps every question in the tool instruction, whatever the user asks:

  | Question | Call | Database | Answer |
  | --- | --- | --- | --- |
  | What is the capital of Australia? | `lookup(Australia)` | No entry for Australia. | "The capital of Australia is Canberra." |
  | What is 12 * 13? | `lookup(12)` | No entry for 12. | "There is no entry for 12 in the Nobel Prize in Physics database, so I cannot provide the answer…" |
  | Who discovered the neutron? | `lookup(1931)` | 1931: not awarded | "The neutron was not awarded the Nobel Prize in Physics in 1931." |
  | Who won the Nobel Prize in Chemistry in 1911? | `lookup(1911)` | 1911 (Physics): Wilhelm Wien | "Wilhelm Wien won the Nobel Prize in Chemistry in 1911…" (correct: Marie Curie) |
  | Write a haiku about neutrinos. | none | — | a haiku |

> Notes: The instruction says "look up", so the model looks up, even for a capital or a product. What happens next depends on the database's reply: the model falls back on its own knowledge (Canberra), gives up (12 × 13), or turns the wrong row into a confident answer (Chemistry 1911). A coding agent has the same problem at a larger scale: every task comes wrapped in tool descriptions, and a model that isn't good at deciding when *not* to use them makes up work. Contrast in 3.4.

---

## Part 3 — Native tool calling (9 min)

### 3.1 The `tools` field `[DEMO]`
- In the notebook: the same calculator as a JSON schema (name, description, parameters), sent with `/chat/completions`.
- The response has no text, only `tool_calls: [{"name": "calc", "arguments": "{\"expression\": \"1234567 * 7654321\"}"}]`. We append a message with role `tool`.

> Notes: This is how every real program does it. It looks like a different mechanism. It isn't.

### 3.2 It is the same document `[DEMO]`
- `show_template(messages)`: the document the server builds. A system block "# Tools … `<tools>`{the schema}`</tools>` … return a json object … within `<tool_call></tool_call>` XML tags", then `<tool_call>`, then `<tool_response>` in a user turn.
- Side by side with our hand-written document from 1.3.

> Notes: The server writes the tool description into the system prompt and parses the `<tool_call>` text out of the answer. The model was trained on exactly this format, so it calls reliably. Our hand-written version worked because we used nearly the same format.

### 3.3 The loop
- The ten lines of `native()` on the slide: call the model; if it made tool calls, run each, append the results, and repeat; else return the answer.

> Notes: This loop is the core of every coding agent. Keep this slide in mind for Part 5.

### 3.4 A trained model decides by itself `[DEMO]`
- The API model with `lookup(year)`:
  - "Who won … in 1953?" → one call, `{"year": 1953}`, answer: Frits Zernike, "for his demonstration of the phase contrast method…".
  - "… in 1951 and 1952, and for what?" → two calls in one turn, both answered from the rows.
  - "What is the capital of Australia?" → no call, "Canberra".

- "Who won the Nobel Prize in Chemistry in 1911?" → no call, "Marie Curie" from memory (contrast with 2.6). In another run it refused: "None of the available functions can provide information about the Nobel Prize in Chemistry in 1911." Too careful, but it still doesn't misuse the tool. "Who wrote Faust?": "outside the scope of the available tools. However, … Goethe."

> Notes: Contrast with 2.5 and 2.6. This model was trained on tool use in this format, so we only describe the tool, and it calls when a tool helps, and not when it doesn't. The 1B model needed exactly the right question.

### 3.5 Forcing a call `[DEMO]`
- `tool_choice="required"`: the API makes the model call a tool. Asked "What is the capital of Australia?" with only the calculator, the model calls `calc("2 + 2")`.

> Notes: A harness doesn't have to trust the model to decide: APIs can force a call, and grammars can constrain the output to valid JSON. But forcing is blunt. The model has to call something, so it calls something.

---

## Part 4 — The harness, and what an agent is (6 min)

### 4.1 The harness
- One sentence: "A harness is a program that puts information into a model's context and acts on structured output from the model."
- Diagram: the loop. User → harness builds the context (system prompt, tool descriptions, messages, results) → model → text or tool call → harness runs the tool → result into the context → model → … → answer.

> Notes: Everything we wrote today was a harness: `by_hand()`, `with_tool()`, `native()`. The model is the same function from Lecture 1. All the behaviour we built came from the program around it.

### 4.2 What an agent is
- "Agent = model + harness + tools, in a loop until the task is done."
- What the harness decides: which tools exist, what goes into the context and when, which calls need permission, when to stop.

> Notes: "Agent" is no new kind of model. A coding agent is the loop from 3.4 with tools that read files, edit files and run commands. The quality depends on the model *and* on what the harness puts into the context.

---

## Part 5 — OpenCode (22 min)

Model: Qwen3.8 27B on SAIA (`qwen3.8-27b`).

### 5.1 A coding agent is a harness `[DEMO]`
- Live OpenCode session on a small demo repo: "Add a test for function X and run it." Expand the tool calls: `read`, `grep`, `edit`, `bash`, with their outputs.
- The same loop diagram as 4.1, now with file and terminal tools.

> Notes: Point at the tool calls as they happen: each output lands in the context. The agent reads before it edits because its system prompt tells it to. It asks before running a command because the harness has a permission rule.

### 5.2 What is in the context before you type
- Stacked bar of the context at the start of a session: system prompt, tool descriptions, `AGENTS.md`, the list of skills (names and descriptions), then your message.

> Notes: Everything in this bar is in every request of the session. That is the budget we'll spend in the next three slides.

### 5.3 `AGENTS.md`
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

### 5.4 Skills
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

### 5.5 Agents
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

## Part 6 — Working with an agent (12 min)

### 6.1 Plan first `[DEMO]`
- Tab to `plan`: "Add X. Make a plan." The agent reads the code and writes a plan, without editing files.
- Iterate: correct the plan in two or three messages (a wrong file, a missing test, a simpler approach).
- Tab to `build`: "Implement the plan."

> Notes: A plan is cheap to change and code is expensive. The plan also lands in the context as a short, relevant summary of what to do, instead of a long trail of trial and error. Caveat: `plan` blocks file edits, but by default it follows your normal permission rules for shell commands, so a command could still change files. Set `bash: ask` for `plan` if that matters.

### 6.2 One session, one feature
- Slide picture: the 16/40 vs 40/40 bars from 2.4 and the U-curve from Lecture 1, 6.6, next to a long session's context: three finished features' worth of file reads and test output.

> Notes: Here is why. Each old tool output is still in the context, in every request. It is irrelevant to the next feature, and Lecture 1 showed what irrelevant context does: attention spreads, the relevant piece gets lost, and answers get worse. Practical rule: one session per self-contained feature. Start a new one with `/new`.

### 6.3 Compaction
- `/compact` (or `ctrl+x c`): the hidden compaction agent writes a summary of the session, and the summary replaces the history.
- OpenCode compacts automatically when the context is full (`compaction.auto`, on by default). `compaction.prune` removes old tool outputs (off by default).
- Compact when the past is no longer needed in detail (after the exploration, before the implementation). Start a new session when the next task is unrelated.

> Notes: Compaction is lossy: the summary is a model's choice of what matters. Exact error messages and file contents are gone. Compact on purpose at a good point, not automatically in the middle of a debugging session.

### 6.4 Trust, but verify
- Checklist: run the tests, read every diff, watch for invented APIs (Lecture 1, 6.1: `tolerance_mode`), commit after each working step (so that `/undo` and git can take it back).

> Notes: The model is indifferent to truth (Lecture 1, 6.4). Tests and compilers are not. Put the test command into `AGENTS.md` so the agent runs it itself.

---

## Part 7 — Wrap-up (3 min)

### 7.1 Two lectures in one picture
- The loop diagram from 4.1, each part labelled with its lecture: the model samples tokens (L1); the context conditions it, and less, relevant context works better (L1, L2); the harness turns text into actions and results into context (L2).
- The working rules: plan → iterate → implement; one session per feature; compact when the past is irrelevant; verify with tests.

---

## Backup

### B.1 A small change in wording `[DEMO]`
- "Who won the Nobel Prize in Physics in {year}, and for what?" with the instruction in the user turn: 38 of 40 calls. In 1917 and 1927 the model answers from memory ("…awarded to Wilhelm Conrad Ro…").

> Notes: The working document from 2.3 is fragile: three extra words cost two calls. A small model needs its document exactly right; this is why tool calling is trained into larger models.

### B.2 The call can be wrong too `[DEMO]`
- "Who won … ten years after the transistor prize?" → the API model calls `lookup(1957)` and answers Yang and Lee, "ten years after the 1947 Nobel Prize … awarded to the inventors of the transistor". The transistor prize was 1956 (the invention was 1947), so the right year is 1966.
- Stable in two runs. Don't use "… the year after Albert Einstein won it?": at temperature 0 it gave `lookup(1922)` (right) in one run and `lookup(1923)` in the other (the 1921 prize was awarded in 1922).

> Notes: The tool is exact, but the arguments are sampled text, and here they come from the model's memory. A wrong fact before the call gives a confident, well-sourced, wrong answer. In a coding agent: the agent runs the right test command on the wrong file.

### B.3 MCP
- One slide: the Model Context Protocol is a standard way to offer tools to any harness. An MCP server is a program with tools; OpenCode is configured to call it.

---

## Exercises (homework slot, ~90 min)

| Exercise | Deepens | Status |
| --- | --- | --- |
| 6 Build a tool loop: complete the harness (parse the call, run it, append the result) | Parts 1, 3 | To build (`demos/tool_loop.py` is the solution) |
| 7 Context window trap: questions about a long text, then with a search tool | Part 2 | To build |
| 8 Agentic coding in our exercise repo: plan, iterate, implement one feature | Parts 5, 6 | To build |
| 9 Write an `AGENTS.md`, one skill and one review agent for the exercise repo; check that the skill is loaded when it should be | Part 5 | New idea |

## Open questions

- **Demo repo for Parts 5–6:** not built yet. Needs tests, a helper module, and one small feature to add.
- **OpenCode model:** Qwen3.8 27B "works in practice" but this plan's demos are not tested with it yet; `qwen3-coder-next` is untested. Check the rate limits (10 requests per 10 s) during a live session.
- **Course plan:** the Lecture 2 table in the course plan has a "context window" segment (a truncated document). This plan replaces it with the Nobel database (Part 2); update the course plan if this holds.
