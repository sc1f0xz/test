"""Extract a JSON (or YAML-free) object from model output and validate it.

Usage:
  extract_json(text) -> object | None   (handles ```json fences, leading prose,
                                          and strips a <think>...</think> block)
  check(text, schema) -> {"ok": bool, "errors": [...], "value": obj}
"""
from __future__ import annotations

import json
import re
from typing import Any

try:
    import jsonschema
except ImportError:  # pragma: no cover
    jsonschema = None

_THINK = re.compile(r"<think>.*?</think>", re.S)
_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.S | re.I)


def extract_json(text: str) -> Any:
    text = _THINK.sub("", text).strip()
    candidates = [m.group(1) for m in _FENCE.finditer(text)] + [text]
    for c in candidates:
        c = c.strip()
        try:
            return json.loads(c)
        except json.JSONDecodeError:
            pass
        # fall back to the first balanced {...} or [...]
        for open_c, close_c in (("{", "}"), ("[", "]")):
            start = c.find(open_c)
            while start != -1:
                depth, in_str, esc = 0, False, False
                for i in range(start, len(c)):
                    ch = c[i]
                    if in_str:
                        if esc:
                            esc = False
                        elif ch == "\\":
                            esc = True
                        elif ch == '"':
                            in_str = False
                    elif ch == '"':
                        in_str = True
                    elif ch == open_c:
                        depth += 1
                    elif ch == close_c:
                        depth -= 1
                        if depth == 0:
                            try:
                                return json.loads(c[start:i + 1])
                            except json.JSONDecodeError:
                                break
                start = c.find(open_c, start + 1)
    return None


def check(text: str, schema: dict | str) -> dict:
    if isinstance(schema, str):
        schema = json.loads(schema)
    value = extract_json(text)
    if value is None:
        return {"ok": False, "errors": ["no JSON found"], "value": None}
    if jsonschema is None:
        raise RuntimeError("pip install jsonschema")
    validator_cls = jsonschema.validators.validator_for(schema)
    validator = validator_cls(schema, format_checker=jsonschema.FormatChecker())
    errors = [f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message}"
              for e in validator.iter_errors(value)]
    return {"ok": not errors, "errors": errors, "value": value}
