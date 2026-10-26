"""ThaiLLM/med-tool-use (no license stated): native Thai medical assistant prompts; answer = name of the tool
that should be called, or 'negatives' (= should NOT call any tool; ~62% of train).
Tools are embedded in the system prompt inside <tools>...</tools> (one JSON per line; non-standard schema with
when_to_use / when_not_to_use / parameters list) -> extracted and normalised.
Gold -> first predicted call name must equal expected_tool (or no call). Role: prompt-only (no answers given).
"""
import ast
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "ThaiLLM/med-tool-use"
_TOOLS = re.compile(r"<tools>(.*?)</tools>", re.S)


def _norm(t):
    params = t.get("parameters")
    if isinstance(params, list):  # [{name,type,description,required?}] -> JSON schema
        props, req = {}, []
        for p in params:
            if isinstance(p, dict) and p.get("name"):
                props[p["name"]] = {**json_type(p.get("type")), "description": p.get("description", "")}
                if p.get("required"):
                    req.append(p["name"])
        params = {"type": "object", "properties": props, "required": req}
    desc = t.get("description", "")
    for k in ("when_to_use", "when_not_to_use"):
        if t.get(k):
            desc += f"\n[{k}] {t[k]}"
    return tool(t["name"], desc, params)


def convert(row):
    msgs = [generic_message(m, parse_inline=False) for m in row["prompt"]]
    tools = []
    for m in msgs:
        if m["role"] == "system":
            blk = _TOOLS.search(m["content"])
            if blk:
                for line in blk.group(1).splitlines():
                    t = loads_maybe(line.strip())
                    if isinstance(t, dict) and "name" in t:
                        tools.append(_norm(t))
                m["content"] = _TOOLS.sub("<tools>(see tools field)</tools>", m["content"])
    ans = row.get("answer")
    return record(msgs, tools, SRC, {"expected_tool": None if ans == "negatives" else ans, "expect_no_call": ans == "negatives"})


if __name__ == "__main__":
    main(convert)
