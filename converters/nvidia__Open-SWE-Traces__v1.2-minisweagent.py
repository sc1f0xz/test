"""nvidia/Open-SWE-Traces v1.2 / minisweagent (CC-BY-4.0): SWE trajectories; filter metadata.teacher_model.name
(e.g. qwen38_27b = same family as our teacher) and resolved==1. Has reasoning_content + bash tool_calls.
ONLY_RESOLVED=1 (default). MAX_CHARS = cheap pre-filter on ALL text (content + reasoning + tool-call arguments
+ tool schemas); default 56000 ≈ 16K tokens at the measured ~3.5 chars/token of rendered SWE traces.
The authoritative length gate is tools/render_chat.py --tokenizer ... --max-tokens 16384.
AUDIT (30 real rows): 17 resolved, rendered length 16.8K-120K tokens (median ~29K) -> 0/17 fit in 16K.
At 16K context this set yields almost nothing; it is only useful with a 32K+ context run or as a pool to mine
the rare short trajectories from (scan many shards).
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "nvidia/Open-SWE-Traces:v1.2/minisweagent"
ONLY_RESOLVED = os.environ.get("ONLY_RESOLVED", "1") == "1"
MAX_CHARS = int(os.environ.get("MAX_CHARS", "56000"))
TEACHERS = set(filter(None, os.environ.get("TEACHERS", "").split(",")))  # empty = all


def convert(row):
    if ONLY_RESOLVED and int(row.get("resolved") or 0) != 1:
        return None
    teacher = ((row.get("metadata") or {}).get("teacher_model") or {}).get("name")
    if TEACHERS and teacher not in TEACHERS:
        return None
    msgs = [generic_message(m, parse_inline=False) for m in row["messages"]]
    n_chars = len(json.dumps(row.get("tools") or [], ensure_ascii=False)) + sum(
        len(m["content"]) + len(m.get("reasoning_content", ""))
        + sum(len(json.dumps(c["function"]["arguments"], ensure_ascii=False)) for c in m.get("tool_calls", []))
        for m in msgs)
    if n_chars > MAX_CHARS:
        return None
    return record(msgs, row.get("tools"), f"{SRC}#{row.get('trajectory_id')}",
                  {"resolved": row.get("resolved"), "instance_id": row.get("instance_id"), "teacher": teacher,
                   "license_of_repo": row.get("license")})


if __name__ == "__main__":
    main(convert)
