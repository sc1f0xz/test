"""agentica-org/DeepScaleR-Preview-Dataset (MIT): ~40k AIME/AMC/Omni-MATH/STILL problems with answers — the
standard prompt set of L1 / AdaptThink / Thinkless / AutoThink. NOTE: contains past AIME/AMC (do not eval on those).
Gold -> verifiers.math_answer.check. Role: prompt-only.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: E402,F401,F403

SRC = "agentica-org/DeepScaleR-Preview-Dataset"


def convert(row):
    return record([{"role": "user", "content": row["problem"]}], None, SRC, {"answer": row["answer"]})


if __name__ == "__main__":
    main(convert)
