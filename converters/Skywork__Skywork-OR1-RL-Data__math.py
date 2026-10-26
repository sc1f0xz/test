"""Skywork/Skywork-OR1-RL-Data (split math): competition math, ground_truth list, model_difficulty
(0-16 = #correct of 16 samples for R1-Distill 1.5B/7B/32B). Decontaminated vs AIME24/25 per card. License not stated.
Gold -> verifiers.math_answer.check against any ground_truth. Role: prompt-only.
"""
import ast
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "Skywork/Skywork-OR1-RL-Data:math"


def convert(row):
    gt = loads_maybe(row["reward_model"]["ground_truth"])
    return record([generic_message(m) for m in row["prompt"]], None, f"{SRC}#{row.get('extra_info', {}).get('index')}",
                  {"answers": gt if isinstance(gt, list) else [gt], "model_difficulty": row.get("extra_info", {}).get("model_difficulty"),
                   "data_source": row.get("data_source")})


if __name__ == "__main__":
    main(convert)
