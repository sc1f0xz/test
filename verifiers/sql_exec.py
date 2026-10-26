"""Execution-based text-to-SQL check on SQLite (Spider/BIRD/SynSQL style).

check(pred_sql, gold_sql, db_path) -> {"ok", "error"}
Compares result multisets (order-insensitive unless gold has ORDER BY).
Runs on a read-only connection with a step budget (progress handler) to stop
runaway queries; destructive statements are rejected up front.
"""
from __future__ import annotations

import re
import sqlite3
from collections import Counter

_WRITE = re.compile(r"^\s*(insert|update|delete|drop|alter|create|replace|attach|detach|pragma|vacuum)\b", re.I | re.M)


def _exec(sql: str, db_path: str, max_steps: int = 5_000_000):
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    steps = {"n": 0}

    def handler():
        steps["n"] += 1
        return 1 if steps["n"] > max_steps // 1000 else 0

    con.set_progress_handler(handler, 1000)
    try:
        return con.execute(sql).fetchall()
    finally:
        con.close()


def _norm_row(row):
    return tuple(round(v, 6) if isinstance(v, float) else v for v in row)


def check(pred_sql: str, gold_sql: str, db_path: str, allow_empty_gold: bool = False) -> dict:
    """Execution match. A gold query with an EMPTY result cannot tell right from wrong (any query that returns
    nothing would "pass"), so it is reported as not ok unless allow_empty_gold=True."""
    pred_sql = re.sub(r"^```(?:sql)?|```$", "", pred_sql.strip(), flags=re.I | re.M).strip()
    if _WRITE.search(pred_sql):
        return {"ok": False, "error": "write/DDL statement rejected"}
    try:
        p = _exec(pred_sql, db_path)
    except Exception as e:
        return {"ok": False, "error": f"pred: {e}"}
    try:
        g = _exec(gold_sql, db_path)
    except Exception as e:
        return {"ok": False, "error": f"gold: {e}"}
    if not g and not allow_empty_gold:
        return {"ok": False, "error": "gold result empty (uninformative; drop this item)"}
    if re.search(r"\border\s+by\b", gold_sql, re.I):
        ok = [_norm_row(r) for r in p] == [_norm_row(r) for r in g]
    else:
        ok = Counter(map(_norm_row, p)) == Counter(map(_norm_row, g))
    return {"ok": ok, "error": None}
