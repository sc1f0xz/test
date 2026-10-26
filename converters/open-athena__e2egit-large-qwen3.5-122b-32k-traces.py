"""open-athena/*-qwen3.5-122b-32k-traces (Terminus-2 harness; Qwen3.5-122B with <think> each turn). NO LICENSE.
Terminus-2 actions are JSON keystroke batches inside assistant text (not function calls) and the following
'user' turn is the terminal output — kept as plain text turns (harness-native format). result=='1.0' only
unless KEEP_FAILED=1. Siblings with the same schema: ghactions-v3, nl2bash-tasks-cleaned-oracle, ...
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "open-athena/e2egit-large-qwen3.5-122b-32k-traces"
KEEP_FAILED = os.environ.get("KEEP_FAILED") == "1"


def convert(row):
    result = float(row.get("result") or 0)
    if result < 1.0 and not KEEP_FAILED:
        return None
    msgs = [generic_message(m) for m in row["conversations"]]
    if msgs and msgs[0]["role"] == "user" and not msgs[0]["content"].strip():
        msgs[0]["content"] = row.get("instruction") or ""
    return record(msgs, None, f"{SRC}#{row.get('trial_name')}", {"result": result, "task": row.get("task")})


if __name__ == "__main__":
    main(convert)
