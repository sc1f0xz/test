"""Convert mini-swe-agent (v2.x, trajectory_format "mini-swe-agent-1.1") runs into our record format.

Checked against mini-swe-agent 2.4.6 source: a run dir holds <instance_id>/<instance_id>.traj.json with
  {"info": {"exit_status", "submission", ...}, "messages": [...], "trajectory_format": "mini-swe-agent-1.1"}
messages = system, user (task), then assistant (litellm message.model_dump(): content, tool_calls with JSON-string
arguments, reasoning_content if the server returned it) and role "tool" observations; a format error inserts an
extra role "user" message; the run ends with a role "exit" message. The bash tool schema is fixed (BASH_TOOL).

Filters (BEST_PRACTICES §D): exit_status == Submitted; resolved according to the harness report (--resolved);
no format-error turns (extra user messages) unless --allow-format-errors; keep the SHORTEST passing trajectory per
instance across all run dirs. Length gate = tools/render_chat.py --max-tokens (not here).

  python3 tools/convert_minisweagent.py OUT.jsonl RUN_DIR [RUN_DIR ...] --resolved REPORT [--keep-unresolved]

REPORT = harness output listing resolved instance ids: a JSON with any list-valued key containing "resolved"
(e.g. "resolved_ids"), a JSON {instance_id: {"resolved": true}}, or a text file with one id per line.
!! If the script reports that no assistant turn has reasoning_content, the server/litellm did not pass thinking
through (check vLLM --reasoning-parser) -> the data would train "no thinking"; fix that before generating more.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "converters"))
from common import generic_message, record, validate_record  # noqa: E402

SRC = "mini-swe-agent"
BASH_TOOL = {"type": "function", "function": {
    "name": "bash", "description": "Execute a bash command",
    "parameters": {"type": "object", "properties": {"command": {"type": "string", "description": "The bash command to execute"}},
                   "required": ["command"]}}}


def load_resolved(path: str) -> set[str]:
    text = open(path, encoding="utf-8").read()
    try:
        d = json.loads(text)
    except json.JSONDecodeError:
        return {l.strip() for l in text.splitlines() if l.strip()}
    ids: set[str] = set()
    if isinstance(d, list):
        return {str(x) for x in d}
    for k, v in d.items():
        if "resolved" in k.lower() and "unresolved" not in k.lower() and isinstance(v, list):
            ids |= {str(x) for x in v}
        elif isinstance(v, dict) and v.get("resolved") is True:
            ids.add(k)
    return ids


def convert_traj(traj: dict, instance_id: str, resolved: bool | None, allow_format_errors: bool) -> tuple[dict | None, str]:
    info = traj.get("info") or {}
    if info.get("exit_status") != "Submitted":
        return None, f"exit_status={info.get('exit_status')}"
    raw = [m for m in traj.get("messages", []) if m.get("role") != "exit"]
    msgs = []
    n_user = 0
    for m in raw:
        m = {k: v for k, v in m.items() if k != "extra"}
        if m.get("role") == "user":
            n_user += 1
            if n_user > 1 and not allow_format_errors:
                return None, "format_error_turn"
        msgs.append(generic_message(m, parse_inline=False))
    if not any(m["role"] == "assistant" for m in msgs):
        return None, "no_assistant"
    rec = record(msgs, [BASH_TOOL], f"{SRC}#{instance_id}",
                 {"instance_id": instance_id, "resolved": resolved, "submission": info.get("submission", "")})
    return rec, "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("run_dirs", nargs="+")
    ap.add_argument("--resolved", required=True, help="harness report with resolved instance ids")
    ap.add_argument("--keep-unresolved", action="store_true", help="also emit unresolved ones (e.g. DPO negatives)")
    ap.add_argument("--allow-format-errors", action="store_true")
    a = ap.parse_args()
    resolved_ids = load_resolved(a.resolved)
    best: dict[str, tuple[int, dict]] = {}
    stats = Counter()
    for d in a.run_dirs:
        for path in sorted(glob.glob(os.path.join(d, "*", "*.traj.json"))):
            iid = os.path.basename(path)[: -len(".traj.json")]
            stats["traj"] += 1
            ok = iid in resolved_ids
            if not ok and not a.keep_unresolved:
                stats["unresolved"] += 1
                continue
            rec, why = convert_traj(json.load(open(path, encoding="utf-8")), iid, ok, a.allow_format_errors)
            if rec is None:
                stats[why.split("=")[0]] += 1
                continue
            errs = validate_record(rec)
            if errs:
                stats["invalid"] += 1
                print(f"invalid {path}: {errs[:2]}", file=sys.stderr)
                continue
            asst = [m for m in rec["messages"] if m["role"] == "assistant"]
            stats["assistant_turns"] += len(asst)
            stats["assistant_turns_with_reasoning"] += sum(1 for m in asst if (m.get("reasoning_content") or "").strip())
            size = len(json.dumps(rec["messages"], ensure_ascii=False))
            key = f"{iid}|{ok}"
            if key not in best or size < best[key][0]:
                best[key] = (size, rec)
    with open(a.out, "w", encoding="utf-8") as fo:
        for _, rec in best.values():
            fo.write(json.dumps(rec, ensure_ascii=False) + "\n")
    stats["written_(shortest_per_instance)"] = len(best)
    print(json.dumps(stats), file=sys.stderr)
    if stats["assistant_turns"] and not stats["assistant_turns_with_reasoning"]:
        print("WARNING: no assistant turn has reasoning_content -> thinking was not captured "
              "(check vLLM --reasoning-parser qwen3 / litellm). Do not train on this as thinking data.", file=sys.stderr)


if __name__ == "__main__":
    main()
