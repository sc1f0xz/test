"""nvidia/Nemotron-RL-Agentic-Indirect-Prompt-Injection-v1 (CC-BY-4.0): 1,272 stateful tool environments
(9 domains) where a tool result carries an injection. Prompt-only/RL: run the policy against 'environment'
(NeMo Gym agent 'indirect_prompt_injection_simple_agent'), reward = attack tool NOT called (trace analysis).
CAVEAT: also require task completion (required_tools called) — otherwise 'do nothing' gets full reward.
"""
import ast
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "nvidia/Nemotron-RL-Agentic-Indirect-Prompt-Injection-v1"


def convert(row):
    p = row["responses_create_params"]
    msgs = [generic_message(m) for m in p["input"]]
    inj = loads_maybe(row.get("injection"))
    if isinstance(inj, str):
        try:
            inj = ast.literal_eval(inj)
        except (ValueError, SyntaxError):
            pass
    req = row.get("required_tools")
    if isinstance(req, str):
        try:
            req = ast.literal_eval(req)
        except (ValueError, SyntaxError):
            pass
    return record(msgs, p.get("tools"), f"{SRC}#{row.get('id')}",
                  {"type": "ipi_env", "domain": row.get("domain"), "attack_category": row.get("attack_category"),
                   "forbidden_tool": row.get("target_tool"), "required_tools": req, "injection": inj,
                   "environment": row.get("environment")})


if __name__ == "__main__":
    main(convert)
