"""HuggingFaceTB/smoltalk2 SFT/smoltalk_systemchats_Qwen3_32B_think (Apache-2.0): everyday chats answered by
Qwen3-32B in thinking mode (<think> in content) — natural short-thinking anchors for easy prompts. Use directly
(sparingly). custom_instructions -> system message.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "HuggingFaceTB/smoltalk2:SFT/smoltalk_systemchats_Qwen3_32B_think"


def convert(row):
    msgs = [generic_message(m) for m in row["messages"]]
    ci = (row.get("chat_template_kwargs") or {}).get("custom_instructions")
    if ci and msgs[0]["role"] != "system":
        msgs.insert(0, {"role": "system", "content": ci})
    return record(msgs, None, SRC, {"source": row.get("source")})


if __name__ == "__main__":
    main(convert)
