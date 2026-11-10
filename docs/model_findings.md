# Model findings

What we found out about the behaviour of the models we tried for the course, so that nobody has to find it out again.
Numbers come from greedy decoding (temperature 0) unless stated otherwise. Local runs: Apple M3 Pro, MPS, BF16.
Scripts that reproduce the larger tests are in `demos/`.

## Summary

| Model | Where | Status | Why |
| --- | --- | --- | --- |
| OLMo 2 1B (`allenai/OLMo-2-0425-1B`) | local | **used** (base) | Behaves like a real text continuer; same pretraining as the Instruct model; open training data |
| OLMo 2 1B Instruct (`allenai/OLMo-2-0425-1B-Instruct`) | local | **used** (aligned) | Clean base-vs-aligned contrast; attention weights readable |
| Qwen3 30B-A3B Instruct 2507 (`qwen3-30b-a3b-instruct-2507`) | SAIA API | **used** (capable model) | Fast, no hidden reasoning, logprobs, still makes the mistakes Lecture 1 shows |
| Llama 3.1 8B Instruct (`meta-llama-3.1-8b-instruct`) | SAIA API | tested, not used in Lecture 1 | Good at retrieval, but needs a system prompt (see below) |
| Qwen3.5 2B Base | local | rejected | Not a real base model: opens a `<think>` block and answers like an assistant |
| EuroLLM 22B | SAIA API | rejected | Too slow |
| Gemma 4 31B | SAIA API | rejected | Loops on raw `/completions` |
| GLM 5.3 Flash, Qwen3.6 35B | SAIA API | rejected | Reasoning models: they think first and often return empty content (`content` is `None`) within a normal token budget |

## OLMo 2 1B (base and Instruct)

**Setup**
- 16 layers × 16 heads, context 4,096 tokens, vocabulary 100,278 tokens. About 3 GB each in BF16.
- Load with `attn_implementation="eager"`, otherwise `output_attentions=True` returns nothing.
- The base tokenizer has no chat template (`chat_template is None`; `apply_chat_template` raises `ValueError`). To give the base model a chat document, use the Instruct tokenizer's template text.
- Instruct template: `<|endoftext|><|user|>\n…\n<|assistant|>\n`, with an optional `<|system|>` block. The turn ends with `<|endoftext|>`.
- MPS sampling gives different draws than the CPU for the same seed. With seed 0, one demo drew a 0.03% `<|endoftext|>` token: bad luck, not a bug (300 seeds looked fine). The demos use seeds 1 and 2.

**Tokens and the distribution**
- "The Technical University of Munich was founded in" → `' '` 87%: years are cut into a space token and digit tokens. With a trailing space in the prompt, the next token starts the year, and the distribution is flat: '190' 8.5%, '192' 8.0%, '194' 7.2%, '191' 7.2%, '189' 6.4%, … The base model has no idea (correct: 1868). Sampling by hand (seed 1) drew "1921".
- "The capital of Australia is" (base): Canberra 72%, Sydney 5%, Melbourne 1%.
- Strawberry (Instruct): "How many times does the letter r occur in the word strawberry? Answer with a number only." → 3; "How many r's are in the word strawberry?" → 2. ` strawberry` is one token.

**Common misconceptions on the base model** (38 prompts tested, see the list below)
- The myth wins clearly: "Bulls get angry when they see the color" → " red" 72%; "The Great Wall of China is the only man-made structure visible from" → " space" 53%; "We lose most of our body heat through our" → " head" 47% + " heads" 27%.
- Misquotes are near certain, but the prompt already contains most of the quote: "Let them eat" → " cake" 95% (" brioche" 0.2%); "Elementary, my dear" → " Watson" 95%; "Play it again," → " Sam" 98%.
- The truth wins on all capitals tried: Turkey (Ankara 68%, Istanbul 14%), Canada (Ottawa 87%), Brazil, Switzerland, New Zealand, Pakistan, Morocco, Myanmar, Vietnam. South Africa splits three ways (it has three capitals).
- Diffuse or unusable: 10% of the brain (top token is a space), goldfish memory, Napoleon's height, Einstein failing maths, blood colour, sugar and hyperactivity, spiders, Vikings' horns (" horns" 25% top, but no token carries "no horns").

**Prompting the base model**
- A plain instruction ("Write a haiku about neutrinos.") gets continued as text, not answered, and the base model soon repeats itself.
- The base model given the Instruct template loops on `<|user|>` lines; the Instruct model writes a haiku. First token after `<|assistant|>`: base 'Ne' 9%, Instruct 'Ne' 23%.
- An article plus "TL;DR:" gives a one-sentence summary; without it, the article goes on.
- A Q/A few-shot prompt gives the right short answer ("100"), then the model writes the next Q/A pair itself.

**Attention**
- Attention sinks: in the average over all heads, most attention goes to a few tokens: the first token, a comma, or template tokens such as `>\n`. Single heads do the specific work. `attention_viewer` marks the top 3 sinks with a dashed border.
- Ambiguity (base model, `demos/ambiguity.py`): layer 6, head 12 looks from an ambiguous word back to the word that resolves it.
  - "With his fishing rod over his shoulder, Tom walked down to the bank" → head 6.12 at "bank": 61% on "fishing", 12% on "rod"; continues " of the river. He was looking for a place to cast his line."
  - Same with "backpack": 4% on "backpack"; continues ". He was going to ask for a loan."
  - Same head with "computer" → mouse (61%, " clicked") and "baseball practice" → bat (42% + 24%, " swung"). Neutral words ("desk", "table", "day at work", "guitar") get little.
  - With a long detour between "fishing rod" and "bank", the head drops to 6% and the model says " deposit".
  - Test design: put the resolving word in a side phrase, not as the subject ("The fisherman walked…"). Some heads look at the subject in every sentence, which confounds the test.
- Year (Instruct, "Who won the Nobel Prize in Physics in 1951? Answer in one sentence."): layer 9, head 10 puts 80% of its attention on "1951" while the model predicts the first name. The answer is still wrong.
  - At the first answer step, "The" wins and " Albert" is second with about 11%.
  - First name after "The Nobel Prize in Physics in {year} was awarded to": no year → " Albert" 12%; 1903 → " Wilhelm" 86%; 1921 → " Wilhelm" 33%; 1951 → " William" 38%; 1965 → " William" 31%; 2001 → " William" 26%. The model has stored eras, not winners.
- Wakanda (Instruct): "What is the capital of Wakanda?" → "Kongwe" (correct in the stories: Birnin Zana). The name tokens get low probability.

**Retrieval from the context** (`demos/context_list.py`, `demos/context_beats_memory.py`, `demos/lost_in_middle.py`)
- Nobel list 1945–1960 (16 lines, 214 tokens) + the 1951 question: " John" 99% (2.8% without the list). Head 12.7: 68% on the 1951 line. In free generation (as in `attention_viewer`): step 0, head 12.7 puts 40% on " John" in the 1951 line; step 1, head 10.4 puts 78% on " Cock", the token it copies next.
- The answer adds an invented reason that is not in the list: "for their work on the creation of the first artificial radio wave".
- But only 9 of 16 years right; most misses copy the neighbouring line (1947 → 1946 winner, 1949 → 1948, 1958 → 1957). List 1915–1960 (46 lines, 467 tokens): 14 of 40 right, 1951 still right (87%).
- Fake entry (Heinrich Vogel) after the fixed start "…was awarded to": 1951 → " Heinrich" 78%, " John" 0.1%; 1921 → " Heinrich" 42%, " Albert" 0.2%. In a free answer the model does not copy the fake name; it picks a neighbouring line (Felix Bloch for 1951, "Johannes Bohr" for 1921).
- Needle in a haystack (a code word for "the lab door" in random filler sentences; 250–3,500 tokens; 5 depths; 10 needles): no lost-in-the-middle U-curve.
  - No distractors: 10 of 10 almost everywhere (9 of 10 at 3,500 tokens, depths 25% and 50%).
  - 4 or 20 same-shaped distractors ("The code word for the kitchen door is walnut."): 7–10 of 10, no position pattern.
  - 20 distractors and a paraphrased question ("Which word opens the laboratory?"): 5–10 of 10, scattered.

**Tool calling** (`demos/nobel_lookup.py`; database `demos/nobel_physics.csv`, from the Nobel Prize API, 6 November 2026)
- The chat template has no tool role: a `tool` message is dropped without an error. The harness has to define the call format and return the result as ordinary text (we use a user turn: "Database row: …").
- The template accepts a `<|system|>` block, but the model card's chat format has none, and the model ignores instructions there. Found by Alexandra Trettin, 9 November 2026.
- Tool description ("To look up a year, write only lookup(YEAR)…") and "Who won the Nobel Prize in Physics in {year}?", 1915–1960 (40 years), free calls:
  - Instruction in a system turn, with or without "Answer in one sentence.": 0 of 40 calls.
  - Instruction in the user turn, with "Answer in one sentence.": 0 of 40.
  - First-token probability of `lookup` for 1947, in the order system/one sentence, system, user/one sentence, user: 0.00%, 0.16%, 0.00%, 96%.
  - Instruction in the user turn, without it: 40 of 40 calls with the right year; with the row in the context, the answer names a laureate of that year in 40 of 40 (short answers, often only the names). The whole list in the context, same question, same check: 16 of 40.
  - "…in {year}, and for what?" instead: 38 of 40 calls (1917 and 1927 answer from memory).
  - "…Look up the data first, then answer in a full sentence." appended to the question: 0 of 40 calls (P(`lookup`) 0.31% for 1947). The 1B model can't follow a chained instruction (found by Alexandra Trettin, 9 November 2026).
  - The harness can add the second instruction when it returns the row: "Answer the question in a full sentence using the following information: {row}" instead of "Database row: {row}". 40 of 40 answers are full sentences that name a laureate and give the database's reason, some shortened or paraphrased (Planck: "…for his discovery of energy quanta"; Barkla: "X-ray" for "Röntgen"). Suggested by Alexandra Trettin, measured 9 November 2026.
  - Off-topic questions in the working harness (instruction in the user turn): the model looks up anyway. Capital of Australia → `lookup(Australia)`, "No entry for Australia." → "Canberra". 12 * 13 → `lookup(12)` → "…so I cannot provide the answer". Who discovered the neutron? → `lookup(1931)` (not awarded) → "The neutron was not awarded the Nobel Prize in Physics in 1931." Chemistry 1911 → `lookup(1911)`, the Physics row → "Wilhelm Wien won the Nobel Prize in Chemistry in 1911…" (correct: Marie Curie). What did Edward Appleton discover? → `lookup(1903)` (the example year in the instruction). Haiku about neutrinos → no call, a haiku.
  - A worked example exchange (1903) in front, with the instruction in a system turn and "Answer in one sentence.": still 0 calls.
- Calculator (`demos/olmo_calc.py`, 10 November 2026), the same document shape: "You can use a calculator. To compute something, write only calc(EXPRESSION), for example calc(2 + 3), and nothing else. You will get the result back." and the question in the user turn; the harness returns "Answer the question in a full sentence using the following information: {expression} = {result}".
  - 20 of 20 calls with the question's expression; 19 of 20 answers right (1234567 × 7654321, 12 × 13, a sum, 17 random five-digit products). The miss copies a 10-digit result wrongly ("2,743,014,740"): copying is sampled too.
  - Without the tool, "…? Answer with the number only." → "The answer is 6000000000." (correct: 9449772114007).
  - P(`calc`) for 1234567 × 7654321: system turn 36% (and the model then writes a result itself: "calc(…) = 8000000000"); user turn 91%; user turn + "Answer with the number only." (the Lecture 2 cliffhanger wording) 7%; + "Answer in one sentence." 0.11%; + "Use the calculator first, then answer in a full sentence." 22%. The last three answer from memory, wrongly.
  - Off-topic: capital of Australia → `calc( Canberra )`, the harness's error message ends up in the answer ("…is Canberra, which is an error: only numbers…"); Nobel 1951 → `calc(1951 Nobel Physics Prize winner)`; strawberry → `calc(5)` → "contains the letters r and s exactly 5 times"; haiku → no call.
- Forced call (the harness writes `lookup(` and the model only fills in the year; instruction in a system turn, "Answer in one sentence."): right year in 40 of 40, right first laureate in 39 of 40 (the 1925 miss names Hertz only). The free call in the right document makes this unnecessary.

## Qwen3 30B-A3B Instruct 2507 (SAIA API)

- About 160 tokens/s, no hidden reasoning, logprobs with `top_logprobs`, `n=` for several samples, and raw `/completions` without a template. Vocabulary 151,669 tokens; digits are single tokens.
- Template: `<|im_start|>system … <|im_end|>`, `<|im_start|>user …`, `<|im_start|>assistant`. Logprob streams end with `<|im_end|>`.
- Invents a parameter of a real function: "What does the tolerance_mode argument of scipy.integrate.solve_ivp do?" → a fluent explanation ("controls how the relative and absolute tolerances are interpreted…"). It usually notices a function that does not exist at all (`numpy.linalg.robust_solve`).
- Letter counting: "How many times does the letter s occur in the word Donaudampfschifffahrtsgesellschaftskapitän?" → 11 (correct: 5). Gets strawberry right (seen too often).
- Mössbauer's doctoral advisor → "Wolfgang Pauli" at 75% (correct: Heinz Maier-Leibnitz). Once "Wolfgang" is drawn, "Pauli" follows with near certainty.
- TUM founding year: correct (1868), high probability.
- Wakanda (max_tokens=80): "Bakassa", then a "correction" to "Kahndaq" (a DC Comics country). Name tokens low probability.
- 1234567 × 7654321 → 9449999999999 (correct: 9449772114007).
- Raw `/completions` with "The capital of Australia is" → " Canberra." followed by a list of more capitals: without the template it behaves like a base model.
- Tool calling works (`demos/tool_loop.py`), both by hand on raw `/completions` (a system prompt describing `<tool_call>{"name": "calc", …}</tool_call>`, stop at `</tool_call>`) and through the `tools` field of `/chat/completions`. The server writes Qwen's `# Tools` system block and `<tool_call>` tags, the same format as the hand-written version; the tool result goes back as a user turn with `<tool_response>`.
- It decides by itself when to call: with a `lookup(year)` tool it calls once for one year, twice (in one turn) for "1951 and 1952", and not at all for "What is the capital of Australia?". Answers copy the database row.
- Questions the `lookup` tool can't answer: no call in any case. 12 × 13 → 156, neutron → Chadwick, Appleton → the ionosphere ("I cannot provide information … based on the available tools. However, …"), Faust → Goethe with the same hedge. Chemistry 1911: "Marie Curie" in one run, a refusal ("None of the available functions can provide information…") in another.
- The instructions that break the 1B model's calls don't break this model's (`tool_loop.robustness()`, 10 November 2026, `calc` and `lookup` both offered, 2 of 2 runs alike): "…7654321? Answer with the number only." → `calc` → "9449772114007"; "…? Answer in one sentence." → `calc` → one sentence; "…1947? Answer in one sentence." and "…Look up the data first, then answer in a full sentence." → `lookup(1947)` → one sentence with Appleton and the database's reason. The format instruction shapes the answer, not the decision to call. It always picks the right one of the two tools; capital of Australia and haiku: no call.
- Templates: without tools, Qwen's document is `<|im_start|>user\n…<|im_end|>\n<|im_start|>assistant\n…`, the same shape as OLMo's `<|user|>\n…\n<|assistant|>\n…`. With `tools`, the template adds a system block "# Tools … `<tools>`{schemas}`</tools>` … within `<tool_call></tool_call>` XML tags"; OLMo's template has no such block.
- `tool_choice="required"` works on SAIA. Forced to call the calculator for "What is the capital of Australia?", it calls `calc` with `"2 + 2"`.
- Wrong arguments from memory: "…ten years after the transistor prize?" → `lookup(1957)` in two of two runs; it takes the 1947 invention as the prize year (the prize was 1956). "…the year after Albert Einstein won it?" → `lookup(1922)` in one run, `lookup(1923)` in another, both at temperature 0 (the 1921 prize was awarded in 1922): the API is not fully deterministic.

## Qwen3.8 27B in OpenCode 1.18.27 (SAIA API)

- Custom tool `calc` (`demos/opencode_tools/`, in `.opencode/tools/`), with no instruction to use it. `opencode run`, two runs per question:
  - It called `calc` with the right expression in 10 of 10 runs: "What is 1234567 * 7654321?", the same question with "Answer with the number only.", "(1234567 * 7654321 - 98765) / 4321", and a marble word problem, which it turned into `1234567 * 7654321 - 98765`.
  - It made no call for "What is 2 + 2?".
- With the docs' `python-add` tool instead, it added in its head, correctly, even for two 17-digit numbers. It called the tool only when told "Use the python-add tool".
- With no custom tool, it ran `python3 -c "print(...)"` through `bash` (2 of 2 runs).
- OpenCode installs `@opencode-ai/plugin` into `.opencode/` by itself.

## Llama 3.1 8B Instruct (SAIA API)

- Without a system prompt, it starts answers with an invented tool call, e.g. `tool.call('geography.getCapital', 'Australia')` before the answer. Any system prompt ("You are a helpful assistant.") fixes it. `demos/api_retrieval.py` always sends one.
- Retrieval (`demos/api_retrieval.py`) is nearly perfect:
  - Nobel list: 16 of 16 (1945–1960) and 40 of 40 (1915–1960).
  - Needle with 20 distractors: 5 of 5 everywhere up to 16k tokens; at 32k, 4 of 5 at depths 25% and 50%. Paraphrased question: 5 of 5 up to 16k, one miss at 32k. No clear U-curve.
- From memory, it knows 1951 (Cockcroft and Walton, with the right reason), so 1951 is no "wrong without the list" demo for this model. Wrong without the list: 1920 → "Walther Nernst for his work on the thermal theory of radiation" (correct: Guillaume; Nernst won the 1920 Chemistry prize); 1953 → "not awarded" (Zernike); 1945 → "not awarded" (Pauli); 1915 → "not awarded" (the Braggs); 1917 → Planck (Barkla).
- Fake list entry: 1951 → "Heinrich Vogel won the Nobel Prize in Physics in 1951." 1921 → "…awarded to Albert Einstein, not Heinrich Vogel, however, I couldn't find any information about a person named Heinrich Vogel…". Weak knowledge gives way to the context, strong knowledge resists.

## SAIA API

- OpenAI-compatible at `https://chat-ai.academiccloud.de/v1`, key in `SAIA_API_KEY`. Students get keys through the same form, with the same limits.
- Rate limits from the response headers on 4 November 2026: 10 requests per 10 s, 400 per hour, 800 per day (the website said less). `llm_helpers.api()` waits 1 s between requests; running two scripts at once can still exceed the limit.
- A request can hang; the client has a 60 s timeout.
- Prompts of 32k tokens work with Llama 3.1 8B.

## Method pitfalls

- **Check the tokenization of the answer.** The first token of an answer is often a space, a quote mark (`' "'` took 60% in the needle test) or a part of a name (`' F'` for Frits, `' Ni'` for Niels). Compare against the first token of the tokenized answer, or check the generated text.
- **A synthetic needle is too easy.** When the question repeats the needle's words, the model only has to match tokens. Even with a paraphrase and 20 distractors, models up to 8B found it. The published lost-in-the-middle effect needs long, realistic contexts (many similar documents) or harder tasks.
- **A free answer and a fixed answer start can disagree.** The context-beats-memory effect is clear after "…was awarded to", but not when the 1B model writes its answer freely.
- **Pick the head, not the average.** Averaged over all heads, attention sinks dominate and the effect disappears.
- **Metal hang on macOS.** A background run can stall in Metal device creation, probably while the screen is locked. `LLM_DEVICE=cpu` forces the CPU. Notebook runs of the whole lecture take about 10 minutes.
- **ipywidgets in VS Code** need a live kernel; a notebook executed with nbconvert shows no widget until re-run.
