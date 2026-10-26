"""PersonalAILab/TaskCraft (MIT): ~41k agentic QA (web/PDF/image) with golden_answer, hop count and a reference
agent trace (search/browse actions + observations, from the authors' agent) and agent/LLM answer scores.
FILTER: drop rows mentioning Wikipedia (~1% per C.md) and non-text modalities (observation_images).
Default prompt-only; USE_TRACE=1 converts the reference trace into tool-call turns (no reasoning; answer from the agent).
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "PersonalAILab/TaskCraft"
USE_TRACE = os.environ.get("USE_TRACE") == "1"


def convert(row):
    if re.search(r"wikipedia", row.get("query", "") + str(row.get("content_identifier", "")), re.I):
        return None
    msgs = [{"role": "user", "content": row["query"]}]
    agent = row.get("ans_from_agent") or {}
    trace = (agent.get("trace") or {}).get("actions") or []
    if any(a.get("observation_images") for a in trace):
        return None
    if USE_TRACE and trace:
        for a in trace:
            args = {k: v for k, v in (a.get("arguments") or {}).items() if v is not None}
            msgs.append({"role": "assistant", "content": "", "tool_calls": [{"type": "function", "function": {"name": a["tool_name"], "arguments": args}}]})
            msgs.append({"role": "tool", "name": a["tool_name"], "content": str(a.get("observation") or "")})
        msgs.append({"role": "assistant", "content": agent.get("answer") or ""})
    tools = infer_tools_from_calls(msgs) if USE_TRACE else None
    return record(msgs, tools, SRC, {"answer": row.get("golden_answer"), "hops": row.get("search_agent_actions_times"),
                                     "agent_score": (row.get("score") or {}).get("agent_answer_score")})


if __name__ == "__main__":
    main(convert)
