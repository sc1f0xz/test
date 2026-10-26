"""Final-answer checker for competition math.

extract_answer(text): last \\boxed{...} (balanced braces); falls back to
"answer is X" / "#### X" / last number.
is_equivalent(pred, gold): string normalisation -> numeric/fraction compare ->
sympy symbolic compare (if sympy is installed).
"""
from __future__ import annotations

import re
from fractions import Fraction

try:
    import sympy
    from sympy.parsing.latex import parse_latex  # needs antlr4; optional
except Exception:  # pragma: no cover
    sympy = None
    parse_latex = None

_THINK = re.compile(r"<think>.*?</think>", re.S)


def _last_boxed(text: str) -> str | None:
    idx = max(text.rfind("\\boxed"), text.rfind("\\fbox"))
    if idx < 0:
        return None
    i = text.find("{", idx)
    if i < 0:
        return None
    depth = 0
    for j in range(i, len(text)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return text[i + 1:j]
    return None


def extract_answer(text: str) -> str | None:
    body = _THINK.sub("", text)
    b = _last_boxed(body) or _last_boxed(text)
    if b is not None:
        return b.strip()
    m = re.search(r"####\s*(.+)", body)
    if m:
        return m.group(1).strip()
    m = re.findall(r"(?:final answer|answer is|คำตอบคือ)\s*[:：]?\s*\$?([^\n$]+)", body, re.I)
    if m:
        return m[-1].strip().rstrip(".")
    nums = re.findall(r"-?\d+(?:,\d{3})*(?:\.\d+)?(?:/\d+)?", body)
    return nums[-1] if nums else None


_REPL = [
    (r"\\left|\\right|\\!|\\,|\\;|\\:|\\ ", ""), (r"\\dfrac|\\tfrac", r"\\frac"),
    (r"\^\{\\circ\}|\^\\circ|°", ""), (r"\\%|%", ""), (r"\\text\{[^}]*\}", ""),
    (r"\\mathrm\{[^}]*\}", ""), (r"\$", ""), (r"\s+", ""),
]


def normalize(s: str) -> str:
    s = s.strip()
    for a, b in _REPL:
        s = re.sub(a, b, s)
    s = s.rstrip(".")
    s = re.sub(r"^(x|y|n|k|a|ans)=", "", s)
    s = re.sub(r"(?<=\d),(?=\d{3}\b)", "", s)  # 1,000 -> 1000
    return s


def _to_fraction(s: str):
    m = re.fullmatch(r"\\frac\{(-?\d+)\}\{(-?\d+)\}", s) or re.fullmatch(r"\\frac(\d)(\d)", s)
    if m:
        return Fraction(int(m.group(1)), int(m.group(2)))
    m = re.fullmatch(r"(-?\d+)/(\d+)", s)
    if m:
        return Fraction(int(m.group(1)), int(m.group(2)))
    try:
        return Fraction(s)
    except (ValueError, ZeroDivisionError):
        return None


def is_equivalent(pred: str | None, gold: str) -> bool:
    if pred is None:
        return False
    p, g = normalize(pred), normalize(gold)
    if p == g:
        return True
    fp, fg = _to_fraction(p), _to_fraction(g)
    if fp is not None and fg is not None:
        return fp == fg
    # unordered tuples / sets like "1,2" vs "2,1"
    if "," in p and "," in g:
        sp, sg = sorted(p.strip("(){}[]").split(",")), sorted(g.strip("(){}[]").split(","))
        if len(sp) == len(sg) and all(is_equivalent(a, b) for a, b in zip(sp, sg)):
            return True
    if sympy is not None and parse_latex is not None:
        try:
            return bool(sympy.simplify(parse_latex(p) - parse_latex(g)) == 0)
        except Exception:
            return False
    return False


def check(text: str, gold: str) -> dict:
    pred = extract_answer(text)
    return {"ok": is_equivalent(pred, gold), "pred": pred}
