# Reference solutions for Exercise 2

Copy these into your project (`~/weather_station`) only after you have tried the tasks yourself.

- `AGENTS.md`: Task 2
- `.opencode/tools/data_summary.ts`: Task 4 (next to `data_summary.py`, copied from `exercises/`)
- `.opencode/skills/monthly-report/SKILL.md`: Task 5
- `.opencode/agents/convention-reviewer.md`: Task 6

There is no reference code for the bug fix and `heat_waves`: the agent writes them, and any version that passes your review and the tests is fine.
The bug: `clean()` in `weather/load.py` replaces `-999` with NaN in `tmax` only, but `tmin` (July 2025) and `precip` (March 2024) have missing values too.
