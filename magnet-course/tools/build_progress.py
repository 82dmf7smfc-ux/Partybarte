"""Generate the class status table in PROGRESS.md from the syllabus.

The table is regenerated rather than hand maintained so that the class list, the
titles, and the source keys cannot drift from the syllabus. Status, date, word
count and open questions are preserved across regeneration: they are read back
out of the existing PROGRESS.md before the file is rewritten.

Usage:
    python3 tools/build_progress.py
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "PROGRESS.md"
MARK_START = "<!-- BEGIN GENERATED TABLE -->"
MARK_END = "<!-- END GENERATED TABLE -->"


def existing_rows():
    """Map class id to the editable cells, so regeneration does not lose work."""
    if not OUT.exists():
        return {}
    rows = {}
    for line in OUT.read_text().splitlines():
        if not line.startswith("| c"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 8:
            rows[cells[0]] = {"status": cells[4], "date": cells[5],
                              "words": cells[6], "questions": cells[7]}
    return rows


def main():
    syl = json.loads(subprocess.run(
        [sys.executable, str(ROOT / "tools" / "extract_syllabus.py"),
         str(ROOT / "syllabus" / "magnet-bench-syllabus.html")],
        capture_output=True, text=True, check=True).stdout)

    keep = existing_rows()
    lines = [
        "| id | # | unit | class | status | date | words | open questions | sources |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for c in syl["classes"]:
        k = keep.get(c["id"], {})
        lines.append("| %s | %02d | %s | %s | %s | %s | %s | %s | %s |" % (
            c["id"], c["number"], c["unit"].replace("Unit ", "U"), c["title"],
            k.get("status", "not started"), k.get("date", ""), k.get("words", ""),
            k.get("questions", ""),
            " ".join(s["key"] for s in c["sources"]) or "none listed",
        ))

    table = "\n".join(lines)
    text = OUT.read_text() if OUT.exists() else ""
    if MARK_START in text and MARK_END in text:
        text = re.sub(
            re.escape(MARK_START) + r".*?" + re.escape(MARK_END),
            MARK_START + "\n\n" + table + "\n\n" + MARK_END, text, flags=re.S)
    else:
        text = text.rstrip() + "\n\n" + MARK_START + "\n\n" + table + "\n\n" + MARK_END + "\n"
    OUT.write_text(text)
    done = sum(1 for c in syl["classes"] if keep.get(c["id"], {}).get("status", "").startswith("done"))
    print("wrote table: %d classes, %d marked done, %d hours of material planned"
          % (len(syl["classes"]), done, round(syl["total_minutes"] / 60)))


if __name__ == "__main__":
    main()
