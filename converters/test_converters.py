"""Run every converter against its sample file.

python3 converters/test_converters.py          # all
python3 converters/test_converters.py name ... # some

Pairing rule: converters/<name>.py  <->  samples/<name>.jsonl
Each converter must produce >=1 valid record and must not raise on more than
20% of sample rows.
"""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from common import validate_record  # noqa: E402


def run_one(name: str) -> tuple[bool, str]:
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    path = os.path.join(ROOT, "samples", f"{name}.jsonl")
    if not os.path.exists(path):
        return False, "no sample file"
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    n_err, n_out, problems = 0, 0, []
    for i, row in enumerate(rows):
        try:
            out = mod.convert(row)
        except Exception as e:  # noqa: BLE001
            n_err += 1
            problems.append(f"row{i}: {type(e).__name__}: {e}")
            continue
        for rec in ([out] if isinstance(out, dict) else (out or [])):
            errs = validate_record(rec)
            if errs:
                n_err += 1
                problems.append(f"row{i}: {errs[:2]}")
            else:
                n_out += 1
    ok = n_out >= 1 and n_err <= 0.2 * len(rows)
    return ok, f"{len(rows)} rows -> {n_out} records, {n_err} errors" + (f" | {problems[:2]}" if problems else "")


def check_registry(names):
    reg = json.load(open(os.path.join(HERE, "registry.json"), encoding="utf-8"))
    missing = [n for n in names if n not in reg]
    bad = [n for n, v in reg.items() if n != "_doc" and v.get("role") not in {"sft", "prompt_only", "dpo", "style"}]
    return missing, bad


if __name__ == "__main__":
    names = sys.argv[1:] or sorted(f[:-3] for f in os.listdir(HERE)
                                   if f.endswith(".py") and f not in {"common.py", "test_converters.py", "__init__.py"})
    failed = 0
    for n in names:
        ok, msg = run_one(n)
        failed += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {n}: {msg}")
    missing, bad = check_registry(names)
    if missing or bad:
        failed += 1
        print(f"FAIL  registry.json: missing={missing} bad_role={bad}")
    print(f"\n{len(names) - failed}/{len(names)} converters pass (registry checked)")
    sys.exit(1 if failed else 0)
