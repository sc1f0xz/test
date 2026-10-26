"""PrimeIntellect/INTELLECT-3-RL (config math): question + answer + avg@8 of Qwen3-4B (thinking/instruct).
The pass-rate columns are a ready-made difficulty signal for a 4B model (adaptive-length budgets, curriculum).
Gold -> verifiers.math_answer.check. Role: prompt-only.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "PrimeIntellect/INTELLECT-3-RL:math"


def convert(row):
    pr = {k: v for k, v in row.items() if k.startswith("avg@")}
    return record([{"role": "user", "content": row["question"]}], None, SRC, {"answer": row["answer"], "pass_rates": pr})


if __name__ == "__main__":
    main(convert)
