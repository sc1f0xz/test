"""argilla/Synth-APIGen-v0.1 (Apache-2.0): APIGen-style synthetic FC built on executable Python functions,
incl. 'no tools provided / cannot be answered' and missing-parameter cases; answers = JSON list of calls or a refusal text.
Gold calls -> verifiers.toolcall.score_calls. Role: prompt-only (no reasoning in answers).
"""
import ast
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "argilla/Synth-APIGen-v0.1"


def convert(row):
    ans = loads_maybe(row.get("answers"))
    calls = [norm_tool_call(c)["function"] for c in ans] if isinstance(ans, list) else []
    return record([{"role": "user", "content": row["query"]}], row.get("tools"), f"{SRC}#{row.get('hash_id', '')[:16]}",
                  {"calls": calls, "refusal_text": ans if isinstance(ans, str) else None, "func_name": row.get("func_name")})


if __name__ == "__main__":
    main(convert)
