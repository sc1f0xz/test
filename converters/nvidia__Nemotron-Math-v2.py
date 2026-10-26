"""nvidia/Nemotron-Math-v2 (splits low / medium / high_partNN): gpt-oss-120b solutions at a given reasoning effort
+ metadata pass rates for every effort x tool setting -> ready difficulty label for adaptive length.
Default prompt-only (problem + expected_answer + pass rates); USE_TRACE=1 also emits the gpt-oss trace.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "nvidia/Nemotron-Math-v2"
USE_TRACE = os.environ.get("USE_TRACE") == "1"


def convert(row):
    msgs = [generic_message(m) for m in row["messages"] if m["role"] != "assistant" or USE_TRACE]
    md = row.get("metadata") or {}
    rates = {k: v.get("accuracy") for k, v in md.items() if isinstance(v, dict) and "accuracy" in v}
    return record(msgs, None, f"{SRC}#{row.get('uuid')}", {"answer": row["expected_answer"], "pass_rates": rates,
                                                           "data_source": row.get("data_source")})


if __name__ == "__main__":
    main(convert)
