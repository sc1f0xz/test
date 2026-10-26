"""rl-research/dr-tulu-rl-data (ODC-BY): real long-form research queries (SearchArena / OpenScholar) with weighted
rubrics (GPT-4.1-written) for rubric-reward RL of a citing search agent. Gold = rubrics (needs an LLM judge).
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "rl-research/dr-tulu-rl-data"


def convert(row):
    gt = loads_maybe(row.get("ground_truth")) or {}
    return record([generic_message(m) for m in row["messages"]], None, SRC,
                  {"type": "rubric", "rubrics": gt.get("rubrics") if isinstance(gt, dict) else gt,
                   "question_type": row.get("question_type"), "dataset": row.get("dataset")})


if __name__ == "__main__":
    main(convert)
