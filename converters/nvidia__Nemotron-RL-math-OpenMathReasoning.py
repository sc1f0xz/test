"""nvidia/Nemotron-RL-math-OpenMathReasoning (CC-BY-4.0): AoPS-derived problems with expected_answer.
Gold -> verifiers.math_answer.check. Role: prompt-only.
"""
import ast
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "nvidia/Nemotron-RL-math-OpenMathReasoning"


def convert(row):
    msgs = [generic_message(m) for m in row["responses_create_params"]["input"]]
    return record(msgs, None, SRC, {"answer": row["expected_answer"]})


if __name__ == "__main__":
    main(convert)
