"""Render records through the OFFICIAL Qwen3.5 chat template (jinja2, transformers-compatible settings)
and split multi-turn conversations so every assistant turn is trained WITH its thinking.

Why splitting matters (BEST_PRACTICES §A1): the Qwen3.5 template only renders <think> for assistant turns
after the LAST user message; earlier assistant turns are rendered WITHOUT thinking. Training loss on those
earlier turns would teach "answer without thinking". So a conversation with N user turns becomes N samples,
each ending at a different user turn; loss only on the assistant turns after that sample's last user message.

Usage:
  python3 tools/render_chat.py TEMPLATE.jinja records.jsonl out.jsonl [--no-split] [--require-think]
        [--tokenizer tokenizer.json --max-tokens 16384]   (real token count; needs `pip install tokenizers`)
Output rows: {"text": rendered, "train_spans": [[start_char, end_char], ...], "src": ..., "images": [...]}
Records with meta.images get {"type":"image"} items in the first user turn (-> <|vision_start|><|image_pad|><|vision_end|>);
the "images" field lists the refs in order, for a VLM collator that loads the pixels (text-only training must skip them).
(train_spans = character spans of assistant turns to train on; tokenizers with offsets can map them to tokens)
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import jinja2
from jinja2.sandbox import ImmutableSandboxedEnvironment

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "converters"))
from common import multimodal_messages  # noqa: E402


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


def has_thinking(turn_text: str) -> bool:
    return "<think>" in turn_text and turn_text.split("<think>", 1)[1].split("</think>", 1)[0].strip() != ""


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
    ap.add_argument("--mask-nothink", action="store_true",
                    help="instead of dropping the sample, remove empty-thinking turns from train_spans (they stay as "
                         "context, no loss); sample kept if >=1 turn with thinking remains. For agent traces where a "
                         "few steps lack reasoning (tmax-sft, zake7749).")
    a = ap.parse_args()
    tpl = make_env().from_string(open(a.template, encoding="utf-8").read())
    tok = None
    if a.tokenizer:
        from tokenizers import Tokenizer  # noqa: PLC0415
        tok = Tokenizer.from_file(a.tokenizer)
    n_in = n_out = n_err = n_nothink = n_long = n_masked = 0
    with open(a.out, "w", encoding="utf-8") as fo:
        for line in open(a.inp, encoding="utf-8"):
            if not line.strip():
                continue
            n_in += 1
            rec = json.loads(line)
            tools = json.loads(rec.get("tools") or "[]")
            messages = multimodal_messages(rec, "hf")  # meta.images -> {"type":"image"} items (no-op without images)
            samples = [messages] if a.no_split else split_by_user_turn(messages)
            for msgs in samples:
                try:
                    text, spans = train_spans(tpl, msgs, tools)
                except Exception as e:  # noqa: BLE001
                    n_err += 1
                    print(f"row {n_in}: {type(e).__name__}: {e}", file=sys.stderr)
                    continue
                nothink = [sp for sp in spans if not has_thinking(text[sp[0]:sp[1]])]
                n_nothink += len(nothink)
                if a.mask_nothink:
                    spans = [sp for sp in spans if sp not in nothink]
                    n_masked += len(nothink)
                elif a.require_think and nothink:
                    continue
                if not spans:
                    continue
                n_tok = len(tok.encode(text, add_special_tokens=False).ids) if tok else None
                if a.max_tokens and n_tok is not None and n_tok > a.max_tokens:
                    n_long += 1
                    continue
                row = {"text": text, "train_spans": spans, "n_tokens": n_tok, "src": rec.get("src")}
                if (rec.get("meta") or {}).get("images"):
                    row["images"] = rec["meta"]["images"]
                fo.write(json.dumps(row, ensure_ascii=False) + "\n")
                n_out += 1
    print(json.dumps({"in": n_in, "out_samples": n_out, "errors": n_err, "trained_turns_without_thinking": n_nothink, "masked_nothink_turns": n_masked,
                      "dropped_too_long": n_long,
                      "note": "samples with no trained turns (prompt-only) are never written"}), file=sys.stderr)


if __name__ == "__main__":
    main()
