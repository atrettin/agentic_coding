# LLMs & Agentic Coding

Lecture and exercise material. Lecture plan: [LLMs & Agentic Coding — Lecture and Exercise Plan](https://claude.ai/artifact/1wdg6bzmGcA6B4eaNd1PBZ).

## Models

| Role | Model | Runs |
| --- | --- | --- |
| Base | [allenai/OLMo-2-0425-1B](https://huggingface.co/allenai/OLMo-2-0425-1B) | Locally, 3 GB (BF16) |
| Aligned | [allenai/OLMo-2-0425-1B-Instruct](https://huggingface.co/allenai/OLMo-2-0425-1B-Instruct) | Locally, 3 GB (BF16) |
| Capable instruct model (hallucination demos, tool calling) | `qwen3-30b-a3b-instruct-2507` | [GWDG SAIA API](https://docs.hpc.gwdg.de/services/ai-services/saia/index.html) |

The OLMo pair shares pretraining and tokenizer, so any difference between them comes from post-training.
Qwen3.5-2B-Base is not used: given a plain instruction, it opens a `<think>` block and reasons like an assistant,
which spoils the base-vs-aligned contrast.

The API model was chosen from the SAIA models on 2 November 2026: it is fast (~160 tokens/s), has no hidden reasoning,
returns logprobs, and still makes the mistakes Lecture 1 shows (invented parameters, letter counting, obscure facts, arithmetic).
SAIA allows 10 requests per 10 s, 400 per hour and 800 per day per key (response headers, 4 November 2026); the notebook helper waits 1 s between requests.

## Setup

Each student needs a SAIA API key (requested through the KISSKI LLM service) in the environment variable `SAIA_API_KEY`.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/hf download allenai/OLMo-2-0425-1B
.venv/bin/hf download allenai/OLMo-2-0425-1B-Instruct
.venv/bin/jupyter lab
```

## Layout

- `llm_helpers.py`: helpers shared by all notebooks (model loading, SAIA client with rate limiting, token and attention views)
- `lectures/01_lecture_plan.md`: Lecture 1 slide plan
- `lectures/01_what_an_llm_does.ipynb`: Lecture 1 live demos, in the order of the slide plan
- `lectures/02_lecture_plan.md`: Lecture 2 slide plan (tool calling, harnesses, OpenCode)
- `lectures/02_tools_and_agents.ipynb`: Lecture 2 live demos (tool calling by hand and native, the Nobel database)
- `demos/`: scripts for developing the larger demos outside the notebook (attention, retrieval from the context, tool calling)
- `demos/nobel_physics.csv`: all Physics Nobel Prizes 1901–2025 (year, laureates, motivation), from the Nobel Prize API
- `docs/model_findings.md`: what we found out about the models we tried, including the ones we didn't use
- `exercises/00_template.ipynb`: template and conventions for new exercises
- `exercises/01_llms_and_tools.ipynb`: tokens, sampling (temperature, top-p), a letter-counting tool for Qwen written by hand
- `exercises/02_opencode.md`: OpenCode on the example project: fix a bug, `AGENTS.md`, a custom tool, a skill, a review agent
- `exercises/data_summary.py`: the script students copy into the project in Exercise 2, Task 4
- `exercises/weather_station/`: the example project for Exercise 2 (students copy it out of the repo); its data come from `demos/make_weather_data.py`
- `demos/weather_solution/`: reference solutions for Exercise 2
