"""airesearch/WangchanX-Legal-ThaiCCL-RAG (MIT) — TRAIN split only (test = NitiBench eval).
Thai legal QA with gold law sections (positive_contexts) and expert-checked positive_answer.
Converted to a grounded-answer task: contexts are put in the user turn (RAG style).
Gold: cited sections (law_code/section) for a citation check. Role: prompt-only by default (expert answer has no thinking; kept in gold as reference).
"""
import ast
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "airesearch/WangchanX-Legal-ThaiCCL-RAG:train"
USE_ANSWER = os.environ.get("USE_ANSWER", "0") == "1"   # answers lack thinking -> prompt-only by default


def convert(row):
    ctx = row.get("positive_contexts") or []
    docs = "\n\n".join(f"[{i + 1}] {c['metadata'].get('law_title', '')} มาตรา {c['metadata'].get('section', '')}\n{c['context']}"
                       for i, c in enumerate(ctx))
    msgs = [{"role": "user", "content": f"เอกสารอ้างอิง:\n{docs}\n\nคำถาม: {row['question']}"}]
    if USE_ANSWER and row.get("positive_answer"):
        msgs.append(assistant_msg(row["positive_answer"]))
    gold = {"reference_answer": row.get("positive_answer"), "sections": [{"law_code": c["metadata"].get("law_code"), "section": c["metadata"].get("section")} for c in ctx]}
    return record(msgs, None, SRC, gold)


if __name__ == "__main__":
    main(convert)
