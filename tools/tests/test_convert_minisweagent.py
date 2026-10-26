"""Tests for tools/convert_minisweagent.py with a fixture shaped like mini-swe-agent 2.4.6 output
(agents/default.py serialize(), models/litellm_model.py message.model_dump(), actions_toolcall observations)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, "tools", "convert_minisweagent.py")


def call(cid, cmd):
    return {"id": cid, "type": "function", "function": {"name": "bash", "arguments": json.dumps({"command": cmd})}}


def traj(n_steps=2, exit_status="Submitted", format_error=False, reasoning=True):
    msgs = [{"role": "system", "content": "sys"}, {"role": "user", "content": "<pr_description>fix bug</pr_description>"}]
    for i in range(n_steps):
        msgs.append({"role": "assistant", "content": f"THOUGHT: step {i}", "tool_calls": [call(f"c{i}", f"ls {i}")],
                     "reasoning_content": f"think {i}" if reasoning else None, "function_call": None,
                     "extra": {"actions": [], "cost": 0.0}})
        msgs.append({"role": "tool", "tool_call_id": f"c{i}", "content": "<returncode>0</returncode>", "extra": {}})
        if format_error and i == 0:
            msgs.append({"role": "user", "content": "Tool call error: ...", "extra": {}})
    msgs.append({"role": "assistant", "content": "done", "reasoning_content": "submit" if reasoning else None,
                 "tool_calls": [call("cz", "echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && git diff")], "extra": {}})
    msgs.append({"role": "exit", "content": "diff", "extra": {"exit_status": exit_status, "submission": "diff"}})
    return {"info": {"exit_status": exit_status, "submission": "diff"}, "messages": msgs,
            "trajectory_format": "mini-swe-agent-1.1"}


class T(unittest.TestCase):
    def run_conv(self, runs, resolved, *extra):
        with tempfile.TemporaryDirectory() as d:
            dirs = []
            for k, run in enumerate(runs):
                rd = os.path.join(d, f"run{k}")
                for iid, t in run.items():
                    os.makedirs(os.path.join(rd, iid))
                    json.dump(t, open(os.path.join(rd, iid, f"{iid}.traj.json"), "w"))
                dirs.append(rd)
            rep = os.path.join(d, "report.json")
            json.dump({"resolved_ids": resolved, "unresolved_ids": []}, open(rep, "w"))
            out = os.path.join(d, "out.jsonl")
            p = subprocess.run([sys.executable, SCRIPT, out, *dirs, "--resolved", rep, *extra], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            return [json.loads(l) for l in open(out)], p.stderr

    def test_basic_and_filters(self):
        recs, err = self.run_conv([{"a__1": traj(), "b__2": traj(exit_status="LimitsExceeded"),
                                    "c__3": traj(format_error=True), "d__4": traj()}], ["a__1", "b__2", "c__3"])
        self.assertEqual([r["gold"]["instance_id"] for r in recs], ["a__1"])  # d__4 unresolved, b limits, c format error
        r = recs[0]
        roles = [m["role"] for m in r["messages"]]
        self.assertEqual(roles, ["system", "user", "assistant", "tool", "assistant", "tool", "assistant"])
        self.assertEqual(r["messages"][2]["tool_calls"][0]["function"]["arguments"], {"command": "ls 0"})
        self.assertEqual(r["messages"][2]["reasoning_content"], "think 0")
        self.assertNotIn("extra", r["messages"][2])
        self.assertEqual(json.loads(r["tools"])[0]["function"]["name"], "bash")

    def test_shortest_per_instance(self):
        recs, _ = self.run_conv([{"a__1": traj(n_steps=4)}, {"a__1": traj(n_steps=1)}], ["a__1"])
        self.assertEqual(len(recs), 1)
        self.assertEqual(sum(m["role"] == "assistant" for m in recs[0]["messages"]), 2)

    def test_warns_when_reasoning_missing(self):
        _, err = self.run_conv([{"a__1": traj(reasoning=False)}], ["a__1"])
        self.assertIn("WARNING: no assistant turn has reasoning_content", err)

    def test_renders_with_official_template(self):
        recs, _ = self.run_conv([{"a__1": traj()}], ["a__1"])
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import render_chat as R  # noqa: PLC0415
        tpl = R.make_env().from_string(open(os.path.join(ROOT, "tools", "qwen3_5_chat_template.jinja")).read())
        text, spans = R.train_spans(tpl, recs[0]["messages"], json.loads(recs[0]["tools"]))
        self.assertEqual(len(spans), 3)
        self.assertTrue(all(R.has_thinking(text[s:e]) for s, e in spans))
        self.assertIn("<function=bash>", text)


if __name__ == "__main__":
    unittest.main()
