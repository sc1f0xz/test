"""Fetch a few real rows of a HF dataset via datasets-server and save a small,
schema-preserving sample (<30 KB) for converter development.

python3 tools/fetch_samples.py <hf_id> <config> <split> <out_name> [n_rows=20] [drop_cols=a,b]

- uses /rows (full cells) with retries, falls back to /first-rows (cells may be truncated)
- long strings are shortened (JSON-in-string fields are parsed, shortened, re-dumped so they stay valid JSON)
- shrinks string budget / row count until the file is < 30 KB (min 5 rows)
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request

API = "https://datasets-server.huggingface.co"
MAX_BYTES = 30_000
HEAVY = {"prompt_token_ids", "completion_token_ids", "logprobs", "input_ids", "labels", "attention_mask"}


def _get(url: str, tries: int = 5):
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=90) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001
            if i == tries - 1:
                raise
            time.sleep(2 ** i)


def fetch(ds: str, config: str, split: str, n: int) -> tuple[list[dict], str]:
    q = f"dataset={urllib.parse.quote(ds)}&config={urllib.parse.quote(config)}&split={urllib.parse.quote(split)}"
    try:
        d = _get(f"{API}/rows?{q}&offset=0&length={min(n, 100)}")
        return [r["row"] for r in d["rows"]], "rows"
    except Exception:  # noqa: BLE001
        d = _get(f"{API}/first-rows?{q}")
        return [r["row"] for r in d["rows"]][:n], "first-rows(truncated cells possible)"


def shorten(v, limit: int):
    if isinstance(v, str):
        s = v.strip()
        if len(v) > limit and s[:1] in "[{" and s[-1:] in "]}":
            try:
                return json.dumps(shorten(json.loads(s), limit), ensure_ascii=False)
            except json.JSONDecodeError:
                pass
        if len(v) > limit:
            head = v[: int(limit * 0.7)]
            tail = v[-int(limit * 0.2):]
            return f"{head}\n…[TRUNCATED {len(v) - len(head) - len(tail)} chars]…\n{tail}"
        return v
    if isinstance(v, list):
        if len(v) > 40:  # long conversations: keep head and tail turns
            v = v[:30] + v[-10:]
        return [shorten(x, limit) for x in v]
    if isinstance(v, dict):
        return {k: shorten(x, limit) for k, x in v.items()}
    return v


def main():
    ds, config, split, name = sys.argv[1:5]
    n = int(sys.argv[5]) if len(sys.argv) > 5 else 20
    drop = set(sys.argv[6].split(",")) if len(sys.argv) > 6 and sys.argv[6] else set()
    rows, how = fetch(ds, config, split, n)
    rows = [{k: v for k, v in r.items() if k not in HEAVY | drop} for r in rows]
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "samples", f"{name}.jsonl")
    limit, keep = 3000, len(rows)
    while True:
        lines = [json.dumps(shorten(r, limit), ensure_ascii=False) for r in rows[:keep]]
        body = "\n".join(lines) + "\n"
        if len(body.encode()) <= MAX_BYTES or (limit <= 200 and keep <= 5):
            break
        if limit > 400:
            limit = int(limit * 0.7)
        elif keep > 5:
            keep -= 1
        else:
            limit = int(limit * 0.7)
    with open(out, "w", encoding="utf-8") as f:
        f.write(body)
    print(f"{name}: {keep} rows via {how}, str_limit={limit}, {len(body.encode())} bytes -> {out}")


if __name__ == "__main__":
    main()
