"""open-athena/*-qwen3.5-122b-*-traces (Harbor/OpenCode/Terminus agent traces of Qwen3.5-122B-A10B, with <think>).
Same schema across ~100 repos: conversations (first user turn is empty -> use 'instruction'),
result ('1.0'/'0.0'), verifier_output. Assistant turns embed <tool_call>{json}</tool_call>;
the following 'user' turn is the tool/environment output -> mapped to role 'tool'.
Tool schemas are not shipped -> inferred from observed calls (marked in description).
KEEP_FAILED=1 keeps result<1 (e.g. for DPO negatives). NO LICENSE on these repos.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = os.environ.get("SRC", "open-athena/nemotron-code-oracle-filtered-qwen3.5-122b-131k-opencode-traces")  # set SRC=open-athena/<sibling repo> when reusing
KEEP_FAILED = os.environ.get("KEEP_FAILED") == "1"


def convert(row):
    result = float(row.get("result") or 0)
    if result < 1.0 and not KEEP_FAILED:
        return None
    conv = row["conversations"]
    msgs, prev_had_call = [], False
    for i, m in enumerate(conv):
        if m["role"] == "user":
            content = m["content"] or (row.get("instruction") or "" if i == 0 else "")
            role = "tool" if prev_had_call else "user"
            msgs.append({"role": role, "content": content})
            prev_had_call = False
        elif m["role"] == "assistant":
            a = assistant_msg(m["content"])
            msgs.append(a)
            prev_had_call = bool(a.get("tool_calls"))
        elif m["role"] == "system":
            msgs.append({"role": "system", "content": m["content"]})
    return record(msgs, infer_tools_from_calls(msgs), f"{SRC}#{row.get('trial_name')}",
                  {"result": result, "task": row.get("task"), "verifier_output_tail": (row.get("verifier_output") or "")[-500:]})


if __name__ == "__main__":
    main(convert)
