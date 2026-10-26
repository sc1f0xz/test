"""KodCode/KodCode-V1: question + pytest-style test + test_info (function name) + GPT pass stats.
FILTER: drop rows with benchmark_similarity > 0.79 (near HumanEval/MBPP/BCB/LCB) — set MAX_SIM.
Gold -> verifiers.safe_exec.run_function_tests(code, test). License CC-BY-NC-4.0.
Role: prompt-only (reference solution kept in gold for debugging only).
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "KodCode/KodCode-V1"
MAX_SIM = float(os.environ.get("MAX_SIM", "0.79"))


def convert(row):
    sim = row.get("benchmark_similarity")
    if sim is not None and float(sim) > MAX_SIM:
        return None
    ti = row.get("test_info") or []
    entry = ti[0].get("function_name") if ti else None
    return record([{"role": "user", "content": row["question"]}], None, f"{SRC}#{row.get('question_id')}",
                  {"type": "pytest", "test": row["test"], "entry_point": entry,
                   "reference_solution": row.get("solution"), "gpt_difficulty": row.get("gpt_difficulty"),
                   "benchmark_similarity": sim, "subset": row.get("subset")})


if __name__ == "__main__":
    main(convert)
