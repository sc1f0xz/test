"""Format gate for thinking-first outputs (Qwen3.x chat template conventions).

check(text) -> {"ok", "think_tokens_approx", "answer", "tool_calls", "errors"}
Rules:
  * exactly one <think>...</think> block, at the very start
  * non-empty reasoning (thinking is always on for our model)
  * after </think>: either a final answer, or one or more <tool_call>{json}</tool_call>
  * tool call JSON must have "name" and object "arguments"
Also accepts Qwen3.5-style XML calls: <tool_call><function=NAME><parameter=K>V</parameter>...</function></tool_call>
"""
from __future__ import annotations

import json
import re

_THINK = re.compile(r"^\s*<think>(.*?)</think>", re.S)
_CALL = re.compile(r"<tool_call>\s*(.*?)\s*</tool_call>", re.S)
_XML_FN = re.compile(r"<function=([^>\s]+)>(.*?)</function>", re.S)
_XML_PARAM = re.compile(r"<parameter=([^>\s]+)>\s*(.*?)\s*</parameter>", re.S)


def _parse_call(body: str):
    m = _XML_FN.search(body)
    if m:
        # every byte inside <function=...> must belong to a closed <parameter=...>...</parameter> block;
        # otherwise llama.cpp / vLLM parsers reject or mis-parse the call (e.g. a missing </parameter>)
        if _XML_PARAM.sub("", m.group(2)).strip() or body[m.end():].strip():
            raise ValueError("malformed <parameter> block or text after </function>")
        args = {}
        for k, v in _XML_PARAM.findall(m.group(2)):
            try:
                args[k] = json.loads(v)
            except json.JSONDecodeError:
                args[k] = v
        return {"name": m.group(1), "arguments": args}
    obj = json.loads(body)
    args = obj.get("arguments", {})
    if isinstance(args, str):
        args = json.loads(args)
    if "name" not in obj or not isinstance(args, dict):
        raise ValueError("call needs name + object arguments")
    return {"name": obj["name"], "arguments": args}


def check(text: str, min_think_chars: int = 1) -> dict:
    errors = []
    m = _THINK.match(text)
    if not m:
        return {"ok": False, "errors": ["missing leading <think>...</think>"],
                "think_tokens_approx": 0, "answer": None, "tool_calls": []}
    think = m.group(1).strip()
    if len(think) < min_think_chars:
        errors.append("empty thinking")
    rest = text[m.end():]
    if "<think>" in rest:
        errors.append("multiple <think> blocks")
    calls = []
    for body in _CALL.findall(rest):
        try:
            calls.append(_parse_call(body))
        except (ValueError, json.JSONDecodeError) as e:
            errors.append(f"bad tool_call: {e}")
    answer = _CALL.sub("", rest).strip()
    if not calls and not answer:
        errors.append("no answer and no tool call after </think>")
    return {"ok": not errors, "errors": errors, "think_tokens_approx": len(think) // 4,
            "answer": answer or None, "tool_calls": calls}
