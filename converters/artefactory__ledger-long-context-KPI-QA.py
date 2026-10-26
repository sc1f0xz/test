"""artefactory/ledger-long-context-KPI-QA (config no_eval): KPI questions over full annual-report text, numeric
gold from SEC XBRL (not wiki). Report text can be far beyond 16K tokens -> MAX_CHARS (default 60000 ≈ 15K tokens)
keeps rows whose report fits; for longer reports cut windows around qrels pages (not implemented here).
Gold: answer_value (float, compare with relative tolerance). Card license: see H.md.
AUDIT (30 full rows) -> registry role "exclude" for the 16K run: every report_full_text was ~215K chars (~55K+
tokens) so 0 rows pass MAX_CHARS; qrels are incomplete (9/30 rows have none; for one query the pages holding the
answer were not in qrels) so qrel-based windowing is unreliable; gold source in these rows is yfinance, not the
report itself (units like $'000 vs raw, definitions may differ).
"""
import ast
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "artefactory/ledger-long-context-KPI-QA:no_eval"
MAX_CHARS = int(os.environ.get("MAX_CHARS", "60000"))


def convert(row):
    text = row.get("report_full_text") or ""
    if len(text) > MAX_CHARS:
        return None
    user = f"{text}\n\n---\nQuestion: {row['query_text']}"
    return record([{"role": "user", "content": user}], None, f"{SRC}#{row.get('query_id')}",
                  {"answer_value": row.get("answer_value"), "kpi": row.get("kpi"), "company": row.get("company_name"),
                   "year": row.get("year"), "rel_tol": 0.01})


if __name__ == "__main__":
    main(convert)
