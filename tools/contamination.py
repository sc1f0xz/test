"""8-gram shingle contamination check against eval benchmarks.

    python3 tools/contamination.py build [--cache DIR] [--only gsm8k,humaneval,...]
    python3 tools/contamination.py scan FILE.jsonl [FILE2 ...] [--cache DIR] [--jaccard 0.5] [--containment 0.8]

Method
  * normalise: NFKC, lowercase, keep word chars (Thai/Latin/digits) -> tokens
  * shingles = set of 8-token windows (texts shorter than 8 tokens are skipped)
  * for each training text unit (each user/system/tool message and each
    top-level string field, plus the whole row), look up benchmark items that
    share >=1 shingle via an inverted index, then compute
        Jaccard     = |A∩B| / |A∪B|
        containment = |A∩B| / |B|   (share of the benchmark item copied)
  * FLAG when Jaccard >= 0.5 (spec) ; also report containment >= 0.8, which
    catches benchmark questions embedded inside longer prompts.

Benchmarks indexed (all small; cached outside the repo):
  gsm8k-test, humaneval, mbppplus, ifeval, bfcl-v3 (all categories),
  mmlu-pro-test, swe-bench (full test + verified), terminal-bench-2.0
  (instruction.md of every task), browsecomp (decrypted with the public
  canary procedure from openai/simple-evals). GAIA is gated -> not indexed.
"""
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
import json
import os
import pickle
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from collections import defaultdict

N = 8
API = "https://datasets-server.huggingface.co"
TOKEN_RE = re.compile(r"\w+", re.U)


def norm_tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(unicodedata.normalize("NFKC", text).lower())


def shingles(text: str, n: int = N) -> set[int]:
    t = norm_tokens(text)
    if len(t) < n:
        return set()
    # deterministic 48-bit hash (built-in hash() is salted per process, which would break the cached index)
    return {int.from_bytes(hashlib.blake2b(" ".join(t[i:i + n]).encode(), digest_size=6).digest(), "big")
            for i in range(len(t) - n + 1)}


def _get(url: str, as_json: bool = True, tries: int = 5):
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                data = r.read()
            return json.loads(data) if as_json else data
        except Exception:  # noqa: BLE001
            if i == tries - 1:
                raise
            time.sleep(2 ** i)


def hf_rows(ds: str, config: str, split: str, fields: list[str]) -> list[str]:
    q = f"dataset={urllib.parse.quote(ds)}&config={urllib.parse.quote(config)}&split={urllib.parse.quote(split)}"
    total = _get(f"{API}/size?dataset={urllib.parse.quote(ds)}")["size"]["splits"]
    n = next(s["num_rows"] for s in total if s["config"] == config and s["split"] == split)
    out = []
    for off in range(0, n, 100):
        rows = _get(f"{API}/rows?{q}&offset={off}&length=100")["rows"]
        for r in rows:
            out.append("\n".join(str(r["row"].get(f, "")) for f in fields))
    return out


def load_bfcl() -> list[str]:
    base = "https://huggingface.co/datasets/gorilla-llm/Berkeley-Function-Calling-Leaderboard/resolve/main/"
    tree = _get("https://huggingface.co/api/datasets/gorilla-llm/Berkeley-Function-Calling-Leaderboard/tree/main")
    out = []
    for f in tree:
        if f["path"].startswith("BFCL_") and f["path"].endswith(".json"):
            for line in _get(base + f["path"], as_json=False).decode().splitlines():
                if line.strip():
                    q = json.loads(line).get("question")
                    out.append(json.dumps(q, ensure_ascii=False) if not isinstance(q, str) else q)
    return out


def load_terminal_bench() -> list[str]:
    ds = "harborframework/terminal-bench-2.0"
    dirs = [d["path"] for d in _get(f"https://huggingface.co/api/datasets/{ds}/tree/main") if d["type"] == "directory"]
    out = []
    for d in dirs:
        try:
            out.append(_get(f"https://huggingface.co/datasets/{ds}/resolve/main/{d}/instruction.md", as_json=False).decode())
        except Exception:  # noqa: BLE001
            pass
    return out


def _xor_decrypt(ciphertext_b64: str, password: str) -> str:
    # openai/simple-evals browsecomp_eval.py: key = sha256(password) repeated, XOR
    encrypted = base64.b64decode(ciphertext_b64)
    key = hashlib.sha256(password.encode()).digest()
    key = (key * (len(encrypted) // len(key) + 1))[: len(encrypted)]
    return bytes(a ^ b for a, b in zip(encrypted, key)).decode()


def load_browsecomp() -> list[str]:
    raw = _get("https://openaipublic.blob.core.windows.net/simple-evals/browse_comp_test_set.csv", as_json=False).decode()
    return [_xor_decrypt(r["problem"], r["canary"]) for r in csv.DictReader(io.StringIO(raw))]


BENCHMARKS = {
    "gsm8k-test": lambda: hf_rows("openai/gsm8k", "main", "test", ["question"]),
    "humaneval": lambda: hf_rows("openai/openai_humaneval", "openai_humaneval", "test", ["prompt"]),
    "mbppplus": lambda: hf_rows("evalplus/mbppplus", "default", "test", ["prompt"]),
    "ifeval": lambda: hf_rows("google/IFEval", "default", "train", ["prompt"]),
    "bfcl-v3": load_bfcl,
    "mmlu-pro-test": lambda: hf_rows("TIGER-Lab/MMLU-Pro", "default", "test", ["question"]),
    "swe-bench-verified": lambda: hf_rows("princeton-nlp/SWE-bench_Verified", "default", "test", ["problem_statement"]),
    "swe-bench-full": lambda: hf_rows("princeton-nlp/SWE-bench", "default", "test", ["problem_statement"]),
    "terminal-bench-2.0": load_terminal_bench,
    "browsecomp": load_browsecomp,
}


def build(cache: str, only: list[str] | None):
    os.makedirs(cache, exist_ok=True)
    for name, loader in BENCHMARKS.items():
        if only and name not in only:
            continue
        path = os.path.join(cache, f"{name}.json")
        if os.path.exists(path):
            print(f"{name}: cached")
            continue
        try:
            texts = loader()
        except Exception as e:  # noqa: BLE001
            print(f"{name}: FAILED {e}", file=sys.stderr)
            continue
        json.dump(texts, open(path, "w"))
        print(f"{name}: {len(texts)} items")


def load_index(cache: str):
    path = os.path.join(cache, f"index_n{N}.pkl")
    names = sorted(f[:-5] for f in os.listdir(cache) if f.endswith(".json"))
    if os.path.exists(path):
        idx = pickle.load(open(path, "rb"))
        if idx["names"] == names:
            return idx
    items, inv = [], defaultdict(list)
    for name in names:
        for i, t in enumerate(json.load(open(os.path.join(cache, f"{name}.json")))):
            sh = shingles(t)
            if not sh:
                continue
            k = len(items)
            items.append((name, i, len(sh), t[:160]))
            for s in sh:
                inv[s].append(k)
    idx = {"names": names, "items": items, "inv": dict(inv), "sh": None}
    # keep per-item shingle sets for exact Jaccard
    idx["sh"] = [None] * len(items)
    k = 0
    for name in names:
        for t in json.load(open(os.path.join(cache, f"{name}.json"))):
            sh = shingles(t)
            if sh:
                idx["sh"][k] = sh
                k += 1
    pickle.dump(idx, open(path, "wb"))
    return idx


def text_units(row) -> list[str]:
    units = []

    def walk(v, depth=0):
        if isinstance(v, str):
            s = v.strip()
            if s[:1] in "[{" and s[-1:] in "]}" and depth < 3:
                try:
                    walk(json.loads(s), depth + 1)
                    return
                except json.JSONDecodeError:
                    pass
            units.append(v)
        elif isinstance(v, list):
            for x in v:
                walk(x, depth + 1)
        elif isinstance(v, dict):
            role = v.get("role", v.get("from"))
            if role in ("assistant", "gpt"):  # model outputs are not where benchmark prompts hide
                return
            for x in v.values():
                walk(x, depth + 1)

    walk(row)
    return units


def scan(files: list[str], cache: str, jac_t: float, cont_t: float):
    idx = load_index(cache)
    summary = {}
    for fpath in files:
        rows = [json.loads(l) for l in open(fpath, encoding="utf-8") if l.strip()]
        hits = []
        for ri, row in enumerate(rows):
            for u in text_units(row) + [json.dumps(row, ensure_ascii=False)]:
                A = shingles(u)
                if not A:
                    continue
                cands = defaultdict(int)
                for s in A:
                    for k in idx["inv"].get(s, ()):
                        cands[k] += 1
                for k, inter in cands.items():
                    B = idx["sh"][k]
                    jac = inter / (len(A) + len(B) - inter)
                    cont = inter / len(B)
                    if jac >= jac_t or cont >= cont_t:
                        name, bi, _, preview = idx["items"][k]
                        hits.append({"row": ri, "bench": name, "bench_item": bi, "jaccard": round(jac, 3),
                                     "containment": round(cont, 3), "bench_preview": preview})
        best = {}
        for h in hits:
            key = (h["row"], h["bench"], h["bench_item"])
            if key not in best or h["containment"] > best[key]["containment"]:
                best[key] = h
        flagged_rows = {h["row"] for h in best.values() if h["jaccard"] >= jac_t}
        contained_rows = {h["row"] for h in best.values() if h["containment"] >= cont_t}
        summary[os.path.basename(fpath)] = {"rows": len(rows), "jaccard_flag_rows": len(flagged_rows),
                                            "containment_flag_rows": len(contained_rows),
                                            "hits": sorted(best.values(), key=lambda h: -h["containment"])[:10]}
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build", "scan"])
    ap.add_argument("files", nargs="*")
    ap.add_argument("--cache", default=os.path.expanduser("~/.cache/contam_bench"))
    ap.add_argument("--only", default="")
    ap.add_argument("--jaccard", type=float, default=0.5)
    ap.add_argument("--containment", type=float, default=0.8)
    a = ap.parse_args()
    if a.cmd == "build":
        build(a.cache, [x for x in a.only.split(",") if x] or None)
    else:
        scan(a.files, a.cache, a.jaccard, a.containment)
