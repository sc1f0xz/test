"""zake7749/Qwen3.6-35B-A3B-Tool-Calling: Qwen3.6-35B-A3B (thinking) samples that exact-matched the gold
call (name + parsed args). Each row = conversation prefix ending in the chosen assistant turn.
Usable directly (has reasoning). Earlier assistant turns may also carry reasoning. Default keeps it: the official
Qwen3.5 chat_template already renders reasoning only for assistant turns AFTER the last user message (the tool loop)
and strips it before that, so stripping here would make tool-loop turns differ from inference.
DROP_PRIOR_REASONING=1 strips reasoning from every assistant turn except the last. No license tag on the card.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "zake7749/Qwen3.6-35B-A3B-Tool-Calling"
DROP_PRIOR = os.environ.get("DROP_PRIOR_REASONING", "0") == "1"


def convert(row):
    msgs = [generic_message(m, parse_inline=False) for m in row["messages"]]
    last = max(i for i, m in enumerate(msgs) if m["role"] == "assistant")
    if DROP_PRIOR:
        for m in msgs[:last]:
            m.pop("reasoning_content", None)
    gold = {"calls": [c["function"] for c in msgs[last].get("tool_calls", [])]}
    return record(msgs, row.get("tools"), SRC, gold)


if __name__ == "__main__":
    main(convert)
