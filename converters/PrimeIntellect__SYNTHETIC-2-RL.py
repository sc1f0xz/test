"""PrimeIntellect/SYNTHETIC-2-RL (no license stated): mixed verifiable tasks (code/math/reasoning-gym/format/JSON/
code-output prediction) with avg reward of Qwen3-4B / Qwen3-32B / R1-0528-Qwen3-8B.
FILTER: drops problem_id starting with 'ifeval' (IFEval-derived => benchmark contamination).
Gold = verification_info (task-specific: test_cases / ground_truth / schema) + pass rates. Role: prompt-only.
"""
import ast
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "PrimeIntellect/SYNTHETIC-2-RL"


def convert(row):
    pid = row.get("problem_id", "")
    if pid.lower().startswith("ifeval"):
        return None
    vi = loads_maybe(row.get("verification_info"))
    if isinstance(vi, dict) and isinstance(vi.get("test_cases"), str):
        vi["test_cases"] = loads_maybe(vi["test_cases"])
    pr = {k: v for k, v in row.items() if k.endswith("_avg_reward")}
    return record([{"role": "user", "content": row["prompt"]}], None, f"{SRC}#{pid}",
                  {"task_type": pid.rsplit("_", 1)[0], "verification_info": vi, "pass_rates": pr})


if __name__ == "__main__":
    main(convert)
