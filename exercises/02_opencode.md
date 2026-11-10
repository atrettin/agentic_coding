# Exercise 2: Working with a coding agent

**Lecture segment:** Lecture 2, Parts 6–7 (OpenCode: custom tools, `AGENTS.md`, skills, agents; plan first).
**Goal:** you can let an agent fix a bug and add a feature in a small project, and you can explain what an `AGENTS.md`, a custom tool, a skill and a custom agent each put into the model's context.
**Model:** Qwen3.8 27B on the SAIA API, through OpenCode (needs `SAIA_API_KEY`).
**Time:** about 60 minutes.

The project is `weather_station/`: a small Python package that reads the daily data of a weather station (2023–2025) and computes monthly statistics. It works, it has tests, and it has a bug.

Every task ends with an **Observe** question. Write your answers into a file `answers.md` in the project, or on paper.
Reference solutions are in `demos/weather_solution/` in the course repository. Look only after you have tried.

---

## Setup (10 min)

These instructions are for macOS and Linux. On Windows, use WSL.

**1. Install OpenCode**

```bash
curl -fsSL https://opencode.ai/install | bash
# or, with Node.js installed:
npm install -g opencode-ai
```

Check with `opencode --version`.

**2. Connect OpenCode to SAIA.** Create the file `~/.config/opencode/opencode.json` (or add the `provider` and `model` entries to it, if it exists):

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "saia": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "SAIA",
      "options": {
        "baseURL": "https://chat-ai.academiccloud.de/v1",
        "apiKey": "{env:SAIA_API_KEY}"
      },
      "models": {
        "qwen3.8-27b": { "name": "Qwen 3.8 27B" }
      }
    }
  },
  "model": "saia/qwen3.8-27b"
}
```

`{env:SAIA_API_KEY}` reads your key from the environment variable, so the key is not written into the file.

**3. Copy the project out of the course repository.** OpenCode works in a project directory, and the project needs its own git repository. From the root of the course repository:

```bash
cp -R exercises/weather_station ~/weather_station
cd ~/weather_station
git init
git add -A
git commit -m "Initial version"
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pytest -q          # 5 passed
.venv/bin/python run.py      # the table of monthly values
```

**4. Start OpenCode** in the project directory: `opencode`. Type "Hello" to check that the model answers.

Useful keys and commands:

| | |
| --- | --- |
| **Tab** | Switch between the `build` agent (may edit) and the `plan` agent (may not edit files) |
| `/new` | Start a new session (an empty context) |
| `/undo` | Undo the last message and its file changes |
| `@name` | Call a subagent, or attach a file |
| `/exit` | Quit |

SAIA allows 10 requests per 10 seconds. An agent makes one request per step, so if you see a rate-limit error, wait a few seconds and type "continue".

---

## Task 1: Find and fix a bug (10 min)

Look at the output of `.venv/bin/python run.py`. In July 2025, the mean daily minimum temperature is −49.4 °C. That is impossible for Munich in July.

1. Press **Tab** to switch to the `plan` agent. Describe only the symptom, as you would to a colleague. Don't guess the cause:

   > When I run run.py, the mean daily minimum temperature for July 2025 comes out as −49.4 °C. That can't be right. Find out why and make a plan to fix it.

2. Read the plan. If something is missing (for example, a test that would have caught the bug), say so in one message.
3. Press **Tab** to switch to `build` and write "Implement the plan."
4. Check the result yourself: `git diff`, `.venv/bin/pytest -q`, `.venv/bin/python run.py`.
5. Commit: `git commit -am "Fix missing values in clean()"`.

**Observe:** Which tools did the agent call, and in which order? How did it find the cause without you telling it where to look? Look at the precipitation of March 2024 in the table before and after the fix: did the agent fix that too, and did it tell you?

---

## Task 2: Write an `AGENTS.md` (10 min)

`AGENTS.md` is put into the context of every session in this project. It is the place for what the agent can't find out by reading the code: conventions, decisions, commands, traps.

1. Start a new session (`/new`) and run `/init`. The agent reads the project and writes an `AGENTS.md`.
2. Read it. Delete every line that only repeats what the agent can see in the code anyway (the file list, what each function does). Every line costs context in every request.
3. Make sure the file contains these conventions, in your own words:
   - Tests run with `.venv/bin/pytest -q`.
   - `data/munich_daily.csv` is the only copy of the measurements: never edit it.
   - `-999` in the data means "missing"; analyses work on the data after `clean()`.
   - Every function gets a **numpy-style docstring** (sections `Parameters` and `Returns`) that gives the **unit** of every physical quantity, e.g. "Daily maximum temperature in °C".
   - Every new function in `weather/` gets a test in `tests/`, on small hand-made data, not on the CSV.
4. Commit: `git add AGENTS.md && git commit -m "Add AGENTS.md"`.

**Observe:** Which of the five conventions could the agent have guessed from the code? Look at the existing docstrings in `weather/stats.py`: which style would the agent copy without your `AGENTS.md`?

---

## Task 3: Does the agent follow the conventions? (10 min)

To see what `AGENTS.md` changes, do the same task twice: once in a copy of the project without it.

```bash
cp -R ~/weather_station ~/weather_station_no_agents
rm ~/weather_station_no_agents/AGENTS.md
```

In **each** of the two directories, start OpenCode and give the same task:

> Add a function heat_waves to weather/stats.py that finds the heat waves in the data: periods of at least 3 consecutive days with a daily maximum temperature above 30 °C. Print them in run.py.

The data contains two heat waves: 10–14 August 2024 and 1–4 July 2025.

**Observe:** Compare the two results with `git diff`. Which docstring did each version get? Did each version add tests? Did both find the two heat waves?

Commit the result in `~/weather_station` (if it is correct). Leave the changes in `~/weather_station_no_agents` uncommitted; you need them in Task 6.

---

## Task 4: A custom tool (10 min)

The agent could read the 1,096 lines of the CSV file to find out what is in it, but that puts all of them into the context. A tool can give it a summary instead.

The script is in the course repository. Copy it into your project and run it yourself (replace `<course repo>` with the path of your checkout):

```bash
mkdir -p .opencode/tools
cp <course repo>/exercises/data_summary.py .opencode/tools/
python3 .opencode/tools/data_summary.py data/munich_daily.csv
```

Your job: write the tool definition `.opencode/tools/data_summary.ts`, so that the agent can call the script. Use the calculator from the lecture as a model:

```ts
// .opencode/tools/calc.ts (from the lecture)
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

What you have to change: the `description` (what the tool does, and when the agent should use it), the argument (the path of the CSV file), and the command in `execute`. The file name becomes the tool's name: `data_summary`. The script expects the path of the CSV file; `path.join(context.worktree, args.file)` makes it a full path.

Quit OpenCode and start it again (tools are loaded at the start), then ask in a new session:

> Which columns of the station data have missing values, and on which days?

In the session, the tool call shows up as `data_summary` with its argument, e.g. `{"file": "data/munich_daily.csv"}`.

**Observe:** Did the agent call your tool, without being told to? Now rename `data_summary.ts` to `data_summary.ts.off`, restart, and ask again: how does the agent find the answer without the tool, and how much text does that put into its context?

Rename the file back and commit.

---

## Task 5: A skill (10 min)

Every month, the station needs a report in a fixed format. A skill is a written procedure that the agent loads only when the task needs it. Until then, only its `name` and `description` are in the context.

Create `.opencode/skills/monthly-report/SKILL.md`:

```markdown
---
name: monthly-report
description: TODO: what the skill does, and when the agent should use it
---
TODO: the steps
```

The steps should say:
- Load the data with `clean(read_csv(...))` and compute everything with the functions in `weather.stats`. Don't write new functions for a report.
- Write the report to `reports/YYYY-MM.md`, in exactly this format:

  ```markdown
  # Station report 2025-07

  | Quantity | Value |
  | --- | --- |
  | Mean daily maximum | 24.8 °C |
  | Mean daily minimum | 16.1 °C |
  | Anomaly of the mean maximum (baseline 2023–2024) | +1.4 °C |
  | Total precipitation | 80.1 mm |
  | Missing days (tmax / tmin / precip) | 0 / 2 / 0 |
  | Heat waves | 2025-07-01 to 2025-07-04 |
  ```

Restart OpenCode and test, each in a new session:

> Write a report for July 2025.

> What does the anomaly function return?

When the agent loads the skill, the session shows a `Skill "monthly-report"` step.

**Observe:** Was the skill loaded for the first request and not for the second? Change the `description` to "Report helper." and try the first request again: what decides *whether* a skill is used?

---

## Task 6: A review agent (10 min)

A custom agent has its own system prompt and its own permissions. A subagent runs in a fresh context and returns only its final report to your session.

Create `.opencode/agents/convention-reviewer.md`. Requirements:
- `mode: subagent`
- It may not edit files (`edit: deny`) and may run only `git diff` and `git status` (a `bash` permission with patterns: `"*": deny` first, then the allowed commands).
- The body (its system prompt) says: read `AGENTS.md`, read the uncommitted changes, check each convention, report each problem with file, line and the convention it breaks. Don't fix anything.

The frontmatter of the lecture's example shows the format:

```markdown
---
description: Reviews a diff for bugs and missing tests. Use after an implementation step.
mode: subagent
permission:
  edit: deny
  bash: ask
---
You review code changes. ...
```

Test it on the result from Task 3 that was written *without* the conventions:

```bash
cp -R ~/weather_station/.opencode/agents ~/weather_station_no_agents/.opencode/
cp ~/weather_station/AGENTS.md ~/weather_station_no_agents/
cd ~/weather_station_no_agents && opencode
```

> @convention-reviewer review my uncommitted changes

**Observe:** Which problems did the reviewer find? What arrived in your main session: the reviewer's file reads, or only its report? Ask the reviewer to fix the problems: what happens, and why?

---

## Wrap-up

For each of these, say what is in the context of *every* request, and what only when it is needed: `AGENTS.md`, a custom tool, a skill, a subagent.

*Your answer:*
