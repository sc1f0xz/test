"""zjunlp/DataMind-12K (MIT): data-analysis agent trajectories (Python + SQL) with <think> and ground truth.
TRAIN split only (test = BIRD/DAEval/TableBench evals). Gold = reward_model.ground_truth.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "zjunlp/DataMind-12K"


def convert(row):
    msgs = [generic_message(m) for m in (row.get("trajectory") or row["prompt"])]
    gt = (row.get("reward_model") or {}).get("ground_truth") or {}
    return record(msgs, None, f"{SRC}#{row.get('task_id')}",
                  {"answer": gt.get("ground_truth"), "db_id": row.get("db_id"), "data_source": row.get("data_source")})


if __name__ == "__main__":
    main(convert)
