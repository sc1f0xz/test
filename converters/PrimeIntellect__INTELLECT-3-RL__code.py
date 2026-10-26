"""PrimeIntellect/INTELLECT-3-RL (config code): question + info.tests {inputs, outputs, fn_name?}.
fn_name present -> call-based (LeetCode style: call fn with parsed inputs); else stdin/stdout.
Gold -> verifiers.safe_exec.run_stdio_tests (stdio) or a call harness (function). Role: prompt-only.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "PrimeIntellect/INTELLECT-3-RL:code"


def convert(row):
    info = loads_maybe(row["info"])
    tests = loads_maybe(info.get("tests"))
    kind = "function" if tests.get("fn_name") else "stdio"
    pr = {k: v for k, v in row.items() if k.startswith("avg@")}
    return record([{"role": "user", "content": row["question"]}], None, SRC,
                  {"type": kind, "fn_name": tests.get("fn_name"), "inputs": tests["inputs"],
                   "outputs": tests["outputs"], "source": info.get("source"), "pass_rates": pr})


if __name__ == "__main__":
    main(convert)
