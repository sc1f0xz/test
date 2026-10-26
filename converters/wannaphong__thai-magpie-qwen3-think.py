"""wannaphong/thai-magpie-qwen3-think (CC-BY-3.0 per card): Thai Magpie prompts answered by Qwen3-32B in thinking
mode (<think> inside content). No answer verifier -> use only a slice for Thai-thinking style, or prompt-only.
"""
import ast
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "wannaphong/thai-magpie-qwen3-think"


def convert(row):
    msgs = [generic_message(m) for m in row["messages"]]
    if not any(m.get("reasoning_content") for m in msgs if m["role"] == "assistant"):
        return None
    return record(msgs, None, SRC, None)


if __name__ == "__main__":
    main(convert)
