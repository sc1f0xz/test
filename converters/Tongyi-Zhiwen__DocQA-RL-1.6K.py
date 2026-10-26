"""Tongyi-Zhiwen/DocQA-RL-1.6K: long-document QA RLVR (financial / MC) with ground_truth. TRAIN split.
FILTER: drop data_source containing 'musique' (Wikipedia-based). Gold -> exact/numeric match (math_answer.is_equivalent)
or option letter. Role: prompt-only.
"""
import ast
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "Tongyi-Zhiwen/DocQA-RL-1.6K"


def convert(row):
    if "musique" in (row.get("data_source") or "").lower():
        return None
    return record([generic_message(m) for m in row["prompt"]], None, f"{SRC}#{row.get('extra_info', {}).get('index')}",
                  {"answer": row["reward_model"]["ground_truth"], "data_source": row.get("data_source"),
                   "input_length": row.get("extra_info", {}).get("input_length")})


if __name__ == "__main__":
    main(convert)
