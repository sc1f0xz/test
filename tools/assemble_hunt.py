"""Rebuild DATASET_HUNT.md from hunt_sections/{A..L}.md (keeps the header block of the current file)."""
import re

secs = "ABCDEFGHIJKL"
cur = open("DATASET_HUNT.md", encoding="utf-8").read()
head = cur.split("## สารบัญ")[0] + "## สารบัญ\n"
toc, bodies = [], []
for s in secs:
    t = open(f"hunt_sections/{s}.md", encoding="utf-8").read().strip()
    title = t.splitlines()[0].lstrip("# ").strip()
    n = len(re.findall(r"^\| \d+ \|", t, re.M))
    anchor = f"sec-{s.lower()}"
    toc.append(f"- [{title}](#{anchor}) — {n} รายการในตารางหลัก")
    t = re.sub(r"```json\s*(TOP_CANDIDATES)?\s*\n(.*?)```",
               lambda m: "<details><summary>TOP_CANDIDATES (json)</summary>\n\n```json\n" + m.group(2).strip() + "\n```\n</details>",
               t, flags=re.S)
    t = re.sub(r"^## ", f'<a id="{anchor}"></a>\n\n## ', t, count=1)
    bodies.append(t)
open("DATASET_HUNT.md", "w", encoding="utf-8").write(head + "\n".join(toc) + "\n\n---\n\n" + "\n\n---\n\n".join(bodies) + "\n")
print("ok", len(toc))
