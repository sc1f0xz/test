"""Run untrusted Python code against tests in an isolated subprocess.

Isolation (best effort, Linux):
  * fresh temp dir as cwd, deleted afterwards
  * `python3 -I` (ignores env/user site), stripped environment
  * RLIMIT_AS (memory), RLIMIT_CPU, RLIMIT_FSIZE, RLIMIT_NPROC
  * wall-clock timeout, process-group kill
  * network namespace via `unshare -rn` when available (no network)
This is NOT a security sandbox against a determined attacker; run it inside a
container/VM when executing large volumes of model output.

Modes:
  run_function_tests(code, test_code)      -> code + asserts (HumanEval/KodCode style)
  run_stdio_tests(code, [(stdin, stdout)])  -> program reads stdin (Codeforces style)
"""
from __future__ import annotations

import os
import resource
import shutil
import signal
import subprocess
import sys
import tempfile

_UNSHARE = shutil.which("unshare")
_NET_OK = None


def _net_isolation_works() -> bool:
    global _NET_OK
    if _NET_OK is None:
        if not _UNSHARE:
            _NET_OK = False
        else:
            try:
                r = subprocess.run([_UNSHARE, "-rn", "true"], capture_output=True, timeout=5)
                _NET_OK = r.returncode == 0
            except Exception:
                _NET_OK = False
    return _NET_OK


def _limits(mem_mb: int, cpu_s: int):
    def apply():
        os.setsid()
        resource.setrlimit(resource.RLIMIT_AS, (mem_mb * 2**20, mem_mb * 2**20))
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_s, cpu_s + 1))
        resource.setrlimit(resource.RLIMIT_FSIZE, (16 * 2**20, 16 * 2**20))
        try:
            resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))
        except (ValueError, OSError):
            pass
    return apply


def _run(script: str, stdin: str = "", timeout: float = 10.0, mem_mb: int = 1024) -> dict:
    tmp = tempfile.mkdtemp(prefix="safe_exec_")
    try:
        path = os.path.join(tmp, "main.py")
        with open(path, "w") as f:
            f.write(script)
        cmd = [sys.executable, "-I", "-B", path]
        if _net_isolation_works():
            cmd = [_UNSHARE, "-rn"] + cmd
        env = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "PYTHONHASHSEED": "0"}
        proc = subprocess.Popen(cmd, cwd=tmp, env=env, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                preexec_fn=_limits(mem_mb, int(timeout) + 1), text=True)
        try:
            out, err = proc.communicate(stdin, timeout=timeout)
            timed_out = False
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            out, err = proc.communicate()
            timed_out = True
        return {"returncode": proc.returncode, "stdout": out[-20000:], "stderr": err[-5000:],
                "timed_out": timed_out}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run_function_tests(code: str, test_code: str, entry_point: str | None = None,
                       timeout: float = 10.0) -> dict:
    """`test_code` may define check(candidate) (HumanEval style) or be bare asserts / pytest-style test_* functions."""
    runner = [code, "", test_code, ""]
    if entry_point and "def check(" in test_code:
        runner.append(f"check({entry_point})")
    runner.append(
        "import sys as _s\n"
        "_g = dict(globals())\n"
        "for _n, _f in _g.items():\n"
        "    if _n.startswith('test_') and callable(_f):\n"
        "        _f()\n"
        "print('__ALL_TESTS_PASSED__')\n")
    r = _run("\n".join(runner), timeout=timeout)
    r["passed"] = (not r["timed_out"]) and r["returncode"] == 0 and "__ALL_TESTS_PASSED__" in r["stdout"]
    return r


def _tokens(s: str) -> list[str]:
    return s.split()


def run_stdio_tests(code: str, cases: list[tuple[str, str]], timeout: float = 5.0,
                    float_tol: float | None = 1e-6) -> dict:
    results = []
    for stdin, expected in cases:
        r = _run(code, stdin=stdin, timeout=timeout)
        got, exp = _tokens(r["stdout"]), _tokens(expected)
        ok = r["returncode"] == 0 and not r["timed_out"] and len(got) == len(exp)
        if ok:
            for a, b in zip(got, exp):
                if a == b:
                    continue
                if float_tol is not None:
                    try:
                        if abs(float(a) - float(b)) <= float_tol * max(1.0, abs(float(b))):
                            continue
                    except ValueError:
                        pass
                ok = False
                break
        results.append(ok)
        if not ok:
            break  # fail fast
    return {"passed": len(results) == len(cases) and all(results),
            "n_passed": sum(results), "n_cases": len(cases)}
