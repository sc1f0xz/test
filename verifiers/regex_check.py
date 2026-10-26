"""Regex task checker: predicted pattern must fullmatch all positives and no
negatives. Uses a subprocess timeout to defend against catastrophic
backtracking (ReDoS) in model-written patterns.
"""
from __future__ import annotations

import json
import subprocess
import sys

_CHILD = r"""
import json, re, sys
d = json.load(sys.stdin)
try:
    rx = re.compile(d["pattern"], getattr(re, d.get("flags", "NOFLAG"), 0))
except re.error as e:
    print(json.dumps({"ok": False, "error": "compile: %s" % e})); sys.exit()
bad_pos = [s for s in d["positives"] if not rx.fullmatch(s)]
bad_neg = [s for s in d["negatives"] if rx.fullmatch(s)]
print(json.dumps({"ok": not bad_pos and not bad_neg, "bad_pos": bad_pos[:5], "bad_neg": bad_neg[:5], "error": None}))
"""


def check(pattern: str, positives: list[str], negatives: list[str], timeout: float = 2.0) -> dict:
    payload = json.dumps({"pattern": pattern, "positives": positives, "negatives": negatives})
    try:
        r = subprocess.run([sys.executable, "-I", "-c", _CHILD], input=payload, text=True,
                           capture_output=True, timeout=timeout)
        return json.loads(r.stdout)
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout (possible catastrophic backtracking)"}
