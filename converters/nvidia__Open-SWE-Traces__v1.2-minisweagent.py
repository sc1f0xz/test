"""nvidia/Open-SWE-Traces v1.2 / minisweagent (CC-BY-4.0): SWE trajectories; filter metadata.teacher_model.name
(e.g. qwen38_27b = same family as our teacher) and resolved==1. Has reasoning_content + bash tool_calls.
ONLY_RESOLVED=1 (default). MAX_CHARS (default 64000 ≈ 16K tokens) drops longer trajectories.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "nvidia/Open-SWE-Traces:v1.2/minisweagent"
ONLY_RESOLVED = os.environ.get("ONLY_RESOLVED", "1") == "1"
MAX_CHARS = int(os.environ.get("MAX_CHARS", "64000"))
TEACHERS = set(filter(None, os.environ.get("TEACHERS", "").split(",")))  # empty = all


def convert(row):
    if ONLY_RESOLVED and int(row.get("resolved") or 0) != 1:
        return None
    teacher = ((row.get("metadata") or {}).get("teacher_model") or {}).get("name")
    if TEACHERS and teacher not in TEACHERS:
        return None
    msgs = [generic_message(m, parse_inline=False) for m in row["messages"]]
    if sum(len(m["content"]) + len(m.get("reasoning_content", "")) for m in msgs) > MAX_CHARS:
        return None
    return record(msgs, row.get("tools"), f"{SRC}#{row.get('trajectory_id')}",
                  {"resolved": row.get("resolved"), "instance_id": row.get("instance_id"), "teacher": teacher,
                   "license_of_repo": row.get("license")})


if __name__ == "__main__":
    main(convert)
