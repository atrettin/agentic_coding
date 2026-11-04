"""Helpers shared by the lecture and exercise notebooks.

Local models (OLMo 2) run with Hugging Face transformers; the capable instruct model runs on the
GWDG SAIA API and needs a personal key in the environment variable SAIA_API_KEY.
"""
import functools
import html
import math
import os
import time

import ipywidgets as widgets
import torch
from IPython.display import HTML, display
from openai import OpenAI
from transformers import AutoModelForCausalLM, AutoTokenizer

DEVICE = os.environ.get("LLM_DEVICE") or (  # LLM_DEVICE=cpu forces the CPU if the GPU backend misbehaves
    "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
BASE = "allenai/OLMo-2-0425-1B"
ALIGNED = "allenai/OLMo-2-0425-1B-Instruct"
API_MODEL = "qwen3-30b-a3b-instruct-2507"


# --- Local models ---------------------------------------------------------

def load(name):
    # "eager" attention is slower than the default but can return attention weights (attention_viewer)
    model = AutoModelForCausalLM.from_pretrained(name, dtype=torch.bfloat16, attn_implementation="eager").to(DEVICE)
    model.tok = AutoTokenizer.from_pretrained(name)  # each model has its own tokenizer
    return model


def encode(model, text):
    return model.tok(text, return_tensors="pt", add_special_tokens=False).input_ids.to(DEVICE)


@torch.no_grad()
def next_token_probs(model, text):
    """The model's whole output: one probability for every token in the vocabulary."""
    return model(encode(model, text)).logits[0, -1].float().softmax(-1)


def show_top(model, text, k=10):
    p, ids = next_token_probs(model, text).topk(k)
    for pi, i in zip(p.tolist(), ids.tolist()):
        print(f"{pi:6.1%}  {'█' * round(pi * 50):<50} {model.tok.decode(i)!r}")


@torch.no_grad()
def complete(model, text, max_new_tokens=60, temperature=0.0, top_p=1.0, seed=None):
    """Raw text continuation. temperature=0 means greedy: always take the most likely token."""
    if seed is not None:
        torch.manual_seed(seed)
    ids = encode(model, text)
    sampling = dict(do_sample=True, temperature=temperature, top_p=top_p, top_k=0) if temperature > 0 else dict(do_sample=False)
    out = model.generate(ids, max_new_tokens=max_new_tokens, pad_token_id=model.tok.eos_token_id, **sampling)
    return model.tok.decode(out[0, ids.shape[1]:])


def chat_prompt(tok, user, system=None):
    """The text document the harness builds from a conversation."""
    messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": user}]
    return tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)


def chat(model, user, **kw):
    reply = complete(model, chat_prompt(model.tok, user), **kw)
    return reply.split("<|endoftext|>")[0]  # cut at the end-of-turn token


def show_tokens(tok, text):
    ids = tok(text, add_special_tokens=False).input_ids
    print(f"{len(text)} characters -> {len(ids)} tokens")
    print(" | ".join(tok.decode(i) for i in ids))
    print(ids, "\n")


def model_input(model, text, chat=None):
    """The text a local model sees: through its chat template, or raw.
    chat=None decides by the model: aligned models have a chat template, base models don't."""
    if chat is None:
        chat = model.tok.chat_template is not None
    return chat_prompt(model.tok, text) if chat else text


@torch.no_grad()
def attention_viewer(model, text, max_new_tokens=40, k=8, chat=None):
    """Generate a continuation, then show which earlier tokens the model attends to at each step,
    and the k most likely next tokens at that step."""
    prompt_ids = encode(model, model_input(model, text, chat))
    ids = model.generate(prompt_ids, max_new_tokens=max_new_tokens, do_sample=False, pad_token_id=model.tok.eos_token_id)
    out = model(ids, output_attentions=True)
    att = torch.stack(out.attentions)[:, 0].float().cpu()  # layer, head, query, key
    top_p, top_ids = out.logits[0].float().softmax(-1).topk(k)  # next-token candidates at every position
    top_p, top_ids = top_p.cpu().tolist(), top_ids.cpu().tolist()
    toks = [model.tok.decode(i).replace("\n", "⏎") for i in ids[0]]
    start = prompt_ids.shape[1]
    sinks = set(att.mean((0, 1, 2)).topk(3).indices.tolist())  # tokens that soak up attention everywhere

    def show(step, layer, head):
        q = start + step - 1  # the position whose output predicts token q + 1
        a = att[:, :, q, : q + 1]
        a = a.mean(0) if layer == "all" else a[layer]
        a = (a.mean(0) if head == "all" else a[head]).tolist()
        scale = max(a[k] for k in range(q + 1) if k not in sinks)
        spans = []
        for k in range(q + 1):
            style = "border: 1px dashed gray" if k in sinks else f"background: rgba(255, 120, 0, {a[k] / scale:.2f})"
            spans.append(f'<span title="{a[k]:.1%}" style="{style}">{html.escape(toks[k])}</span>')
        spans.append(f' → <b style="border: 2px solid">{html.escape(toks[q + 1])}</b>')
        rows = []
        for p, i in zip(top_p[q], top_ids[q]):
            token = html.escape(repr(model.tok.decode(i)))
            if i == ids[0, q + 1].item():
                token = f"<b>{token}</b> ← generated"
            rows.append(f"<tr><td style='text-align: right'>{p:.1%}</td>"
                        f"<td><div style='width: {200 * p:.0f}px; height: 0.8em; background: rgb(255, 120, 0)'></div></td>"
                        f"<td style='font-family: monospace; text-align: left'>{token}</td></tr>")
        display(HTML("<div style='line-height: 2; font-family: monospace'>" + "".join(spans) + "</div>"
                     "<small>Orange: attention while predicting the boxed token. Dashed: attention sinks, "
                     "left out of the colour scale. Hover for values.</small>"
                     f"<p style='margin-top: 1em'>Most likely next tokens at this step:</p><table>{''.join(rows)}</table>"))

    widgets.interact(show, step=widgets.IntSlider(min=0, max=len(toks) - start - 1, description="token"),
                     layer=["all", *range(att.shape[0])], head=["all", *range(att.shape[1])])


# --- API model (GWDG SAIA) ------------------------------------------------

@functools.cache
def client():
    # a hung request fails after 60 s and is retried, instead of blocking for the default 10 minutes
    return OpenAI(api_key=os.environ["SAIA_API_KEY"], base_url="https://chat-ai.academiccloud.de/v1", timeout=60)


@functools.cache
def api_tokenizer():
    """The API model's tokenizer (no weights), to show its tokens and chat template locally."""
    return AutoTokenizer.from_pretrained("Qwen/Qwen3-30B-A3B-Instruct-2507")


last_request = 0.0


def api(endpoint, **kw):
    """One request to the API model. SAIA allows 10 requests per 10 s per key, so we wait 1 s between requests."""
    global last_request
    time.sleep(max(0, last_request + 1 - time.time()))
    last_request = time.time()
    return endpoint.create(model=API_MODEL, **kw)


def ask(user, max_tokens=300, temperature=0.0, **kw):
    """Chat with the API model. The server applies the chat template."""
    r = api(client().chat.completions, messages=[{"role": "user", "content": user}],
            max_tokens=max_tokens, temperature=temperature, **kw)
    return r.choices[0].message.content


@torch.no_grad()
def show_confidence(text, model=None, max_tokens=60, chat=None):
    """Colour each token of the greedy continuation by the probability the model gave it.
    model=None uses the API model (always through its chat template); a local model follows model_input()."""
    tokens = []  # (token, probability, [(alternative, probability), ...])
    if model is None:
        r = api(client().chat.completions, messages=[{"role": "user", "content": text}], max_tokens=max_tokens,
                temperature=0, logprobs=True, top_logprobs=3)
        for t in r.choices[0].logprobs.content:
            if t.token == "<|im_end|>":
                break
            tokens.append((t.token, math.exp(t.logprob), [(a.token, math.exp(a.logprob)) for a in t.top_logprobs]))
    else:
        ids = encode(model, model_input(model, text, chat))
        out = model.generate(ids, max_new_tokens=max_tokens, do_sample=False, output_scores=True,
                             return_dict_in_generate=True, pad_token_id=model.tok.eos_token_id)
        for step, token_id in enumerate(out.sequences[0, ids.shape[1]:].tolist()):
            if token_id == model.tok.eos_token_id:
                break
            probs = out.scores[step][0].float().softmax(-1)
            top_p, top_ids = probs.topk(3)
            alts = [(model.tok.decode(i), p) for p, i in zip(top_p.tolist(), top_ids.tolist())]
            tokens.append((model.tok.decode(token_id), probs[token_id].item(), alts))
    spans = []
    for token, p, alts in tokens:
        title = ", ".join(f"{a!r} {q:.0%}" for a, q in alts)
        spans.append(f'<span title="{html.escape(title)}" style="background: hsl({120 * p:.0f}, 80%, 80%); color: black">'
                     f'{html.escape(token).replace(chr(10), "⏎<br>")}</span>')
    return HTML("<div style='line-height: 1.8'>" + "".join(spans) + "</div>"
                "<small>green = high probability, red = low. Hover for the top 3 alternatives.</small>")
