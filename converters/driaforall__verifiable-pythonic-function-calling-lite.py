"""driaforall/verifiable-pythonic-function-calling-lite (Apache-2.0): Pythonic function calling with executable
mock_functions + checklist (expected functions called and expected returned values).
Answers are Python code blocks (not JSON tool calls) -> we keep them as plain assistant text; verification =
exec the code against mock_functions in verifiers.safe_exec and compare checklist.values.
Role: prompt-only for JSON-tool-call training (convert the mock function signatures to JSON tools via teacher run),
or use directly to teach code-as-action.
"""
import ast
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "driaforall/verifiable-pythonic-function-calling-lite"


def convert(row):
    msgs = [generic_message(m, parse_inline=False) for m in row["conversations"]]
    tools = row.get("tools")
    tools = tools if isinstance(loads_maybe(tools), (list, dict)) else None
    return record(msgs, tools, f"{SRC}#{row.get('id')}",
                  {"type": "pythonic_exec", "call_type": row.get("type"), "mock_functions": row.get("mock_functions"),
                   "checklist": {"functions": row["checklist"]["functions"], "values": loads_maybe(row["checklist"]["values"])}})


if __name__ == "__main__":
    main(convert)
