"""Generate library/export.bib from library/sources.json.

Every entry carries a note recording its verification state. Entries built from
sources that were never fetched say so, in the entry, because a .bib file is
exactly the artifact that gets copied into a document years later by someone who
has forgotten where it came from.

Regenerate at every unit tag, per CLAUDE.md.

Usage:
    python3 tools/build_bib.py
"""

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "library" / "sources.json"
OUT = ROOT / "library" / "export.bib"

ENTRY_TYPE = {
    "lecture notes": "techreport", "lecture slides": "misc",
    "lecture archive": "misc", "proceedings": "book",
    "conference proceedings": "inproceedings",
    "conference presentation": "misc", "conference programme": "misc",
    "course archive": "misc", "journal article": "article",
    "preprint": "misc", "tutorial paper": "misc",
    "software documentation": "manual", "software manual": "manual",
    "software tutorial": "misc", "software FAQ": "misc",
    "software repository": "misc", "software package": "misc",
    "software index": "misc", "vendor white paper": "techreport",
    "vendor blog post": "misc", "industry guideline": "techreport",
    "industry standard portal": "misc", "national laboratory report": "techreport",
    "technical note": "techreport", "standard": "techreport",
    "standards body landing page": "misc", "topic page": "misc",
    "bibliography": "misc", "unknown": "misc",
}


def escape(s):
    return s.replace("&", r"\&").replace("%", r"\%").replace("_", r"\_")


def main():
    data = json.loads(SOURCES.read_text())
    today = date.today().isoformat()
    verified = [k for k, v in data["sources"].items()
                if v["verification"]["result"] == "ok"]

    out = [
        "%% library/export.bib",
        "%% Generated %s by tools/build_bib.py from library/sources.json." % today,
        "%% Do not edit by hand. Regenerate at every unit tag.",
        "%%",
        "%% VERIFICATION STATE: %d of %d entries resolved."
        % (len(verified), len(data["sources"])),
        "%%",
        "%% Titles and URLs below are transcribed from the course syllabus, which",
        "%% is the user's own document. They are NOT evidence that the source",
        "%% exists at that URL, says what the title suggests, or is by the author",
        "%% implied. Each entry states its own verification result. An entry whose",
        "%% note says it was never fetched must not be cited. See",
        "%% library/verified.log.",
        "",
    ]

    for key, s in sorted(data["sources"].items()):
        et = ENTRY_TYPE.get(s["type"], "misc")
        fields = [("title", escape(s["title"]))]
        if et in ("techreport", "manual", "book"):
            fields.append(("institution" if et == "techreport" else "organization",
                           escape(s["publisher"])))
        else:
            fields.append(("howpublished", escape(s["publisher"])))
        if s["year"]:
            fields.append(("year", str(s["year"])))
        fields.append(("url", s["url"]))
        fields.append(("urldate", s["verification"]["last_attempt"] or "never attempted"))

        note = []
        r = s["verification"]["result"]
        if r == "ok":
            note.append("URL resolved %s." % s["verification"]["last_attempt"])
        else:
            note.append("NOT VERIFIED. Fetch attempted %s, result: %s. "
                        "Do not cite until fetched and read."
                        % (s["verification"]["last_attempt"] or "never", r))
        if not s["year"]:
            note.append("Year unknown, needs fetch.")
        if not s["free"]:
            note.append("Paywalled.")
        if s["free_substitute_note"]:
            note.append("Free instead: %s" % s["free_substitute_note"])
        if s["cited_by_classes"]:
            note.append("Planned for classes: %s." % ", ".join(s["cited_by_classes"]))
        else:
            note.append("Not cited by any class; appendix only.")
        fields.append(("note", escape(" ".join(note))))
        if et == "techreport" and "institution" not in dict(fields):
            fields.append(("institution", escape(s["publisher"])))

        out.append("@%s{%s," % (et, key))
        width = max(len(f) for f, _ in fields)
        for name, value in fields:
            out.append("  %-*s = {%s}," % (width, name, value))
        out.append("}")
        out.append("")

    OUT.write_text("\n".join(out))
    print("wrote %s: %d entries, %d verified" % (OUT.relative_to(ROOT),
                                                 len(data["sources"]), len(verified)))


if __name__ == "__main__":
    main()
