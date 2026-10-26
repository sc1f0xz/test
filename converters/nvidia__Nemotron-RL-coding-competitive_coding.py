"""nvidia/Nemotron-RL-coding-competitive_coding: stdin/stdout problems + unit_tests (CC-BY-SA-4.0).
Gold -> verifiers.safe_exec.run_stdio_tests(code, zip(inputs, outputs)). Role: prompt-only.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "nvidia/Nemotron-RL-coding-competitive_coding"


def convert(row):
    msgs = [generic_message(m) for m in row["responses_create_params"]["input"]]
    ut = row["verifier_metadata"]["unit_tests"]
    return record(msgs, None, f"{SRC}#{row.get('hash_id')}",
                  {"type": "stdio", "inputs": ut["inputs"], "outputs": ut["outputs"], "source": row.get("source")})


if __name__ == "__main__":
    main(convert)
