"""Smoke + logic tests for tools/filter_swe_trajectories.py:  python3 -m unittest discover -s tools/tests -t ."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import filter_swe_trajectories as F  # noqa: E402


def call(name, **args):
    return {"id": f"c{name}{len(json.dumps(args))}", "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}


GOOD = [
    {"role": "system", "content": "sys"}, {"role": "user", "content": "fix bug"},
    {"role": "assistant", "content": "", "tool_calls": [call("think", thought="likely off-by-one in parse()")]},
    {"role": "tool", "content": "Your thought has been logged.", "tool_call_id": None, "name": "think"},
    {"role": "assistant", "content": "repro", "tool_calls": [call("str_replace_editor", command="create", path="/w/reproduce_issue.py", file_text="x")]},
    {"role": "tool", "content": "created", "name": "str_replace_editor"},
    {"role": "assistant", "content": "", "tool_calls": [call("execute_bash", command="python /w/reproduce_issue.py")]},
    {"role": "tool", "content": "Traceback ...", "name": "execute_bash"},
    {"role": "assistant", "content": "", "tool_calls": [call("str_replace_editor", command="str_replace", path="/w/pkg/parse.py", old_str="a", new_str="b")]},
    {"role": "tool", "content": "ok " * 2000, "name": "str_replace_editor"},
    {"role": "assistant", "content": "", "tool_calls": [call("execute_bash", command="cd /w && python -m pytest tests/test_parse.py")]},
    {"role": "tool", "content": "1 passed", "name": "execute_bash"},
    {"role": "assistant", "content": "done", "tool_calls": [call("finish", message="fixed")]},
]


class T(unittest.TestCase):
    def test_workflow_detects_repro_and_verify(self):
        wf = F.workflow(GOOD)
        self.assertTrue(wf["has_src_edit"] and wf["repro_before_fix"] and wf["verify_after_fix"])
        bad = [m for m in GOOD if "pytest" not in json.dumps(m) and "reproduce" not in json.dumps(m)]
        wf = F.workflow(bad)
        self.assertFalse(wf["repro_before_fix"] and wf["verify_after_fix"])

    def test_convert_moves_think_to_reasoning_and_trims(self):
        rec = F.convert_traj({"trajectory": GOOD, "tools": [{"type": "function", "function": {"name": "think", "parameters": {}}},
                                                            {"type": "function", "function": {"name": "execute_bash", "parameters": {"type": "object", "properties": {}}}}],
                              "trajectory_id": "t1"}, obs_chars=500, think_tool_to_reasoning=True)
        asst = [m for m in rec["messages"] if m["role"] == "assistant"]
        self.assertEqual(asst[0]["reasoning_content"], "likely off-by-one in parse()")
        self.assertFalse(any(c["function"]["name"] == "think" for m in asst for c in m.get("tool_calls", [])))
        self.assertFalse(any("thought has been logged" in m["content"] for m in rec["messages"]))
        self.assertTrue(all(len(m["content"]) <= 600 for m in rec["messages"] if m["role"] == "tool"))
        self.assertNotIn("think", rec["tools"])

    def test_cli_end_to_end_and_dedup(self):
        base = {"tools": [], "exit_status": "submit", "resolved": 1, "gen_tests_correct": 1, "pred_passes_gen_tests": 1,
                "instance_id": "i1", "model_patch": "diff"}
        rows = [{**base, "trajectory_id": "long", "trajectory": GOOD + [{"role": "user", "content": "x" * 3000}]},
                {**base, "trajectory_id": "short", "trajectory": GOOD},
                {**base, "trajectory_id": "unresolved", "resolved": 0, "instance_id": "i2", "trajectory": GOOD},
                {**base, "trajectory_id": "nogen", "gen_tests_correct": 0, "instance_id": "i3", "trajectory": GOOD}]
        with tempfile.TemporaryDirectory() as d:
            inp, out = os.path.join(d, "in.jsonl"), os.path.join(d, "out.jsonl")
            open(inp, "w").write("\n".join(json.dumps(r) for r in rows) + "\n")
            r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "filter_swe_trajectories.py"), inp, out], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            got = [json.loads(l) for l in open(out)]
            self.assertEqual([g["src"].split("#")[1] for g in got], ["short"])
            stats = json.loads(r.stderr)
            self.assertEqual(stats["drop_not_resolved"], 1)
            self.assertEqual(stats["drop_no_valid_repro_test"], 1)

    def test_real_sample_runs(self):
        p = os.path.join(ROOT, "samples", "nebius__SWE-rebench-openhands-trajectories.jsonl")
        with tempfile.TemporaryDirectory() as d:
            r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "filter_swe_trajectories.py"), p, os.path.join(d, "o.jsonl"),
                                "--max-tokens", "10000000"], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn('"in"', r.stderr)


if __name__ == "__main__":
    unittest.main()
