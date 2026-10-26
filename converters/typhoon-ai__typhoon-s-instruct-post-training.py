"""typhoon-ai/typhoon-s-instruct-post-training (splits sft / distill; ODC-BY).
Mixture: Thai AutoIF (source=autoif), Tulu-3 subsets (source=ai2-adapt-dev/*), tool-use subsets
(subset_name in single-turn-*, multi-turn, irrelevant; target_tools given).
KEEP env var filters: KEEP=autoif,tool (default) | all. Tulu parts are mostly redundant for us.
Gold: target_tools for tool rows ("irrelevant" => expect no call). AutoIF rows carry the constraint only
in the prompt text (no machine-readable kwargs) -> needs an LLM/heuristic check. No reasoning traces.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "typhoon-ai/typhoon-s-instruct-post-training"
KEEP = set(os.environ.get("KEEP", "autoif,tool").split(","))
THAI_ONLY_AUTOIF = os.environ.get("THAI_ONLY_AUTOIF", "1") == "1"   # only ~39% of AutoIF rows are Thai (D.md)
_THAI = re.compile(r"[\u0E00-\u0E7F]")


def convert(row):
    is_tool = bool(row.get("subset_name"))
    is_autoif = row.get("source") == "autoif"
    if "all" not in KEEP and not ((is_tool and "tool" in KEEP) or (is_autoif and "autoif" in KEEP)):
        return None
    msgs = [generic_message(m) for m in loads_maybe(row["messages"])]
    if is_autoif and THAI_ONLY_AUTOIF and not any(_THAI.search(m["content"]) for m in msgs if m["role"] == "user"):
        return None
    gold = None
    if is_tool:
        gold = {"subset": row["subset_name"], "target_tools": row.get("target_tools"),
                "expect_no_call": row["subset_name"] == "irrelevant"}
    elif is_autoif:
        gold = {"type": "autoif_th", "note": "constraint in prompt text only"}
    return record(msgs, row.get("tools"), f"{SRC}#{row.get('uuid')}", gold)


if __name__ == "__main__":
    main(convert)
