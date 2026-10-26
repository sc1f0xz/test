"""Unit tests: python3 -m unittest discover -s verifiers/tests -t ."""
import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from verifiers import constraints, json_schema, math_answer, regex_check, safe_exec, sql_exec, think_format, toolcall  # noqa: E402


class TestToolCall(unittest.TestCase):
    def test_exact_unordered_parallel(self):
        gold = [{"get_weather": {"city": "Bangkok"}}, {"get_time": {"tz": "Asia/Bangkok"}}]
        pred = [{"type": "function", "function": {"name": "get_time", "arguments": '{"tz": "asia/bangkok"}'}},
                {"name": "get_weather", "arguments": {"city": "Bangkok"}}]
        r = toolcall.score_calls(pred, gold)
        self.assertTrue(r["exact"])
        self.assertEqual(r["name_f1"], 1.0)

    def test_ordered_mismatch(self):
        gold = [{"name": "a", "arguments": {}}, {"name": "b", "arguments": {}}]
        pred = [{"name": "b", "arguments": {}}, {"name": "a", "arguments": {}}]
        self.assertFalse(toolcall.score_calls(pred, gold, ordered=True)["exact"])
        self.assertTrue(toolcall.score_calls(pred, gold, ordered=False)["exact"])

    def test_numeric_string_and_wrong_arg(self):
        gold = [{"name": "f", "arguments": {"n": 5, "x": 0.1}}]
        self.assertTrue(toolcall.score_calls([{"name": "f", "arguments": {"n": "5", "x": 0.1000000001}}], gold)["exact"])
        self.assertFalse(toolcall.score_calls([{"name": "f", "arguments": {"n": 6, "x": 0.1}}], gold)["exact"])

    def test_no_call(self):
        self.assertTrue(toolcall.score_calls([], [])["no_call_correct"])
        self.assertFalse(toolcall.score_calls([{"name": "f", "arguments": {}}], "[]")["exact"])

    def test_alternatives(self):
        gold = [{"name": "f", "arguments": {"unit": ["celsius", ""], "city": ["Bangkok", "BKK"]}}]
        self.assertTrue(toolcall.score_calls([{"name": "f", "arguments": {"city": "BKK"}}], gold, gold_alternatives=True)["exact"])
        self.assertFalse(toolcall.score_calls([{"name": "f", "arguments": {"unit": "celsius"}}], gold, gold_alternatives=True)["exact"])

    def test_schema_validation(self):
        tools = [{"type": "function", "function": {"name": "f", "parameters": {
            "type": "object", "properties": {"mode": {"type": "string", "enum": ["a", "b"]}, "q": {"type": "string"}},
            "required": ["q"]}}}]
        self.assertEqual(toolcall.validate_against_schema({"name": "f", "arguments": {"q": "x", "mode": "a"}}, tools), [])
        errs = toolcall.validate_against_schema({"name": "f", "arguments": {"mode": "c", "z": 1}}, tools)
        self.assertEqual(len(errs), 3)

    def test_bad_pred(self):
        self.assertIn("error", toolcall.score_calls("not json", [{"name": "f", "arguments": {}}]))


class TestJsonSchema(unittest.TestCase):
    schema = {"type": "object", "properties": {"age": {"type": "integer", "minimum": 0},
                                               "tags": {"type": "array", "items": {"enum": ["a", "b"]}}},
              "required": ["age"], "additionalProperties": False}

    def test_fenced_with_think(self):
        r = json_schema.check('<think>{"age": -1}</think>Here:\n```json\n{"age": 3, "tags": ["a"]}\n```', self.schema)
        self.assertTrue(r["ok"], r)

    def test_errors(self):
        r = json_schema.check('Result: {"age": -1, "tags": ["c"], "x": 1} done', self.schema)
        self.assertFalse(r["ok"])
        self.assertEqual(len(r["errors"]), 3)

    def test_nojson(self):
        self.assertFalse(json_schema.check("nothing", self.schema)["ok"])


class TestSafeExec(unittest.TestCase):
    def test_function_tests(self):
        code = "def add(a, b):\n    return a + b\n"
        self.assertTrue(safe_exec.run_function_tests(code, "assert add(2, 3) == 5")["passed"])
        self.assertFalse(safe_exec.run_function_tests(code, "assert add(2, 3) == 6")["passed"])
        self.assertTrue(safe_exec.run_function_tests(code, "def check(c):\n    assert c(1, 1) == 2", entry_point="add")["passed"])
        self.assertTrue(safe_exec.run_function_tests(code, "def test_x():\n    assert add(0, 0) == 0")["passed"])

    def test_timeout(self):
        r = safe_exec.run_function_tests("while True: pass", "", timeout=1)
        self.assertFalse(r["passed"])

    def test_stdio(self):
        code = "a, b = map(int, input().split())\nprint(a + b)\n"
        self.assertTrue(safe_exec.run_stdio_tests(code, [("1 2\n", "3\n"), ("5 5", "10")])["passed"])
        self.assertFalse(safe_exec.run_stdio_tests(code, [("1 2\n", "4\n")])["passed"])

    def test_cwd_isolated(self):
        r = safe_exec.run_function_tests("import os\nopen('x.txt','w').write('1')", "assert os.path.exists('x.txt')")
        self.assertTrue(r["passed"])


class TestMath(unittest.TestCase):
    def test_boxed(self):
        self.assertTrue(math_answer.check(r"<think>maybe \boxed{3}</think> so \boxed{\dfrac{1}{2}}", r"\frac12")["ok"])
        self.assertTrue(math_answer.check(r"\boxed{0.5}", "1/2")["ok"])
        self.assertTrue(math_answer.check(r"The answer is \boxed{1,000}", "1000")["ok"])
        self.assertTrue(math_answer.check(r"\boxed{90^\circ}", "90")["ok"])
        self.assertFalse(math_answer.check(r"\boxed{3}", "4")["ok"])

    def test_fallbacks(self):
        self.assertTrue(math_answer.check("so #### 42", "42")["ok"])
        self.assertTrue(math_answer.check("ดังนั้น คำตอบคือ 7", "7")["ok"])
        self.assertTrue(math_answer.check(r"\boxed{(2, 1)}", "(1,2)")["ok"])

    def test_text_answers_no_false_positive(self):
        # regression (audit 2): \text{..} was stripped to "" on both sides -> any two text answers "matched"
        self.assertFalse(math_answer.check(r"\boxed{\text{Tuesday}}", r"\text{Monday}")["ok"])
        self.assertFalse(math_answer.check(r"\boxed{\mathrm{A}}", r"\mathrm{B}")["ok"])
        self.assertFalse(math_answer.check(r"\boxed{}", r"\text{x}")["ok"])
        self.assertTrue(math_answer.check(r"\boxed{\text{Monday}}", "Monday")["ok"])
        self.assertTrue(math_answer.check(r"\boxed{\text{(B)}}", "B")["ok"])
        self.assertTrue(math_answer.check(r"\boxed{5\text{ cm}}", "5")["ok"])


class TestConstraints(unittest.TestCase):
    def test_check_all(self):
        resp = "<think>plan</think>hello world, this is fine. P.S. bye"
        r = constraints.check_all(resp, ["keywords:existence", "length_constraints:number_words", "detectable_content:postscript"],
                                  [{"keywords": ["world"]}, {"relation": "at most", "num_words": 10}, {"postscript_marker": "P.S."}])
        self.assertTrue(r["all_ok"], r)
        r = constraints.check_all(resp, ["punctuation:no_comma"])
        self.assertFalse(r["all_ok"])

    def test_thai_language_and_unsupported(self):
        self.assertTrue(constraints.check_all("สวัสดีครับ ยินดีต้อนรับ", ["language:response_language"], [{"language": "th"}])["all_ok"])
        r = constraints.check_all("x", ["made:up"])
        self.assertEqual(r["unsupported"], ["made:up"])
        self.assertFalse(r["all_ok"])

    def test_json_and_case(self):
        self.assertTrue(constraints.check_all('```json\n{"a":1}\n```', ["detectable_format:json_format"])["all_ok"])
        self.assertTrue(constraints.check_all("all lower", ["change_case:english_lowercase"])["all_ok"])


class TestSQL(unittest.TestCase):
    def setUp(self):
        fd, self.db = tempfile.mkstemp(suffix=".sqlite")
        os.close(fd)
        con = sqlite3.connect(self.db)
        con.executescript("create table t(id int, name text, score real);"
                          "insert into t values (1,'a',1.5),(2,'b',2.5),(3,'c',2.5);")
        con.commit()
        con.close()

    def tearDown(self):
        os.remove(self.db)

    def test_equivalent_queries(self):
        self.assertTrue(sql_exec.check("SELECT name FROM t WHERE score > 2", "select name from t where score >= 2.5", self.db)["ok"])
        self.assertFalse(sql_exec.check("SELECT name FROM t", "select name from t where id=1", self.db)["ok"])

    def test_empty_gold_and_broken_gold(self):
        # regression (audit 2): empty gold result let any empty-result query pass; broken gold crashed
        r = sql_exec.check("SELECT 1 WHERE 0", "SELECT 1 WHERE 0", self.db)
        self.assertFalse(r["ok"])
        self.assertIn("gold result empty", r["error"])
        self.assertTrue(sql_exec.check("SELECT 1 WHERE 0", "SELECT 1 WHERE 0", self.db, allow_empty_gold=True)["ok"])
        self.assertIn("gold:", sql_exec.check("SELECT 1", "SELEC broken", self.db)["error"])

    def test_order_by_and_reject_write(self):
        self.assertFalse(sql_exec.check("select id from t order by id desc", "select id from t order by id", self.db)["ok"])
        self.assertFalse(sql_exec.check("DROP TABLE t", "select 1", self.db)["ok"])
        self.assertFalse(sql_exec.check("select nope from t", "select id from t", self.db)["ok"])


class TestRegex(unittest.TestCase):
    def test_regex(self):
        self.assertTrue(regex_check.check(r"\d{3}-\d{4}", ["555-1234"], ["5551234", "55-1234"])["ok"])
        self.assertFalse(regex_check.check(r"\d+", ["12"], ["34"])["ok"])
        self.assertFalse(regex_check.check(r"(", ["x"], [])["ok"])

    def test_redos_timeout(self):
        r = regex_check.check(r"(a+)+$", ["a"], ["a" * 40 + "!"], timeout=1.0)
        self.assertFalse(r["ok"])


class TestThinkFormat(unittest.TestCase):
    def test_answer(self):
        r = think_format.check("<think>2+2=4</think>\nThe answer is 4.")
        self.assertTrue(r["ok"])
        self.assertEqual(r["answer"], "The answer is 4.")

    def test_tool_calls_json_and_xml(self):
        t = ('<think>need weather</think>\n<tool_call>\n{"name": "w", "arguments": {"c": "BKK"}}\n</tool_call>'
             '<tool_call><function=t><parameter=n>3</parameter></function></tool_call>')
        r = think_format.check(t)
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["tool_calls"], [{"name": "w", "arguments": {"c": "BKK"}}, {"name": "t", "arguments": {"n": 3}}])

    def test_failures(self):
        self.assertFalse(think_format.check("no think here")["ok"])
        self.assertFalse(think_format.check("<think></think>answer")["ok"])
        self.assertFalse(think_format.check("<think>x</think><tool_call>{bad}</tool_call>")["ok"])
        # regression (audit 2): unclosed <parameter> used to pass with empty arguments
        bad = "<think>\nplan\n</think>\n\n<tool_call>\n<function=f>\n<parameter=a>\n1\n</function>\n</tool_call>"
        self.assertFalse(think_format.check(bad)["ok"])


if __name__ == "__main__":
    unittest.main()
