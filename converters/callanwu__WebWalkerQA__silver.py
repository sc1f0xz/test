"""callanwu/WebWalkerQA (split silver ONLY; 'main' is the eval) (Apache-2.0): website-navigation QA (official sites,
not wiki) with gold answer + root_url + golden_path. Prompt-only for search/browse agents; reward = answer match
(LLM-judge or normalised string). The root_url is passed as a hint in the user turn (as in the original task).
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "callanwu/WebWalkerQA:silver"
WEB_TOOLS = [tool("web_search", "Search the web.", {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}),
             tool("browse", "Open a URL and return its text.", {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]})]


def convert(row):
    info = row.get("info") or {}
    user = f"{row['question']}\n(เว็บไซต์เริ่มต้น / start website: {row.get('root_url')})"
    return record([{"role": "user", "content": user}], WEB_TOOLS, SRC,
                  {"answer": row["answer"], "golden_path": info.get("golden_path"), "type": info.get("type"),
                   "difficulty": info.get("difficulty_level"), "lang": info.get("lang")})


if __name__ == "__main__":
    main(convert)
