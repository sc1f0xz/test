"""Select high-quality OpenHands SWE trajectories (nebius/SWE-rebench-openhands-trajectories and same-schema sets)
and convert them to our record format.

Why these filters (see BEST_PRACTICES.md §D):
  * train only on verified successes (OpenHands LM / SWE-Gym recipe)          -> resolved == 1, exit_status == submit
  * the "reproduce first, then fix, then verify" workflow (OpenHands prompt)  -> gen_tests_correct >= 1
                                                                                + repro-before-fix + verify-after-fix
  * shortest-path trajectories (SWE-TRACE)                                     -> keep the shortest passing one per instance
  * fit the training context (16K)                                             -> token estimate after observation trimming

Usage:
  python3 tools/filter_swe_trajectories.py IN.(jsonl|parquet) OUT.jsonl [--max-tokens 16000] [--min-gen-tests 1]
        [--obs-chars 2500] [--keep-think-tool] [--no-dedup] [--stats-only]
IN rows must have: trajectory, tools, resolved, exit_status, gen_tests_correct, pred_passes_gen_tests, instance_id.
Reading parquet needs pandas + pyarrow; jsonl needs nothing.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "converters"))
from common import record, validate_record  # noqa: E402

SRC = "nebius/SWE-rebench-openhands-trajectories"
TEST_PATH = re.compile(r"(^|/)(test_[^/]*\.py|[^/]*_test\.py|tests?/|reproduc[^/]*|repro[^/]*|debug[^/]*\.py|verify[^/]*\.py)", re.I)
RUN_CHECK = re.compile(r"\b(pytest|python[0-9.]*\s+(-m\s+pytest\s+)?\S*(test|reproduc|repro|debug|verify)\S*\.py|tox|nosetests|unittest|make\s+test|npm\s+test|go\s+test|cargo\s+test)", re.I)
THINK_ACK = re.compile(r"^\s*Your thought has been logged\.?\s*$", re.I)


def _args(call) -> dict:
    a = call["function"].get("arguments")
    if isinstance(a, str):
        try:
            a = json.loads(a) if a.strip() else {}
        except json.JSONDecodeError:
            a = {"_raw": a}
    return a or {}


def workflow(traj: list[dict]) -> dict:
    """Locate first source edit, repro steps, and test runs (OpenHands tool names)."""
    first_src_edit = last_src_edit = None
    repro_steps, check_runs = [], []
    for i, m in enumerate(traj):
        for c in m.get("tool_calls") or []:
            name, a = c["function"]["name"], _args(c)
            if name == "str_replace_editor" and a.get("command") in ("create", "str_replace", "insert"):
                path = a.get("path", "")
                if TEST_PATH.search(path):
                    repro_steps.append(i)
                else:
                    first_src_edit = i if first_src_edit is None else first_src_edit
                    last_src_edit = i
            elif name == "execute_bash" and RUN_CHECK.search(a.get("command", "") or ""):
                check_runs.append(i)
    before = [i for i in repro_steps + check_runs if first_src_edit is not None and i < first_src_edit]
    after = [i for i in check_runs if last_src_edit is not None and i > last_src_edit]
    return {"has_src_edit": first_src_edit is not None, "repro_before_fix": bool(before),
            "verify_after_fix": bool(after), "n_check_runs": len(check_runs)}


def trim(text: str, limit: int) -> str:
    if limit <= 0 or len(text) <= limit:
        return text
    head, tail = text[: int(limit * 0.6)], text[-int(limit * 0.3):]
    return f"{head}\n[... {len(text) - len(head) - len(tail)} characters of tool output omitted ...]\n{tail}"


def convert_traj(row: dict, obs_chars: int, think_tool_to_reasoning: bool) -> dict:
    msgs, pending_thought = [], []
    skip_next_tool_ids = set()
    for m in row["trajectory"]:
        role = m["role"]
        content = m.get("content") or ""
        if role == "assistant":
            calls, thoughts = [], []
            for c in m.get("tool_calls") or []:
                a = _args(c)
                if think_tool_to_reasoning and c["function"]["name"] == "think":
                    thoughts.append(str(a.get("thought", "")))
                    skip_next_tool_ids.add(c.get("id"))
                    continue
                calls.append({"type": "function", "function": {"name": c["function"]["name"], "arguments": a}})
            if not calls and thoughts:  # pure think turn: carry the thought into the next real action
                pending_thought += thoughts
                continue
            reasoning = "\n\n".join(t for t in pending_thought + thoughts if t.strip())
            pending_thought = []
            # OpenHands assistant text before a tool call is the model's own narration -> keep as content
            out = {"role": "assistant", "content": content.strip()}
            if reasoning:
                out["reasoning_content"] = reasoning
            if calls:
                out["tool_calls"] = calls
            msgs.append(out)
        elif role == "tool":
            if m.get("tool_call_id") in skip_next_tool_ids or THINK_ACK.match(content):
                continue
            t = {"role": "tool", "content": trim(content, obs_chars)}
            if m.get("name"):
                t["name"] = m["name"]
            msgs.append(t)
        elif role in ("system", "user"):
            msgs.append({"role": role, "content": content})
    tools = row.get("tools") or []
    if isinstance(tools, str):
        tools = json.loads(tools)
    if think_tool_to_reasoning:
        tools = [t for t in tools if t.get("function", t).get("name") != "think"]
    return record(msgs, tools, f"{SRC}#{row.get('trajectory_id')}",
                  {"instance_id": row.get("instance_id"), "resolved": row.get("resolved"),
                   "gen_tests_correct": row.get("gen_tests_correct"), "model_patch": row.get("model_patch")})


def est_tokens(rec: dict) -> int:
    chars = sum(len(m["content"]) + len(m.get("reasoning_content", "")) +
                sum(len(json.dumps(c["function"]["arguments"], ensure_ascii=False)) for c in m.get("tool_calls", []))
                for m in rec["messages"]) + len(rec["tools"])
    return int(chars / 3.3)  # rough: code/English ≈ 3.3 chars per Qwen token


def load_rows(path: str):
    if path.endswith(".parquet"):
        import pandas as pd  # noqa: PLC0415
        for r in pd.read_parquet(path).to_dict("records"):
            yield {k: (v.tolist() if hasattr(v, "tolist") else v) for k, v in r.items()}
    else:
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    yield json.loads(line)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp")
    ap.add_argument("out")
    ap.add_argument("--max-tokens", type=int, default=16000)
    ap.add_argument("--min-gen-tests", type=int, default=1)
    ap.add_argument("--obs-chars", type=int, default=2500, help="trim each tool output to N chars (0 = keep all)")
    ap.add_argument("--keep-think-tool", action="store_true", help="keep OpenHands 'think' as a tool instead of reasoning_content")
    ap.add_argument("--no-dedup", action="store_true", help="keep all passing trajectories per instance, not only the shortest")
    ap.add_argument("--stats-only", action="store_true")
    a = ap.parse_args()

    stats, best = Counter(), {}
    for row in load_rows(a.inp):
        stats["in"] += 1
        if int(row.get("resolved") or 0) != 1:
            stats["drop_not_resolved"] += 1
            continue
        if not str(row.get("exit_status", "")).startswith("submit"):
            stats["drop_no_submit"] += 1
            continue
        g = row.get("gen_tests_correct")
        if (g or 0) < a.min_gen_tests or (row.get("pred_passes_gen_tests") or 0) < 1:
            stats["drop_no_valid_repro_test"] += 1
            continue
        wf = workflow(row["trajectory"])
        if not (wf["has_src_edit"] and wf["repro_before_fix"] and wf["verify_after_fix"]):
            stats["drop_workflow"] += 1
            continue
        rec = convert_traj(row, a.obs_chars, not a.keep_think_tool)
        n = est_tokens(rec)
        if n > a.max_tokens:
            stats["drop_too_long"] += 1
            continue
        if validate_record(rec):
            stats["drop_invalid"] += 1
            continue
        stats["kept_before_dedup"] += 1
        key = row.get("instance_id") if not a.no_dedup else row.get("trajectory_id")
        if key not in best or n < best[key][0]:
            best[key] = (n, rec)
    kept = [r for _, r in best.values()]
    stats["out"] = len(kept)
    no_think = sum(1 for r in kept for m in r["messages"] if m["role"] == "assistant" and not m.get("reasoning_content"))
    total_asst = sum(1 for r in kept for m in r["messages"] if m["role"] == "assistant") or 1
    if not a.stats_only:
        with open(a.out, "w", encoding="utf-8") as f:
            for r in kept:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(json.dumps({**stats, "assistant_turns_without_reasoning_frac": round(no_think / total_asst, 3),
                      "median_est_tokens": sorted(n for n, _ in best.values())[len(best) // 2] if best else None},
                     indent=1), file=sys.stderr)


if __name__ == "__main__":
    main()
