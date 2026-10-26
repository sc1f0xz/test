"""allenai/TMax-15K: 14.6k terminal tasks with pytest initial/final-state verifiers + container definition.
Prompt-only: run the teacher in the container (Harbor/Docker), score with test_final_state.
Gold carries everything needed to build the environment.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "allenai/TMax-15K"


def convert(row):
    return record([{"role": "user", "content": row["description"]}],
                  [tool("bash", "Run a shell command in the task container.",
                        {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]})],
                  f"{SRC}#{row.get('task_id')}",
                  {"type": "container_pytest", "domain": row.get("domain"), "skill_type": row.get("skill_type"),
                   "test_initial_state": row.get("test_initial_state"), "test_final_state": row.get("test_final_state"),
                   "container_def": row.get("container_def"), "truth": row.get("truth")})


if __name__ == "__main__":
    main(convert)
