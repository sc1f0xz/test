"""nvidia/When2Call (configs train_sft / train_pref; NEVER test — it is built from BFCL).

Row: tools [json str], messages [user, assistant]  (train_pref: + chosen_response/rejected_response)
Gold: expected behaviour — "tool_call" (+calls), "request_for_info", or "cannot_answer/direct".
Role: prompt-only (assistant text has no reasoning) -> teacher regenerates thinking, verify with
verifiers.toolcall.score_calls (calls) or a behaviour classifier (ask vs refuse).
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "nvidia/When2Call"
_TC = re.compile(r"<TOOLCALL>(.*?)</TOOLCALL>", re.S)


def _behaviour(text: str):
    m = _TC.search(text or "")
    if m:
        calls = loads_maybe(m.group(1).strip()) or []
        return "tool_call", [norm_tool_call(c) for c in (calls if isinstance(calls, list) else [calls])]
    if "<tool_call>" in (text or ""):
        return "tool_call", parse_inline_tool_calls(text)[1]
    if (text or "").rstrip().endswith("?"):
        return "request_for_info", []
    return "no_tool_call", []


def convert(row):
    msgs = row["messages"]
    final = row.get("chosen_response") or (msgs[-1] if msgs and msgs[-1]["role"] == "assistant" else None)
    history = [m for m in msgs if m is not final]
    if msgs and msgs[-1]["role"] == "assistant" and final is not msgs[-1]:
        history = msgs[:-1]
    kind, calls = _behaviour(final["content"] if final else "")
    out = [generic_message(m) for m in history]
    if final is not None:
        out.append(assistant_msg(_TC.sub("", final["content"]).strip(), tool_calls=calls, parse_inline=False))
    return record(out, row.get("tools"), SRC, {"behaviour": kind, "calls": calls})


if __name__ == "__main__":
    main(convert)
