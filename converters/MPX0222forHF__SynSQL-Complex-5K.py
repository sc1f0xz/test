"""MPX0222forHF/SynSQL-Complex-5K: complex text-to-SQL from SynSQL-2.5M (Apache-2.0); prompt includes schema.
Needs DB files from seeklhy/SynSQL-2.5M databases.zip (~54.5 MB, outside the repo) for execution checking.
Gold -> verifiers.sql_exec.check(pred, gold_sql, <db_dir>/<db_id>/<db_id>.sqlite).
USE_COT=1 emits the dataset's CoT + SQL as assistant (CoT is GPT-style, not Qwen thinking) — default prompt-only.
"""
import ast
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "MPX0222forHF/SynSQL-Complex-5K"
USE_COT = os.environ.get("USE_COT") == "1"


def convert(row):
    msgs = [generic_message(m) for m in row["prompt"]]
    if USE_COT:
        msgs.append(assistant_msg(f"```sql\n{row['sql']}\n```", reasoning=row.get("cot")))
    gt = row["reward_model"]["ground_truth"]
    return record(msgs, None, f"{SRC}#{row.get('extra_info', {}).get('index')}",
                  {"type": "sql_exec", "db_id": gt["db_id"], "sql": gt["sql"], "complexity": row.get("sql_complexity")})


if __name__ == "__main__":
    main(convert)
