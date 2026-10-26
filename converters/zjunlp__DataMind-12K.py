"""zjunlp/DataMind-12K (MIT): data-analysis agent trajectories (Python + SQL) with <think> and ground truth.
TRAIN split only (test = BIRD/DAEval/TableBench evals). Gold = reward_model.ground_truth.

The raw data uses a TEXT-TAG protocol: assistant writes <code>...</code>, the environment answers as a USER
message <interpreter>...</interpreter>, the final answer is <answer>...</answer>. Training on that as-is teaches
the model to print <code> instead of making real tool calls (and the per-user-turn split would strip thinking from
every earlier step). Default (NATIVE_TOOLS=1) re-expresses the SAME content in the native Qwen3.5 tool protocol:
  <code>X</code>            -> tool_call execute_python(code=X)
  user <interpreter>X       -> tool message X
  <answer>X</answer>        -> assistant content X
  system prompt             -> tag-protocol sections removed (tools are described by the `tools` schema instead)
NATIVE_TOOLS=0 keeps the raw tag protocol.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "zjunlp/DataMind-12K"
NATIVE = os.environ.get("NATIVE_TOOLS", "1") == "1"

PY_TOOL = tool(
    "execute_python",
    "Execute Python code in a persistent session and return stdout. pandas/numpy/sklearn are available. "
    "For SQLite sources two helpers exist: get_db_info() prints the schema; "
    "execute_sql(sql, output_path) runs a query and saves the result as CSV.",
    {"type": "object", "properties": {"code": {"type": "string", "description": "Python code to run"}},
     "required": ["code"]},
)

_THINK = re.compile(r"<think>(.*?)</think>", re.S)
_CODE = re.compile(r"<code>(.*?)</code>", re.S)
_ANSWER = re.compile(r"<answer>(.*?)</answer>", re.S)
_INTERP = re.compile(r"^\s*<interpreter>(.*?)</interpreter>\s*$", re.S)
_FENCE = re.compile(r"^\s*```(?:python|py)?\s*\n(.*?)\n?```\s*$", re.S)
# sections of the system prompt that only describe the text-tag protocol
_SP_PROTOCOL = re.compile(r"# Problem-Solving Protocol\n.*?(?=\n# )", re.S)
_SP_TAGNOTE = re.compile(r"\n1\. Avoid including irrelevant commentary outside of the designated tags[^\n]*")


def _system(text):
    text = _SP_PROTOCOL.sub("", text)
    return _SP_TAGNOTE.sub("", text).strip()


def _assistant(text):
    reasoning = "\n\n".join(t.strip() for t in _THINK.findall(text)) or None
    codes = _CODE.findall(text)
    answers = _ANSWER.findall(text)
    rest = _ANSWER.sub("", _CODE.sub("", _THINK.sub("", text))).strip()
    if rest:
        raise ValueError(f"text outside tags: {rest[:80]!r}")
    calls = []
    for c in codes:
        m = _FENCE.match(c)
        calls.append({"type": "function", "function": {"name": "execute_python",
                                                       "arguments": {"code": (m.group(1) if m else c).strip()}}})
    return assistant_msg("\n\n".join(a.strip() for a in answers), reasoning, calls, parse_inline=False)


def convert(row):
    traj = row.get("trajectory") or row["prompt"]
    gt = (row.get("reward_model") or {}).get("ground_truth") or {}
    gold = {"answer": gt.get("ground_truth"), "db_id": row.get("db_id"), "data_source": row.get("data_source")}
    src = f"{SRC}#{row.get('task_id')}"
    if not NATIVE:
        return record([generic_message(m) for m in traj], None, src, gold)
    msgs = []
    for m in traj:
        role, content = m["role"], m["content"] or ""
        if role == "system":
            msgs.append({"role": "system", "content": _system(content)})
        elif role == "assistant":
            msgs.append(_assistant(content))
        elif role == "user" and _INTERP.match(content):
            if not (msgs and msgs[-1].get("tool_calls")):
                raise ValueError("interpreter output without a preceding code call")
            msgs.append({"role": "tool", "content": _INTERP.match(content).group(1).strip()})
        else:
            msgs.append({"role": role, "content": content})
    return record(msgs, [PY_TOOL], src, gold)


if __name__ == "__main__":
    main(convert)
