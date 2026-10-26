"""Compare predicted tool calls against gold tool calls.

Accepts calls in any of these shapes:
  {"name": ..., "arguments": {...} | "<json string>"}
  {"type": "function", "function": {"name": ..., "arguments": ...}}
  {"<fn_name>": {...args}}                      (BFCL / xLAM "answers" style)

Gold argument values may be a list of acceptable alternatives when
`gold_alternatives=True` (BFCL "possible answer" convention, where "" in the
list means the argument is optional).

Main entry: score_calls(pred, gold, ordered=False) -> dict
  exact            all calls match (name + args), same count
  name_f1          F1 over function names (multiset)
  arg_accuracy     fraction of gold calls fully matched
  no_call_correct  gold empty and pred empty (abstention case)
"""
from __future__ import annotations

import json
import math
from collections import Counter
from typing import Any


def _maybe_json(v: Any) -> Any:
    if isinstance(v, str):
        s = v.strip()
        if s[:1] in "{[" and s[-1:] in "}]":
            try:
                return json.loads(s)
            except json.JSONDecodeError:
                return v
    return v


def normalize_call(call: Any) -> dict:
    """Return {"name": str, "arguments": dict}."""
    call = _maybe_json(call)
    if not isinstance(call, dict):
        raise ValueError(f"unrecognised call: {call!r}")
    if "function" in call and isinstance(call["function"], dict):
        call = call["function"]
    if "name" in call:
        args = _maybe_json(call.get("arguments", call.get("parameters", {})))
        if args is None or args == "":
            args = {}
        if not isinstance(args, dict):
            raise ValueError(f"arguments is not an object: {args!r}")
        return {"name": str(call["name"]), "arguments": args}
    if len(call) == 1:  # {"fn": {...}}
        (name, args), = call.items()
        args = _maybe_json(args) or {}
        if not isinstance(args, dict):
            raise ValueError(f"arguments is not an object: {args!r}")
        return {"name": str(name), "arguments": args}
    raise ValueError(f"unrecognised call: {call!r}")


def normalize_calls(calls: Any) -> list[dict]:
    calls = _maybe_json(calls)
    if calls is None or calls == "":
        return []
    if isinstance(calls, dict):
        calls = [calls]
    return [normalize_call(c) for c in calls]


def _norm_scalar(v: Any) -> Any:
    if isinstance(v, str):
        s = v.strip()
        # numeric strings compare equal to numbers ("5" == 5)
        try:
            f = float(s)
            if math.isfinite(f):
                return f
        except ValueError:
            pass
        return s.lower()
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return float(v)
    return v


def values_equal(pred: Any, gold: Any, rel_tol: float = 1e-6) -> bool:
    pred, gold = _maybe_json(pred), _maybe_json(gold)
    if isinstance(gold, dict):
        if not isinstance(pred, dict) or set(pred) != set(gold):
            return False
        return all(values_equal(pred[k], gold[k], rel_tol) for k in gold)
    if isinstance(gold, list):
        if not isinstance(pred, list) or len(pred) != len(gold):
            return False
        return all(values_equal(p, g, rel_tol) for p, g in zip(pred, gold))
    p, g = _norm_scalar(pred), _norm_scalar(gold)
    if isinstance(p, float) and isinstance(g, float):
        return math.isclose(p, g, rel_tol=rel_tol, abs_tol=1e-9)
    return p == g


def args_match(pred_args: dict, gold_args: dict, gold_alternatives: bool = False) -> bool:
    if not gold_alternatives:
        return values_equal(pred_args, gold_args)
    for k, alts in gold_args.items():
        alts = alts if isinstance(alts, list) else [alts]
        optional = "" in alts
        if k not in pred_args:
            if not optional:
                return False
            continue
        if not any(values_equal(pred_args[k], a) for a in alts if a != ""):
            return False
    return all(k in gold_args for k in pred_args)  # no hallucinated params


def score_calls(pred: Any, gold: Any, ordered: bool = False,
                gold_alternatives: bool = False) -> dict:
    try:
        p = normalize_calls(pred)
    except ValueError as e:
        return {"exact": False, "name_f1": 0.0, "arg_accuracy": 0.0,
                "no_call_correct": False, "error": f"pred parse: {e}"}
    g = normalize_calls(gold)
    if not g:
        ok = not p
        return {"exact": ok, "name_f1": 1.0 if ok else 0.0,
                "arg_accuracy": 1.0 if ok else 0.0, "no_call_correct": ok}
    pn, gn = Counter(c["name"] for c in p), Counter(c["name"] for c in g)
    inter = sum((pn & gn).values())
    prec = inter / max(1, sum(pn.values()))
    rec = inter / sum(gn.values())
    f1 = 0.0 if inter == 0 else 2 * prec * rec / (prec + rec)

    matched = 0
    if ordered:
        for pc, gc in zip(p, g):
            if pc["name"] == gc["name"] and args_match(pc["arguments"], gc["arguments"], gold_alternatives):
                matched += 1
    else:  # greedy bipartite matching is fine for small call lists
        used = set()
        for gc in g:
            for i, pc in enumerate(p):
                if i in used:
                    continue
                if pc["name"] == gc["name"] and args_match(pc["arguments"], gc["arguments"], gold_alternatives):
                    used.add(i)
                    matched += 1
                    break
    exact = matched == len(g) == len(p)
    return {"exact": exact, "name_f1": f1, "arg_accuracy": matched / len(g),
            "no_call_correct": False}


def validate_against_schema(call: dict, tools: list[dict]) -> list[str]:
    """Check a call uses a declared tool, has required params, and no unknown params."""
    call = normalize_call(call)
    by_name = {}
    for t in tools:
        f = t.get("function", t)
        by_name[f.get("name")] = f
    if call["name"] not in by_name:
        return [f"unknown tool {call['name']}"]
    params = by_name[call["name"]].get("parameters") or {}
    props = params.get("properties") or {}
    errs = [f"missing required {r}" for r in params.get("required", []) if r not in call["arguments"]]
    if props:
        errs += [f"unknown param {k}" for k in call["arguments"] if k not in props]
    for k, v in call["arguments"].items():
        enum = (props.get(k) or {}).get("enum")
        if enum and v not in enum:
            errs.append(f"{k}={v!r} not in enum")
    return errs
