"""End-to-end check on REAL rows: converter -> render_chat (official template, flags from registry.json) -> token stats.

Run this on full, untruncated rows before any training run (samples/ in the repo are truncated to <30 KB, so
passing converters/test_converters.py does NOT prove the converters work on real data).

  python3 tools/pipeline_check.py RAW_DIR OUT_DIR --tokenizer <Qwen3.5-4B>/tokenizer.json [--max-tokens 16384] [names...]

RAW_DIR holds one file per converter, named <converter_name>.jsonl|.json|.parquet (raw dataset rows; e.g. from
tools/fetch_fullrows.py or from your real downloads). OUT_DIR gets <name>.jsonl (records) and <name>.r.jsonl
(rendered samples, only for roles that train directly). Needs: pip install jinja2 tokenizers (pyarrow for parquet).
"""
from __future__ import annotations

import argparse
import json
import os
import statistics as st
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAIN_ROLES = {"sft", "style"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("raw_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--tokenizer", required=True)
    ap.add_argument("--max-tokens", type=int, default=16384)
    ap.add_argument("names", nargs="*")
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    reg = json.load(open(os.path.join(ROOT, "converters", "registry.json"), encoding="utf-8"))
    files = {}
    for f in sorted(os.listdir(a.raw_dir)):
        base, ext = os.path.splitext(f)
        if ext in {".jsonl", ".json", ".parquet"} and base in reg:
            files[base] = os.path.join(a.raw_dir, f)
    names = a.names or list(files)
    bad = 0
    print(f"{'dataset':58s} {'role':11s} {'rows->records':14s} {'samples':8s} {'nothink':8s} {'too_long':8s} tokens med/max")
    for n in names:
        role = reg.get(n, {}).get("role", "?")
        out = os.path.join(a.out_dir, f"{n}.jsonl")
        with open(out, "w", encoding="utf-8") as fo:
            c = subprocess.run([sys.executable, os.path.join(ROOT, "converters", f"{n}.py"), files[n]],
                               stdout=fo, stderr=subprocess.PIPE, text=True)
        conv = (c.stderr.strip().splitlines() or ["?"])[-1]
        if c.returncode != 0:
            bad += 1
            print(f"{n[:58]:58s} {role:11s} CONVERTER FAILED: {c.stderr[-300:]}")
            continue
        try:
            n_in, n_rec = conv.strip("[]").split(",")[0].split()[0], conv.strip("[]").split(",")[1].split()[0]
        except Exception:  # noqa: BLE001
            n_in, n_rec = "?", "?"
        if role not in TRAIN_ROLES:
            print(f"{n[:58]:58s} {role:11s} {n_in + '->' + n_rec:14s} (not trained directly)")
            continue
        flags = (reg[n].get("render") or "--require-think").split()
        rout = os.path.join(a.out_dir, f"{n}.r.jsonl")
        r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "render_chat.py"),
                            os.path.join(ROOT, "tools", "qwen3_5_chat_template.jinja"), out, rout, *flags,
                            "--tokenizer", a.tokenizer, "--max-tokens", str(a.max_tokens)], capture_output=True, text=True)
        try:
            d = json.loads(r.stderr.strip().splitlines()[-1])
        except Exception:  # noqa: BLE001
            bad += 1
            print(f"{n[:58]:58s} {role:11s} RENDER FAILED: {r.stderr[-300:]}")
            continue
        bad += d["errors"] > 0
        lens = [json.loads(l)["n_tokens"] for l in open(rout, encoding="utf-8")]
        tok = f"{int(st.median(lens))}/{max(lens)}" if lens else "-"
        print(f"{n[:58]:58s} {role:11s} {n_in + '->' + n_rec:14s} {d['out_samples']:<8d} "
              f"{d['trained_turns_without_thinking']:<8d} {d['dropped_too_long']:<8d} {tok}"
              + (f"  RENDER ERRORS={d['errors']}" if d["errors"] else ""))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
