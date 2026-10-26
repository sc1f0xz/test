"""MadeAgents/xlam-irrelevance-7.5k: query + tools where the right tool was removed.
Gold: no tool call (answers == []). Role: prompt-only (teacher explains it cannot do it with given tools).
Verify: verifiers.toolcall.score_calls(pred, []) -> no_call_correct.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "MadeAgents/xlam-irrelevance-7.5k"


def convert(row):
    gold = loads_maybe(row.get("answers")) or []
    return record([{"role": "user", "content": row["query"]}], row["tools"], SRC, {"calls": gold})


if __name__ == "__main__":
    main(convert)
