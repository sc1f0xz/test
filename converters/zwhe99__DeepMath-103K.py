"""zwhe99/DeepMath-103K: hard math with final_answer + difficulty (5-9) + 3 R1 solutions.
Role: prompt-only (regenerate with teacher; R1 solutions are not Qwen-style and very long).
Set USE_R1=1 to emit r1_solution_1 as the assistant turn (reasoning only, no <think> split available).
Gold: {"answer", "difficulty"} -> verifiers.math_answer.check
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "zwhe99/DeepMath-103K"
USE_R1 = os.environ.get("USE_R1") == "1"


def convert(row):
    msgs = [{"role": "user", "content": row["question"]}]
    if USE_R1 and row.get("r1_solution_1"):
        msgs.append(assistant_msg(row["r1_solution_1"]))
    return record(msgs, None, SRC, {"answer": row["final_answer"], "difficulty": row.get("difficulty"),
                                    "topic": row.get("topic")})


if __name__ == "__main__":
    main(convert)
