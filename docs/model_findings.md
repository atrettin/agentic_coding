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
