# Lecture 1: What an LLM does — slide plan

Working draft, iteration 2: duplicates removed, material that later parts don't build on moved to the backup.
Each slide gives what the slide shows (pictures and examples, not text to read), and speaker notes.
`[DEMO]` means a switch to the live notebook (`lectures/01_what_an_llm_does.ipynb`).

**Where the students should be at the end**

1. An LLM samples tokens, one at a time, from a probability distribution that is conditioned on all previous tokens.
2. The mechanism of that conditioning is multi-head attention.
3. Sampling is indifferent to truth: the distribution reflects what is common in the training data.
4. Prompts condition the model to perform tasks, such as summarising and answering questions.
5. Alignment shifts the distribution towards the "assistant" role.
6. A prompt can carry the information the answer needs; by attending to it, the model answers from it instead of guessing.

**Structure and rough minutes (total ≈ 78, target 90; the rest is buffer for questions and demos)**

| Part | Topic | Min |
| --- | --- | --- |
| 0 | Hook: from ChatGPT to coding agents | 4 |
| 1 | "GPT": the four questions | 2 |
| 2 | Generative: tokens, distribution, sampling | 12 |
| 3 | Transformer: attention as the conditioning mechanism | 12 |
| 4 | Pretrained: what the base model learned, prompting as conditioning | 11 |
| 5 | Chat: alignment and the chat template | 11 |
| 6 | Limits and context: confidently wrong, and the information in the prompt | 22 |
| 7 | Wrap-up and bridge to Lecture 2 | 4 |

---

## Part 0 — Hook (4 min)

### 0.1 November 2022
- News clips and headlines from the ChatGPT launch (30 November 2022): "1 million users in 5 days", "100 million users in two months" (UBS estimate, January 2023).
- Screenshots: early viral conversations (poems, code, essays, exam answers).

> Notes: In November 2022, OpenAI released ChatGPT: a language model you could just talk to. It seemed to perform any task and answer any question. Within two months it had more users than any consumer app before it.

### 0.2 Today: models that work on their own
- Short flashes (GIFs or screen recordings) of Claude Code, Codex and OpenCode working on a repository: reading files, editing them, running tests, fixing failures.
- One line each: release dates (Claude Code early 2025, Codex CLI April 2025, OpenCode 2025; check the dates).

> Notes: Three years later, tools like these take a task such as "add this feature", work on it for many minutes, run the tests and fix their own mistakes. How does a model do that? To answer that, we first need to know what the model itself does. That is today's lecture. Next lecture: how a program around the model turns it into an agent.

### 0.3 Today's question
- "What is a large language model, what can it do, and where does it fail?"

> Notes: Promise the students that by the end they can explain every step of what happens between typing a question and getting an answer.

---

## Part 1 — "GPT" (2 min)

### 1.1 ChatGPT
- "ChatGPT" in large letters. Then it splits: **Chat** + **G**enerative **P**re-trained **T**ransformer.
- Four questions appear, one per click, in the order of the name:
  - What does *generative* mean?
  - What does *pre-trained* mean?
  - What is a *transformer*?
  - What makes it *chat*?
- Then the questions reorder into the lecture order: generative, transformer, pre-trained, chat.

> Notes: This name is our outline. We take the questions in a different order than the name, because each answer needs the one before it: "transformer" explains how the earlier tokens condition the distribution, and we need that to understand what pre-training stored in the model. Keep this slide; we come back to it at the end and tick off the questions.

---

## Part 2 — Generative (12 min)

Concepts introduced: token, vocabulary, next-token distribution, sampling, autoregressive loop, context window.

### 2.1 A model that continues text
- A sentence fragment, "The Technical University of Munich was founded in", with a blank.
- Question to the audience: what comes next?

> Notes: Let the students guess. Most will say a year. That is what the model does too: it continues text. But it doesn't continue in words or letters. It continues in tokens.

### 2.2 Text becomes tokens `[DEMO]`
- Picture: a sentence cut into coloured pieces, each with its ID number.
- Examples: a common English word (1 token), a rare word (several), German compounds, code, a number.
- Demo: `show_tokens` on the API model's tokenizer.

> Notes: The model has a fixed vocabulary of about 100,000–150,000 pieces. Common words are one piece; rare words are cut into several. The model never sees letters, only these IDs.

### 2.3 Consequence: the model doesn't see letters `[DEMO]`
- "How many s are in 'Donaudampfschifffahrtsgesellschaftskapitän'?" API model: 11. Correct: 5.
- Picture: the word as the model sees it (token pieces).

> Notes: A light, funny demo with a serious point: what looks like a trivial task for us is hard for the model, because its input is not what we see. Remember this when a coding model miscounts characters or columns. First slide to cut if the lecture runs long.

### 2.4 The output: a probability for every token `[DEMO]`
- Bar chart: top 10 next tokens for the TUM sentence, with their probabilities.
- Note on the slide: "the model's whole output is this list, over the whole vocabulary".
- Demo: `show_top`.

> Notes: This is the key picture of the lecture. The model does not output an answer. It outputs a probability distribution over the vocabulary for the next token. Everything else is built around this.

### 2.5 Generating = sampling, appending, repeating `[DEMO]`
- Diagram: prompt → distribution → draw one token → append → new distribution → …
- Demo: `generate_by_hand`, step by step, with the drawn token highlighted each time.

> Notes: Generating text is a loop. Draw one token from the distribution, append it to the text, compute a new distribution for the extended text. Each new token is conditioned on everything before it, including the tokens the model wrote itself. Hence "generative" and "autoregressive". Note that the model can't take a token back once it has drawn it.

### 2.6 Same prompt, different answers
- Two or three continuations of the same prompt with different seeds.
- One line: "temperature" and "top-p" change how the draw is made → Exercise 2.

> Notes: Because we draw, the same prompt gives different texts. Greedy decoding (always the most likely token) is repeatable but often boring or repetitive. Temperature sharpens or flattens the distribution; top-p cuts off the unlikely tail. The details are in the exercise.

### 2.7 The context window
- Picture: a long strip of tokens with a window frame; everything inside the frame conditions the next token, nothing outside exists.
- Numbers: OLMo 2 1B, 4,096 tokens; the API model, 256k (check); typical coding agents, 200k–1M.

> Notes: "All previous tokens" means: all tokens in the context window. That is the model's entire working memory: there is no other memory between calls. Keep this picture in mind; in Part 6 and in Lecture 2 it becomes central.

### 2.8 Answer 1
- Back to the four questions: tick *generative*. "It samples the next token from a distribution conditioned on all previous tokens."

---

## Part 3 — Transformer (12 min)

Concepts introduced: embedding (as "a vector per token"), layer, attention, head, multi-head attention, attention sink.

### 3.1 How does the earlier text get into the distribution?
- The question, with the TUM example: "founded in" alone could be anything; "Technical University of Munich … founded in" points to a year near 1868.

> Notes: Last part: the distribution is conditioned on all previous tokens. How? That is what the transformer architecture does. We stay at the level of a picture; no maths.

### 3.2 What is transformed? `[DEMO]`
- Live demo: [Transformer Explainer](https://poloclub.github.io/transformer-explainer/) (GPT-2 small in the browser; paper: https://dl.acm.org/doi/10.1145/3772318.3791725). Type a prompt, follow it from embeddings through the blocks to the output probabilities. Open one attention head to show the weights.
- Diagram for the slide: tokens → one vector per token → a stack of layers (OLMo 2 1B: 16) → the *last* token's vector → classifier → distribution over the vocabulary.
- Each layer: an *attention* step, then a *feed-forward* step. In: a sequence of vectors. Out: a sequence of the same length, every vector changed.
- Each attention step has many heads in parallel. OLMo 2 1B: 16 layers × 16 heads = 256 attention patterns per token.
- Reference image: "Attention Is All You Need" (2017), figure 1, shown small for recognition.

> Notes: What gets transformed is the input sequence. Each token becomes a vector of numbers. Each layer adds an update to every vector, so the sequence keeps its length, but each token's vector morphs: it takes on meaning from its context. The feed-forward step works on each position alone; much of the stored knowledge sits there. The attention step is the only place where positions exchange information: at every layer, each token asks "which earlier tokens matter for me?" and takes a weighted mix of their vectors. The weights sum to 100%, they look only backwards, and they are computed from the content, so they differ for each text. A layer has many such patterns in parallel, the heads; each head learns to look for something different, and nobody programs what. At the end, a classifier looks only at the last token's final vector and computes the logits for the next token. The other final vectors are not used for this prediction, but their states in the earlier layers are what the last token attended to on the way. (Aside if asked: in training, the classifier is applied at every position at once, so one text gives a prediction task for every token.)
> Fallback without internet: the attention diagrams in backup B.1.

### 3.3 Which bank? `[DEMO]`
- Two sentences that differ in one word, both ending at "bank":
  - "With his **fishing rod** over his shoulder, Tom walked down to the bank" → " of the river. He was looking for a place to cast his line."
  - "With his **backpack** over his shoulder, Tom walked down to the bank" → ". He was going to ask for a loan."
- Demo: `attention_viewer(base, ...)` on both, step 0, layer 6, head 12.
- Slide picture: the two sentences with head 6.12's attention from "bank" shaded: 61% on "fishing" (+12% on "rod") vs. 4% on "backpack".

> Notes: "Bank" alone is ambiguous; only an earlier word can resolve it. Ask the class which bank each sentence means, then show that the model resolves it the same way. At the "bank" position, one head (layer 6, head 12) looks back to "fishing" and pulls that information into the vector for "bank". With a backpack, the same head finds nothing relevant and the model falls back to the default meaning, the money bank. Point out that the average over all heads shows mostly the comma, an *attention sink*: a parking spot for heads that have nothing to look up, drawn with a dashed border in the viewer. Single heads do the specific work. This ties back to 3.2: the vector of "bank" is what got transformed.
> Tested on OLMo 2 1B base. Same head, same behaviour with "computer" → mouse ("clicked", 61%) and "baseball practice" → bat ("swung", 42% + 24%); neutral controls ("desk", "table", "day at work") get little or no attention. Aside if asked: with a long detour between "fishing rod" and "bank", the head loses it (6%) and the model goes back to " deposit". That previews 6.6.

### 3.4 Answer 2
- Tick *transformer*: "A stack of layers; attention lets each position use the earlier tokens. Many heads, each looking for something different."

---

## Part 4 — Pre-trained (11 min)

Concepts introduced: pre-training, base model, training data as the source of the distribution, prompting as conditioning.

### 4.1 Where do the probabilities come from?
- Picture: a huge pile of text (web pages, books, code, papers), with a number: OLMo 2 1B, about 4 trillion tokens (check).
- Training loop picture: hide the next token, predict it, compare, adjust the weights slightly. Repeat trillions of times.
- What this forces the model to learn: grammar, spelling, facts ("Paris" after "The capital of France is"), styles, code syntax, the structure of documents (headings, lists, Q&A pages, forum threads).

> Notes: Pre-training is only next-token prediction on a huge amount of text. The model gets better when it gives the true next token a higher probability. Nothing else: no "facts" table, no rules of grammar, no notion of truth. But to predict the next token well, the model has to pick up a lot about the world. That is why a pure next-token predictor seems to "know" things.

### 4.2 Common is not the same as true `[DEMO]`
- A prompt where the most common continuation in text is wrong. Candidates: "The capital of Australia is" (Sydney vs. Canberra), "Humans use only 10% of their" (brain), "The Great Wall of China is visible from".
- Demo: `show_top(base, ...)`.

> Notes: Plant the idea here, show it in full in Part 6: the distribution reflects what is frequent in the training text, not what is true. If a misconception is common, it gets probability. Keep to about a minute.
> To test: which of the candidates shows the effect on OLMo 2 1B base.

### 4.3 A base model continues documents `[DEMO]`
- Give the base model a plain question. It doesn't answer; it continues with more questions, a list, or a forum page.

> Notes: The base model has no idea it is being asked something. To it, the question is the beginning of a document, and it writes what usually follows such a beginning on the web.

### 4.4 Prompting = writing the start of the right document `[DEMO]`
- Two prompts on the base model, each a document whose natural continuation is the task:
  - Summary: an article followed by "TL;DR:".
  - Question answering: "Q: … A:".

> Notes: That is the core of prompting: you condition the distribution so that the result you want is the likely continuation. The model can summarise because "TL;DR:" followed by a summary is common text. Every prompt technique you will meet is a variant of this. (More examples: backup B.3.)

### 4.5 Answer 3
- Tick *pre-trained*: "Trained to predict the next token on trillions of tokens. It learned what is common in text. Prompts condition it to perform tasks."

---

## Part 5 — Chat (11 min)

Concepts introduced: alignment (post-training), chat template, special tokens, assistant role, system prompt.

### 5.1 From base model to assistant
- Picture: base model → supervised fine-tuning on example conversations → preference tuning (which of two answers is better) → aligned model.
- OLMo 2 Instruct: the same pre-trained model, with this post-training added.
- Historical reference: InstructGPT (2022), the step before ChatGPT.

> Notes: Alignment doesn't teach new facts. It trains the model on many examples of conversations, where one side is a helpful assistant. Afterwards, the most likely continuation of a conversation is a helpful answer.

### 5.2 A chat is a document too `[DEMO]`
- The chat template of the OLMo Instruct model as raw text, special tokens highlighted: `<|user|>`, `<|assistant|>`, `<|endoftext|>`.
- The same template with a system prompt: one more block at the top.

> Notes: The model still only continues text. The chat interface writes your message into this template and lets the model continue after "assistant". The model's turn ends when it samples the end token. "The assistant" is a character in this document that the model has learned to write; the system prompt is one more block at the top that conditions what that character is like. Keep this in mind for Lecture 2: an agent's system prompt is the same mechanism.

### 5.3 Same template, different model `[DEMO]`
- The base model and the aligned model, both given the aligned model's template with the same question. Side by side: what each one writes, and `show_top` for the first token.

> Notes: Here you see what alignment did. Same pre-training, same text, but the distribution after "assistant" is shifted: the aligned model puts its probability on an answer, the base model on whatever usually follows such odd markup. Alignment shifts the distribution towards the assistant role. It adds no facts and no access to the truth, but it does change the tone: fluent, helpful, confident. Transition to Part 6: does sounding sure mean being right?

### 5.4 Answer 4
- Tick *chat*: "Post-training shifts the distribution towards the assistant role. The chat itself is a template around your text."
- All four questions ticked.

---

## Part 6 — Limits and context (22 min)

Concepts used: everything before. New: confidence vs. correctness, information in the context, lost in the middle.

### 6.1 Ask about something that doesn't exist `[DEMO]`
- Question to the API model: the `tolerance_mode` parameter of `scipy.integrate.solve_ivp` (it doesn't exist). The model explains how to use it.

> Notes: For programmers, this is the most common and costly failure: an invented parameter, function or flag, written in exactly the style of real documentation. Ask: why does this happen? With what we know now, we can answer: the model writes the most likely continuation of "an answer about solve_ivp's tolerance_mode", and such an answer looks like this.

### 6.2 Wakanda `[DEMO]`
- "What is the capital of Wakanda?" Local aligned model: "Kongwe". API model: "Bakassa", then mixes in "Kahndaq" (a different comic country).
- Correct answer in the stories: Birnin Zana.
- `show_confidence`: the name tokens are red, the sentence around them green. Legend: green = high probability, red = low.

> Notes: Another question about something the model can't know, like 6.1. Here the model knows the shape of the answer (a capital name, African-sounding) but not the answer itself, and the colours show it. The sentence around the name is green: the model is sure *that* it should name a capital, not *which*. Sometimes low probability flags an error like this; the next slide shows it doesn't have to.

### 6.3 Does the model read the year? `[DEMO]`
- Question to the local aligned model: "Who won the Nobel Prize in Physics in 1951? Answer in one sentence."
- Demo: `attention_viewer(aligned, ...)`, step to the first name. Average over all heads, then layer 9, head 10.
- Slide picture: the layer × head heatmap of attention on "1951", with the hot head marked.
- The answer: "William" (38%). The 1951 prize went to John Cockcroft and Ernest Walton.

> Notes: Start with the question: does the model read the year, or does it see "Nobel Prize in Physics" and default to the most famous name? Show the next-token table at the first step: "The" wins, but "Albert" is already second with about 11%, the default answer to "physics Nobel". At the first name, the average hides the year, but single heads put most of their attention on it (layer 9, head 10: 80%). So the attention did its job: the year was read and changed the answer. But what is stored for "1951" is fuzzy, so the sampled name is a plausible one, not the right one, at a middling 38%. Conditioning is not knowing. (Counterfactual years: backup B.2.)

### 6.4 Summary: indifferent to truth
- One sentence on the slide: "The model samples what is likely, given the training data and the context. Whether it is true doesn't enter the computation."

> Notes: The probability measures "how common is this continuation", not "how true". A wrong answer can be very likely. This is the point planted in 4.2.

### 6.5 Put the answer into the context `[DEMO]`
- Prompt: a list of Nobel Prize in Physics winners per year (e.g., 1945–1960), then the 1951 question.
- Demo: the same `attention_viewer` on the aligned model. While it writes the name, attention goes to the "1951" line of the list. The answer: Cockcroft and Walton.
- Slide picture: 6.3 and 6.5 side by side; the attention view with the list line highlighted.

> Notes: Same model, same question, same viewer. Now the information is in the context window, and attention lets the model use it: the "Cockcroft" position attends to the matching list entry. The model no longer has to recall; it copies. This is the most important practical lesson of the lecture: give the model the information it needs.
> To test: whether the 1B model finds the line reliably, and how long the list can be.

### 6.6 More context is not free
- Figure: the "lost in the middle" U-curve (Liu et al., *Lost in the Middle*, TACL 2024): retrieval accuracy vs. the position of the relevant document; high at the start and the end, low in the middle.
- Optional: "context rot" (Chroma, 2025): performance drops as the context grows, even on simple tasks.
- Pointer: Exercise N, hide the needle yourself.

> Notes: Attention has to spread over everything in the context. With a lot of irrelevant text, the relevant piece gets lost, especially in the middle. (The bank head in 3.3 lost "fishing rod" after a long detour.) Practical rule for agentic coding: keep the context focused. Compact long sessions, start a fresh session for a new feature.

### 6.7 Who puts the information there?
- Diagram: the model's context window, with the information coming from: you (pasting), or a program (a search, a file read, a calculator).

> Notes: In 6.5, I pasted the list by hand. A coding agent does that by itself: it asks the program around it to read a file or run a command, and the result lands in its context. That is tool calling, and that is Lecture 2.

---

## Part 7 — Wrap-up (4 min)

### 7.1 The four questions, answered
- The "ChatGPT" slide again, each word with its one-sentence answer:
  - *Generative:* it samples one token at a time from a distribution conditioned on all previous tokens.
  - *Transformer:* attention is how the earlier tokens condition the distribution.
  - *Pre-trained:* the distribution reflects what is common in the training data, not what is true; prompts condition it to perform tasks.
  - *Chat:* alignment shifts the distribution towards the assistant role.
- Plus one line: information in the context can be used by attention. Give the model what it needs, and no more.

### 7.2 Next lecture `[DEMO]`
- A four-digit multiplication on the API model; the answer is close but wrong.
- Teaser: a short program that lets the model call a calculator. "The model writes the call, the program computes, the result goes into the context."
- The coding-agent clips from 0.2 again: "This is the same loop, with files and a terminal instead of a calculator."

> Notes: Calculation by next-token prediction: each digit is a guess conditioned on the previous ones. A program computes it exactly. Putting the program's result into the context is what 6.7 asked for.

---

## Backup

Slides moved out of the main line. Use them for questions, or if time is left.

### B.1 Attention diagrams (fallback for 3.2 without internet)
- Attention, looking back: the current position draws weighted arrows to all earlier tokens; arrow thickness = weight; weights sum to 100%. Only backwards.
- Multi-head attention: the same sentence, several heads, each with its own arrow pattern (one looks at the previous token, one at the subject, one at numbers…).

### B.2 Change the year, change the answer `[DEMO]`
- Aligned model, first name after "The Nobel Prize in Physics in … was awarded to": no year → "Albert" 12%; 1903 → "Wilhelm" 86%; 1951 → "William" 38%.

> Notes: The year changes the distribution in a plausible direction, but not to the right answer. 1903 was Becquerel and the Curies; Röntgen, Wilhelm, was 1901. 1951 was Cockcroft and Walton.

### B.3 More prompts on the base model `[DEMO]`
- Few-shot: three example pairs (e.g., country → capital), then the fourth without the answer.
- Translation: "English: … German:".

### B.4 Tokenizers differ `[DEMO]`
- The same text in OLMo's and Qwen's tokenizer: different cuts, different IDs.
- Strawberry on the local aligned model: 3 or 2 r's, depending on phrasing.

### B.5 Other chat templates `[DEMO]`
- The API model's template (Qwen: `<|im_start|>`, `<|im_end|>`).
- The API model through raw `/completions` with a hand-written template.

### B.6 The assistant is a role `[DEMO]`
- The same question, two system prompts, two styles of answer.

### B.7 Confidently wrong in green `[DEMO]`
- `show_confidence` on the TUM founding year (correct, green) and the Mössbauer question (wrong, "Wolfgang Pauli" at 75%; correct: Heinz Maier-Leibnitz). Also a candidate for Exercise 3.

### B.8 The context beats memory `[DEMO]`
- The Nobel list from 6.5 with a wrong entry for 1951 (a made-up name). The model answers with the made-up name.

> Notes: The model follows the context, even against what it "knows". That is a feature (up-to-date documentation, your own code) and a risk (wrong or outdated documents, text written to mislead the model). Candidate for Lecture 2 (untrusted file contents) or an exercise.

---

## Exercises (homework slot, ~90 min)

| Exercise | Deepens | Status |
| --- | --- | --- |
| 2 Sampling lab: temperature, top-p | Part 2 | Built |
| 3 Confidently wrong | Part 6 | To build |
| N Needle in a haystack: hide a fact in more and more text, at different positions, and see where retrieval breaks | Part 6.5–6.6 | New idea |

## Open questions

- **"Common is not true" (4.2).** Which prompt shows it on OLMo 2 1B base? "The capital of Australia is" gives Canberra 72%, Sydney only 5%.
- **TUM bar chart (2.4).** The top token is `' '` (87%): the tokenizer splits years into a space and digits. Either explain it (it fits 2.2) or end the prompt so that the next token is a word. The hand-sampled loop (2.5, seed 1) drew "1921", a nice wrong year.
- **Context demo (6.5, B.8).** Can the 1B aligned model find the 1951 line in a list, and with which list length? Fallback: the API model with `show_confidence` (no attention view).
- **Lost in the middle on OLMo 2 1B.** Its context is only 4,096 tokens, and the U-curve may not appear; the model may also fail everywhere. Test before designing the exercise. Fallback: run the exercise on the API model with a few long requests (watch the rate limit).
- **Notebook order.** The notebook still follows the old outline; reorder it once the plan is settled.
- **Check the numbers:** ChatGPT user numbers, agent release dates, OLMo 2 1B training tokens, the API model's context length.
