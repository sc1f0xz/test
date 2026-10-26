"""nvidia/Nemotron-RL-knowledge-web_search-mcqa (CC-BY-4.0): MCQs with search + browse tool schemas, exact letter
answer, and task_difficulty_qwen3_32b_avg_8 (difficulty signal: low pass rate -> should search / think longer).
Gold -> boxed letter match. Role: prompt-only (RL).
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "nvidia/Nemotron-RL-knowledge-web_search-mcqa"


def convert(row):
    p = row["responses_create_params"]
    msgs = []
    if p.get("instructions"):
        msgs.append({"role": "system", "content": p["instructions"]})
    inp = p.get("input")
    if isinstance(inp, str):
        msgs.append({"role": "user", "content": inp})
    else:
        msgs += [generic_message(m) for m in inp]
    return record(msgs, p.get("tools"), SRC, {"answer": row["expected_answer"],
                                              "qwen3_32b_pass_rate": row.get("task_difficulty_qwen3_32b_avg_8")})


if __name__ == "__main__":
    main(convert)
