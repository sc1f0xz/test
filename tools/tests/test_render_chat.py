"""Tests for tools/render_chat.py against the official Qwen3.5-4B chat template (copied in tools/)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import render_chat as R  # noqa: E402

TPL = os.path.join(ROOT, "tools", "qwen3_5_chat_template.jinja")
TOOLS = [{"type": "function", "function": {"name": "get_weather", "description": "w",
                                           "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}}]
CONV = [
    {"role": "user", "content": "hi"},
    {"role": "assistant", "content": "hello", "reasoning_content": "greet back"},
    {"role": "user", "content": "weather in Bangkok?"},
    {"role": "assistant", "content": "", "reasoning_content": "need tool",
     "tool_calls": [{"type": "function", "function": {"name": "get_weather", "arguments": {"city": "Bangkok"}}}]},
    {"role": "tool", "content": "33C"},
    {"role": "assistant", "content": "It is 33C.", "reasoning_content": "answer"},
]


class T(unittest.TestCase):
    def setUp(self):
        self.tpl = R.make_env().from_string(open(TPL, encoding="utf-8").read())

    def test_split_by_user_turn(self):
        parts = R.split_by_user_turn(CONV)
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0][-1]["content"], "hello")
        self.assertEqual(parts[1], CONV)

    def test_spans_have_thinking_and_xml_tool_call(self):
        for msgs in R.split_by_user_turn(CONV):
            text, spans = R.train_spans(self.tpl, msgs, TOOLS)
            self.assertTrue(spans)
            for s, e in spans:
                seg = text[s:e]
                self.assertIn("<think>", seg)
                self.assertNotEqual(seg.split("<think>")[1].split("</think>")[0].strip(), "")
        text, _ = R.train_spans(self.tpl, CONV, TOOLS)
        self.assertIn("<function=get_weather>", text)
        self.assertIn("<parameter=city>", text)
        # earlier turn ("greet back") must be stripped from history in the final sample
        self.assertNotIn("greet back", text)

    def test_cli_require_think_drops_empty(self):
        rec_ok = {"messages": CONV, "tools": json.dumps(TOOLS), "src": "t#1", "gold": None}
        rec_bad = {"messages": [{"role": "user", "content": "q"}, {"role": "assistant", "content": "a"}], "tools": "[]", "src": "t#2", "gold": None}
        rec_prompt = {"messages": [{"role": "user", "content": "only prompt"}], "tools": "[]", "src": "t#3", "gold": None}
        with tempfile.TemporaryDirectory() as d:
            inp, out = os.path.join(d, "in.jsonl"), os.path.join(d, "out.jsonl")
            open(inp, "w").write("\n".join(json.dumps(r) for r in (rec_ok, rec_bad, rec_prompt)) + "\n")
            r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "render_chat.py"), TPL, inp, out, "--require-think"],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            got = [json.loads(l) for l in open(out)]
            self.assertEqual({g["src"] for g in got}, {"t#1"})   # 2 samples from the 2-user-turn conversation
            self.assertEqual(len(got), 2)
            self.assertEqual(json.loads(r.stderr.strip().splitlines()[-1])["trained_turns_without_thinking"], 1)


if __name__ == "__main__":
    unittest.main()
