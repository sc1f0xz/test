"""Shared helpers for dataset converters.

Target record (one JSON object per line):
{
  "messages": [
    {"role": "system"|"user"|"assistant"|"tool",
     "content": str,
     "reasoning_content": str,            # optional, assistant only
     "tool_calls": [{"type": "function",  # optional, assistant only
                     "function": {"name": str, "arguments": {...dict}}}],
     "name": str                          # optional, tool only
    }, ...],
  "tools": "<JSON string: list of {type:function, function:{name, description, parameters}}>",
  "src": "<hf_id>[:<config>/<split>]#<row id>",
  "gold": <anything the matching verifier needs, or null>
}

Every converter module exposes `SRC` and `convert(row: dict) -> dict | list[dict] | None`
and can be run as a script:  python3 converters/<name>.py in.jsonl > out.jsonl
"""
from __future__ import annotations

import json
import re
import sys
from typing import Any, Callable, Iterable

_THINK_RE = re.compile(r"^\s*<think>(.*?)</think>\s*", re.S)
_CALL_RE = re.compile(r"<tool_call>\s*(.*?)\s*</tool_call>", re.S)
_XML_FN = re.compile(r"<function=([^>\s]+)>(.*?)</function>", re.S)
_XML_PARAM = re.compile(r"<parameter=([^>\s]+)>\s*(.*?)\s*</parameter>", re.S)

ROLE_MAP = {
    "human": "user", "user": "user", "gpt": "assistant", "assistant": "assistant",
    "model": "assistant", "system": "system", "tool": "tool", "function": "tool",
    "observation": "tool", "ipython": "tool", "function_response": "tool",
}


def loads_maybe(v: Any) -> Any:
    """json.loads strings that look like JSON; otherwise return as is."""
    if isinstance(v, str):
        s = v.strip()
        if s[:1] in "[{" and s[-1:] in "]}":
            try:
                return json.loads(s)
            except json.JSONDecodeError:
                pass
    return v


def split_think(text: str | None) -> tuple[str | None, str]:
    """'<think>r</think>answer' -> ('r', 'answer'). Unclosed <think> -> all reasoning."""
    if text is None:
        return None, ""
    m = _THINK_RE.match(text)
    if m:
        return m.group(1).strip(), text[m.end():].strip()
    s = text.lstrip()
    if s.startswith("<think>") and "</think>" not in s:
        return s[len("<think>"):].strip(), ""
    return None, text.strip()


def norm_tool_call(call: Any) -> dict:
    call = loads_maybe(call)
    if not isinstance(call, dict):
        raise ValueError(f"bad tool call {call!r}")
    fn = call.get("function", call)
    if not isinstance(fn, dict):
        raise ValueError(f"bad tool call {call!r}")
    if "name" not in fn and len(fn) == 1:  # {"fn_name": {...}}
        (name, args), = fn.items()
        fn = {"name": name, "arguments": args}
    args = loads_maybe(fn.get("arguments", fn.get("parameters", {})))
    if args in (None, ""):
        args = {}
    if not isinstance(args, dict):
        raise ValueError(f"arguments not an object: {args!r}")
    return {"type": "function", "function": {"name": str(fn["name"]), "arguments": args}}


def parse_inline_tool_calls(text: str) -> tuple[str, list[dict]]:
    """Pull Hermes-JSON or Qwen-XML <tool_call> blocks out of assistant text."""
    calls = []
    for body in _CALL_RE.findall(text or ""):
        m = _XML_FN.search(body)
        if m:
            args = {}
            for k, v in _XML_PARAM.findall(m.group(2)):
                args[k] = loads_maybe(v) if v.strip()[:1] in "[{" else _scalar(v)
            calls.append({"type": "function", "function": {"name": m.group(1), "arguments": args}})
        else:
            calls.append(norm_tool_call(body))
    return _CALL_RE.sub("", text or "").strip(), calls


def _scalar(v: str):
    try:
        return json.loads(v)
    except json.JSONDecodeError:
        return v


def norm_tool_schema(t: Any) -> dict:
    t = loads_maybe(t)
    if "function" in t and isinstance(t["function"], dict):
        f = t["function"]
    else:
        f = t
    params = fix_schema(f.get("parameters", {"type": "object", "properties": {}}))
    return {"type": "function", "function": {"name": f["name"], "description": f.get("description", ""),
                                             "parameters": params}}


def tools_json(tools: Any) -> str:
    tools = loads_maybe(tools)
    if not tools:
        return "[]"
    if isinstance(tools, dict):
        tools = [tools]
    return json.dumps([norm_tool_schema(t) for t in tools], ensure_ascii=False)


def assistant_msg(text: str | None, reasoning: str | None = None, tool_calls: Iterable | None = None,
                  parse_inline: bool = True) -> dict:
    r2, content = split_think(text)
    reasoning = reasoning if reasoning else r2
    calls = [norm_tool_call(c) for c in (tool_calls or [])]
    if parse_inline and "<tool_call>" in content:
        content, inline = parse_inline_tool_calls(content)
        calls += inline
    msg = {"role": "assistant", "content": content}
    if reasoning:
        msg["reasoning_content"] = reasoning
    if calls:
        msg["tool_calls"] = calls
    return msg


def generic_message(m: dict, parse_inline: bool = True) -> dict:
    """OpenAI-ish or ShareGPT message -> target message."""
    role = ROLE_MAP.get(m.get("role", m.get("from", "")), None)
    if role is None:
        raise ValueError(f"unknown role in {m!r}")
    content = m.get("content", m.get("value"))
    if isinstance(content, list):  # [{type:text,text:..}]
        content = "".join(p.get("text", "") for p in content if isinstance(p, dict))
    content = "" if content is None else str(content)
    if role == "assistant":
        return assistant_msg(content, m.get("reasoning_content") or m.get("reasoning") or m.get("thinking"),
                             m.get("tool_calls") or [], parse_inline)
    out = {"role": role, "content": content}
    if role == "tool":
        if m.get("name"):
            out["name"] = m["name"]
        if m.get("tool_call_id"):
            out["tool_call_id"] = m["tool_call_id"]
    return out


def record(messages: list[dict], tools: Any = None, src: str = "", gold: Any = None) -> dict:
    return {"messages": messages, "tools": tools_json(tools), "src": src, "gold": gold}


def validate_record(rec: dict) -> list[str]:
    errs = []
    if set(rec) - {"messages", "tools", "src", "gold", "meta"}:
        errs.append(f"unexpected keys {set(rec) - {'messages', 'tools', 'src', 'gold', 'meta'}}")
    msgs = rec.get("messages")
    if not isinstance(msgs, list) or not msgs:
        return errs + ["messages empty"]
    for i, m in enumerate(msgs):
        if m.get("role") not in {"system", "user", "assistant", "tool"}:
            errs.append(f"msg{i}: bad role {m.get('role')}")
        if not isinstance(m.get("content"), str):
            errs.append(f"msg{i}: content not str")
        if "reasoning_content" in m and (m["role"] != "assistant" or not isinstance(m["reasoning_content"], str)):
            errs.append(f"msg{i}: bad reasoning_content")
        for c in m.get("tool_calls", []) or []:
            f = c.get("function", {})
            if c.get("type") != "function" or not isinstance(f.get("name"), str) or not isinstance(f.get("arguments"), dict):
                errs.append(f"msg{i}: bad tool_call {c}")
    if not isinstance(rec.get("tools"), str):
        errs.append("tools must be a JSON string")
    else:
        try:
            tl = json.loads(rec["tools"])
            assert isinstance(tl, list)
            for t in tl:
                assert t["type"] == "function" and "name" in t["function"]
        except Exception as e:  # noqa: BLE001
            errs.append(f"tools invalid: {e}")
    if not rec.get("src"):
        errs.append("src empty")
    if any(isinstance(m.get("content"), str) and "<image>" in m["content"] for m in msgs):
        errs.append("literal <image> in content (not an image token for Qwen3.5; use meta.images)")
    return errs


IMAGE_PLACEHOLDER_RE = re.compile(r"<image>\s*")


def multimodal_messages(rec: dict, style: str = "hf", image_urls: list[str] | None = None) -> list[dict]:
    """Records keep `content` as plain text; images live in rec["meta"]["images"] (refs, in order) and belong to the
    FIRST user message. This builds the content-list form the model actually needs:
      style="hf"     -> [{"type":"image"}, ..., {"type":"text","text":...}]   (Qwen3.5 chat template / processor;
                        the template renders each as <|vision_start|><|image_pad|><|vision_end|>)
      style="openai" -> [{"type":"image_url","image_url":{"url":u}}, ..., {"type":"text",...}]  (vLLM / llama-server;
                        pass image_urls = data: URLs or http URLs, same order as meta.images)
    A literal "<image>" string is NOT an image for Qwen3.5 (it is just text) - never put it in content."""
    images = ((rec.get("meta") or {}).get("images")) or []
    msgs = [dict(m) for m in rec["messages"]]
    if not images:
        return msgs
    if style == "openai" and (image_urls is None or len(image_urls) != len(images)):
        raise ValueError("style='openai' needs one url per meta.images entry")
    i = next(k for k, m in enumerate(msgs) if m["role"] == "user")
    parts = ([{"type": "image"} for _ in images] if style == "hf"
             else [{"type": "image_url", "image_url": {"url": u}} for u in image_urls])
    msgs[i]["content"] = parts + [{"type": "text", "text": msgs[i]["content"]}]
    return msgs


def iter_rows(path: str | None):
    """Yield dict rows from .jsonl, .json (array) or .parquet (needs pandas+pyarrow); stdin if path is None."""
    if path is None:
        for line in sys.stdin:
            if line.strip():
                yield json.loads(line)
    elif path.endswith(".parquet"):
        import pandas as pd  # noqa: PLC0415
        for r in pd.read_parquet(path).to_dict("records"):
            yield {k: (v.tolist() if hasattr(v, "tolist") else v) for k, v in r.items()}
    else:
        with open(path, encoding="utf-8") as f:
            head = f.read(1)
            while head and head.isspace():
                head = f.read(1)
            f.seek(0)
            if head == "[":
                yield from json.load(f)
            else:
                for line in f:
                    if line.strip():
                        yield json.loads(line)


def main(convert: Callable[[dict], Any], argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    n_in = n_out = n_bad = 0
    for row in iter_rows(argv[0] if argv else None):
        n_in += 1
        try:
            out = convert(row)
        except Exception as e:  # noqa: BLE001
            n_bad += 1
            print(f"skip row {n_in}: {type(e).__name__}: {e}", file=sys.stderr)
            continue
        for rec in ([out] if isinstance(out, dict) else (out or [])):
            errs = validate_record(rec)
            if errs:
                n_bad += 1
                print(f"invalid row {n_in}: {errs[:3]}", file=sys.stderr)
                continue
            n_out += 1
            sys.stdout.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"[{n_in} in, {n_out} out, {n_bad} skipped]", file=sys.stderr)


# --- schema helpers -------------------------------------------------------
_PY_TYPES = {"str": "string", "string": "string", "int": "integer", "integer": "integer", "float": "number",
             "number": "number", "bool": "boolean", "boolean": "boolean", "dict": "object", "object": "object",
             "list": "array", "array": "array", "tuple": "array", "set": "array"}


def json_type(t: Any) -> dict:
    """Map loose type strings ('str, optional', 'List[int]', 'dict') to a JSON-schema fragment."""
    if not isinstance(t, str):
        return {}
    s = t.strip().lower().replace(", optional", "").replace(" optional", "")
    m = re.match(r"(list|array|set|tuple)\[(.+)\]$", s)
    if m:
        inner = json_type(m.group(2))
        return {"type": "array", **({"items": inner} if inner else {})}
    if "|" in s or "union" in s or s in ("any", ""):
        return {}
    return {"type": _PY_TYPES[s]} if s in _PY_TYPES else {}


def fix_schema(params: Any) -> dict:
    """Normalise loose parameter specs into JSON Schema.

    Handles (a) proper JSON schema with python-ish types ('dict','str'),
    (b) xLAM style {param: {type, description, default}} without 'properties'."""
    params = loads_maybe(params) or {}
    if not isinstance(params, dict):
        return {"type": "object", "properties": {}}
    if "properties" not in params and params.get("type") not in ("object", "dict"):
        props, required = {}, []
        for k, spec in params.items():
            spec = spec if isinstance(spec, dict) else {"description": str(spec)}
            p = {**json_type(spec.get("type")), "description": spec.get("description", "")}
            if "enum" in spec:
                p["enum"] = spec["enum"]
            props[k] = p
            if "default" not in spec and "optional" not in str(spec.get("type", "")).lower():
                required.append(k)
        return {"type": "object", "properties": props, "required": required}

    def walk(node):
        if isinstance(node, dict):
            node = dict(node)
            if isinstance(node.get("type"), str) and node["type"].lower() in _PY_TYPES:
                node["type"] = _PY_TYPES[node["type"].lower()]
            for k in ("properties",):
                if isinstance(node.get(k), dict):
                    node[k] = {pk: walk(pv) for pk, pv in node[k].items()}
            if "items" in node:
                node["items"] = walk(node["items"])
            return node
        return node

    out = walk(params)
    out["type"] = "object"
    return out


def tool(name: str, description: str = "", parameters: Any = None) -> dict:
    return {"type": "function", "function": {"name": name, "description": description,
                                             "parameters": fix_schema(parameters or {})}}


def infer_tools_from_calls(messages: list[dict]) -> list[dict]:
    """Build minimal schemas when a dataset doesn't ship tool definitions."""
    seen: dict[str, dict] = {}
    for m in messages:
        for c in m.get("tool_calls", []) or []:
            f = c["function"]
            props = seen.setdefault(f["name"], {})
            for k, v in f["arguments"].items():
                t = ("boolean" if isinstance(v, bool) else "integer" if isinstance(v, int) else
                     "number" if isinstance(v, float) else "array" if isinstance(v, list) else
                     "object" if isinstance(v, dict) else "string")
                props.setdefault(k, {"type": t})
    return [{"type": "function", "function": {"name": n, "description": "(schema inferred from observed calls)",
                                              "parameters": {"type": "object", "properties": p}}}
            for n, p in seen.items()]
