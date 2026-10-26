"""casey-martin/Seal-Tools (MIT): tool calling incl. NESTED calls (outputs referenced as API_call_k in later args).
Prompt embeds api_list (python literal) + task_instruction; answer = python-literal list of
{'api','parameters','responses'}. We parse api_list -> JSON tools, answer -> gold calls (responses kept for nesting).
Role: prompt-only (rewrite into a natural user turn = task_instruction).
"""
import ast
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "casey-martin/Seal-Tools"
_API = re.compile(r"api_list\s*=\s*(\[.*?\])\s*\ntask_instruction", re.S)
_TASK = re.compile(r'task_instruction\s*=\s*"(.*?)"\s*\nOutput', re.S)


def convert(row):
    prompt = next(m["value"] for m in row["conversations"] if m["from"] == "human")
    answer = next((m["value"] for m in row["conversations"] if m["from"] == "gpt"), "[]")
    tools = []
    m = _API.search(prompt)
    if m:
        for a in ast.literal_eval(m.group(1)):
            params = {"type": "object", "properties": {k: {**json_type(v.get("type")), "description": v.get("description", "")}
                                                       for k, v in (a.get("parameters") or {}).items()},
                      "required": a.get("required", [])}
            tools.append(tool(a["api_name"], a.get("api_description", ""), params))
    t = _TASK.search(prompt)
    user = t.group(1) if t else prompt
    calls = [{"name": c["api"], "arguments": c.get("parameters", {}), "responses": c.get("responses", [])}
             for c in ast.literal_eval(answer)]
    return record([{"role": "user", "content": user}], tools, f"{SRC}#{row.get('id')}",
                  {"calls": calls, "nested": any(str(v).startswith("API_call_") for c in calls for v in c["arguments"].values())})


if __name__ == "__main__":
    main(convert)
