"""Lecture 2: tool calling, first by hand, then through the API's tools field.

by_hand(): we write the chat document ourselves and send it to the raw /completions endpoint. The system
prompt describes a calculator in plain words. When the model writes a tool call, the script computes the
result, pastes it into the document, and lets the model continue.
native(): the same loop through /chat/completions with tools=[...]. The server writes the tool description
into the document and parses the call for us. show_template() prints the document the server builds.

Run from the repo root: .venv/bin/python demos/tool_loop.py
"""
import json
import re
import sys

sys.path.insert(0, ".")
from llm_helpers import api, api_tokenizer, client

QUESTION = "What is 1234567 * 7654321?"
SYSTEM = ('You can use a calculator. To use it, write <tool_call>{"name": "calc", "arguments": {"expression": "..."}}'
          "</tool_call> and stop. The result will be given to you.")


def calc(expression):
    if not re.fullmatch(r"[\d\s+\-*/().]+", expression):  # only arithmetic: never eval text from a model unchecked
        return "error: only numbers and + - * / ( ) are allowed"
    return str(eval(expression))


def by_hand(question=QUESTION):
    doc = (f"<|im_start|>system\n{SYSTEM}<|im_end|>\n<|im_start|>user\n{question}<|im_end|>\n<|im_start|>assistant\n")
    for _ in range(5):
        r = api(client().completions, prompt=doc, max_tokens=200, temperature=0, stop=["</tool_call>", "<|im_end|>"])
        text = r.choices[0].text
        doc += text
        if "<tool_call>" not in text:
            return doc  # no tool call: the model has answered
        call = json.loads(text.split("<tool_call>")[1])
        result = calc(**call["arguments"])
        doc += (f"</tool_call><|im_end|>\n<|im_start|>user\n<tool_response>\n{result}\n</tool_response><|im_end|>\n"
                "<|im_start|>assistant\n")
    return doc


TOOLS = [{"type": "function", "function": {
    "name": "calc", "description": "Evaluate an arithmetic expression exactly.",
    "parameters": {"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]}}}]


def native(question=QUESTION, tools=TOOLS, functions={"calc": calc}):
    """The agent loop: call the model, run every tool call it makes, append the results, repeat until it answers."""
    messages = [{"role": "user", "content": question}]
    for _ in range(5):
        msg = api(client().chat.completions, messages=messages, tools=tools, max_tokens=300, temperature=0).choices[0].message
        messages.append(msg.model_dump(exclude_none=True))
        if not msg.tool_calls:
            return messages
        for c in msg.tool_calls:
            result = functions[c.function.name](**json.loads(c.function.arguments))
            messages.append({"role": "tool", "tool_call_id": c.id, "content": str(result)})
    return messages


def show_template(messages, tools=TOOLS):
    """The document the server builds from messages and tools (Qwen's template, rendered locally)."""
    msgs = [{**m, "tool_calls": [{"type": "function", "function": {
        "name": c["function"]["name"], "arguments": json.loads(c["function"]["arguments"])}} for c in m["tool_calls"]]}
        if m.get("tool_calls") else m for m in messages]
    print(api_tokenizer().apply_chat_template(msgs, tools=tools, tokenize=False))


if __name__ == "__main__":
    print("Without a tool:", api(client().chat.completions, messages=[{"role": "user", "content": QUESTION}],
                                max_tokens=100, temperature=0).choices[0].message.content)
    print("Correct:", 1234567 * 7654321)
    print("\n=== By hand, raw /completions ===\n" + by_hand())
    print("\n=== Native tools field ===")
    messages = native()
    for m in messages:
        print(m)
    print("\n=== The document the server builds ===")
    show_template(messages)
