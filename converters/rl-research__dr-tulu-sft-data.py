"""rl-research/dr-tulu-sft-data (ODC-BY): deep-research trajectories with <call_tool name=..>q</call_tool>,
<tool_output>..</tool_output>, <think>, final <answer> with <cite id=..>.
FILTER: drop source 'popqa_tydiqa_en' (Wikipedia-based) and 'browsecomp_*' (BrowseComp-style; contamination risk);
also drops questions that literally ask about a Wikipedia article (seen in the taskcraft subset).
Splits the single assistant blob into assistant(tool_calls) / tool / ... / assistant(answer) turns.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "rl-research/dr-tulu-sft-data"
DROP_SOURCES = {"popqa_tydiqa_en"}
_SEG = re.compile(r"<call_tool\s+name=\"([^\"]+)\"([^>]*)>(.*?)</call_tool>\s*(?:<tool_output>(.*?)</tool_output>)?", re.S)
_ATTR = re.compile(r'(\w+)="([^"]*)"')


def convert(row):
    src = row.get("source", "")
    if src in DROP_SOURCES or src.startswith("browsecomp") or re.search(r"wikipedia", row.get("question", ""), re.I):
        return None
    conv = row["conversations"]
    msgs = [generic_message(m, parse_inline=False) for m in conv if m["role"] != "assistant"]
    blob = next(m["content"] for m in conv if m["role"] == "assistant")
    pos = 0
    for mt in _SEG.finditer(blob):
        before = blob[pos:mt.start()]
        reasoning = "\n".join(t.strip() for t in re.findall(r"<think>(.*?)</think>", before, re.S)) or None
        args = {"query": mt.group(3).strip(), **dict(_ATTR.findall(mt.group(2)))}
        a = {"role": "assistant", "content": "",
             "tool_calls": [{"type": "function", "function": {"name": mt.group(1), "arguments": args}}]}
        if reasoning:
            a["reasoning_content"] = reasoning
        msgs.append(a)
        msgs.append({"role": "tool", "name": mt.group(1), "content": (mt.group(4) or "").strip()})
        pos = mt.end()
    tail = blob[pos:]
    reasoning = "\n".join(t.strip() for t in re.findall(r"<think>(.*?)</think>", tail, re.S)) or None
    ans = re.search(r"<answer>(.*?)(?:</answer>|$)", tail, re.S)
    final = {"role": "assistant", "content": (ans.group(1) if ans else re.sub(r"<think>.*?</think>", "", tail, flags=re.S)).strip()}
    if reasoning:
        final["reasoning_content"] = reasoning
    msgs.append(final)
    names = sorted({c["function"]["name"] for m in msgs for c in m.get("tool_calls", [])})
    tools = [tool(n, "DR Tulu search/browse tool", {"type": "object", "properties": {"query": {"type": "string"}},
                                                     "required": ["query"]}) for n in names]
    return record(msgs, tools, f"{SRC}#{row.get('id')}", {"source": src, "type": row.get("type"), "question": row.get("question")})


if __name__ == "__main__":
    main(convert)
