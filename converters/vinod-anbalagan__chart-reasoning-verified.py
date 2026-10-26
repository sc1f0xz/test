"""vinod-anbalagan/chart-reasoning-verified (CC-BY-4.0): programmatically generated charts with verified answers,
evidence values and abstention cases. Image referenced via meta.images (repo images/<id>.png); any "<image>"
placeholder in the raw prompt is removed (use common.multimodal_messages() to attach the real image).
'completion' is a short structured answer (Answer/Evidence/Reasoning) — no thinking -> prompt-only by default.
"""
import ast
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "vinod-anbalagan/chart-reasoning-verified"
USE_COMPLETION = os.environ.get("USE_COMPLETION") == "1"


def convert(row):
    q = row.get("prompt") or row["question"]
    msgs = [{"role": "user", "content": IMAGE_PLACEHOLDER_RE.sub("", q).strip()}]
    if USE_COMPLETION:
        msgs.append(assistant_msg(row["completion"]))
    rec = record(msgs, None, f"{SRC}#{row.get('id')}",
                 {"answer": row.get("answer"), "evidence": row.get("evidence"), "values": loads_maybe(row.get("values")),
                  "task_family": row.get("task_family")})
    rec["meta"] = {"images": [row.get("id")]}
    return rec


if __name__ == "__main__":
    main(convert)
