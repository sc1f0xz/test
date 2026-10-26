"""MiniMaxAI/SynLogic: 35 logic-puzzle tasks with programmatic verifiers (configs easy/hard).
Gold = task name + game_data (the official verifier from github.com/MiniMax-AI/SynLogic consumes it).
Note: many prompts are Chinese; reward_model.answer can be empty (verifier checks constraints, not a string).
Role: prompt-only.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "MiniMaxAI/SynLogic"


def convert(row):
    msgs = [generic_message(m) for m in row["prompt"]]
    gd = loads_maybe((row.get("extra_info") or {}).get("game_data_str"))
    return record(msgs, None, SRC, {"task": row.get("data_source"), "answer": (row.get("reward_model") or {}).get("answer"),
                                    "game_data": gd})


if __name__ == "__main__":
    main(convert)
