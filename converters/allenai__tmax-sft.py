"""allenai/tmax-sft, config ..._thinking_only_success (ODC-BY): terminal-agent trajectories by Qwen3.6-27B
(metadata.source_model) with reasoning_content + OpenAI tool_calls (bash), filtered to verifier success.
Use directly. Prior-turn reasoning kept (multi-step agent SFT); set DROP_PRIOR_REASONING=1 to strip all but last.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "allenai/tmax-sft:thinking_only_success"
DROP_PRIOR = os.environ.get("DROP_PRIOR_REASONING") == "1"


def convert(row):
    msgs = [generic_message(m, parse_inline=False) for m in row["messages"]]
    if DROP_PRIOR:
        last = max(i for i, m in enumerate(msgs) if m["role"] == "assistant")
        for m in msgs[:last]:
            m.pop("reasoning_content", None)
    md = row.get("metadata") or {}
    return record(msgs, row.get("tools"), f"{SRC}#{md.get('trial_name')}",
                  {"task": md.get("task"), "source_model": md.get("source_model"), "has_task_complete": md.get("has_task_complete")})


if __name__ == "__main__":
    main(convert)
