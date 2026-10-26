"""Render records through the OFFICIAL Qwen3.5 chat template (jinja2, transformers-compatible settings)
and split multi-turn conversations so every assistant turn is trained WITH its thinking.

Why splitting matters (BEST_PRACTICES §A1): the Qwen3.5 template only renders <think> for assistant turns
after the LAST user message; earlier assistant turns are rendered WITHOUT thinking. Training loss on those
earlier turns would teach "answer without thinking". So a conversation with N user turns becomes N samples,
each ending at a different user turn; loss only on the assistant turns after that sample's last user message.

Usage:
  python3 tools/render_chat.py TEMPLATE.jinja records.jsonl out.jsonl [--no-split] [--require-think]
        [--tokenizer tokenizer.json --max-tokens 16384]   (real token count; needs `pip install tokenizers`)
Output rows: {"text": rendered, "train_spans": [[start_char, end_char], ...], "src": ...}
(train_spans = character spans of assistant turns to train on; tokenizers with offsets can map them to tokens)
"""
from __future__ import annotations

import argparse
import json
import sys

import jinja2
from jinja2.sandbox import ImmutableSandboxedEnvironment


def make_env():
    def raise_exception(msg):
        raise jinja2.exceptions.TemplateError(msg)

    def tojson(x, ensure_ascii=False, indent=None, separators=None, sort_keys=False):
        return json.dumps(x, ensure_ascii=ensure_ascii, indent=indent, separators=separators, sort_keys=sort_keys)

    env = ImmutableSandboxedEnvironment(trim_blocks=True, lstrip_blocks=True, extensions=["jinja2.ext.loopcontrols"])
    env.filters["tojson"] = tojson
    env.globals["raise_exception"] = raise_exception
    return env


def split_by_user_turn(messages: list[dict]) -> list[list[dict]]:
    """One sample per user turn: prefix up to (and incl.) the assistant/tool turns that follow that user turn."""
    user_idx = [i for i, m in enumerate(messages) if m["role"] == "user"]
    if len(user_idx) <= 1:
        return [messages]
    out = []
    for k, ui in enumerate(user_idx):
        end = user_idx[k + 1] if k + 1 < len(user_idx) else len(messages)
        sample = messages[:end]
        if any(m["role"] == "assistant" for m in sample[ui + 1:]):
            out.append(sample)
    return out


def render(tpl, messages, tools):
    return tpl.render(messages=messages, tools=tools or None, add_generation_prompt=False, enable_thinking=True)


def train_spans(tpl, messages, tools) -> tuple[str, list[list[int]]]:
    """Character spans of assistant turns after the last user message (prefix-diff method)."""
    full = render(tpl, messages, tools)
    last_user = max(i for i, m in enumerate(messages) if m["role"] == "user")
    spans = []
    for i in range(last_user + 1, len(messages)):
        if messages[i]["role"] != "assistant":
            continue
        before = render(tpl, messages[:i], tools) + "<|im_start|>assistant\n"
        upto = render(tpl, messages[: i + 1], tools)
        if not full.startswith(upto) or not upto.startswith(before):
            raise ValueError(f"template is not prefix-stable at message {i}")
        spans.append([len(before), len(upto)])
    return full, spans


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("template")
    ap.add_argument("inp")
    ap.add_argument("out")
    ap.add_argument("--no-split", action="store_true")
    ap.add_argument("--tokenizer", help="path to tokenizer.json of Qwen3.5-4B for exact token counts")
    ap.add_argument("--max-tokens", type=int, default=0, help="drop samples longer than this (needs --tokenizer)")
    ap.add_argument("--require-think", action="store_true",
                    help="drop samples where any trained assistant turn has empty thinking (recommended for SFT)")
    a = ap.parse_args()
    tpl = make_env().from_string(open(a.template, encoding="utf-8").read())
    tok = None
    if a.tokenizer:
        from tokenizers import Tokenizer  # noqa: PLC0415
        tok = Tokenizer.from_file(a.tokenizer)
    n_in = n_out = n_err = n_nothink = n_long = 0
    with open(a.out, "w", encoding="utf-8") as fo:
        for line in open(a.inp, encoding="utf-8"):
            if not line.strip():
                continue
            n_in += 1
            rec = json.loads(line)
            tools = json.loads(rec.get("tools") or "[]")
            samples = [rec["messages"]] if a.no_split else split_by_user_turn(rec["messages"])
            for msgs in samples:
                try:
                    text, spans = train_spans(tpl, msgs, tools)
                except Exception as e:  # noqa: BLE001
                    n_err += 1
                    print(f"row {n_in}: {type(e).__name__}: {e}", file=sys.stderr)
                    continue
                empty = sum(1 for s, e in spans if "<think>" not in text[s:e]
                            or text[s:e].split("<think>", 1)[1].split("</think>", 1)[0].strip() == "")
                n_nothink += empty
                if not spans or (a.require_think and empty):
                    continue
                n_tok = len(tok.encode(text, add_special_tokens=False).ids) if tok else None
                if a.max_tokens and n_tok is not None and n_tok > a.max_tokens:
                    n_long += 1
                    continue
                fo.write(json.dumps({"text": text, "train_spans": spans, "n_tokens": n_tok, "src": rec.get("src")},
                                    ensure_ascii=False) + "\n")
                n_out += 1
    print(json.dumps({"in": n_in, "out_samples": n_out, "errors": n_err, "trained_turns_without_thinking": n_nothink, "dropped_too_long": n_long,
                      "note": "samples with no trained turns (prompt-only) are never written"}), file=sys.stderr)


if __name__ == "__main__":
    main()
