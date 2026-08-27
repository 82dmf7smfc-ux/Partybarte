"""Parse the syllabus HTML and emit its S (sources) and UNITS (classes) objects as JSON.

The syllabus HTML is the source of truth for scope. Nothing in this repository
should hand-transcribe it. Run this to regenerate the machine-readable views.

Usage:
    python3 tools/extract_syllabus.py syllabus/magnet-bench-syllabus.html
"""

import json
import re
import sys
from pathlib import Path

# The syllabus embeds two JavaScript object literals, S and UNITS. They are
# almost JSON: keys are bare identifiers and strings use double quotes. We
# convert bare keys to quoted keys, then parse as JSON.


def extract_literal(text, name, opener, closer):
    """Return the source text of the literal assigned to `name`."""
    start = text.index("const %s=%s" % (name, opener))
    start = text.index(opener, start)
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    raise ValueError("unterminated literal for %s" % name)


def jsify(src):
    """Quote bare object keys so the literal becomes valid JSON."""
    out = []
    in_string = False
    escape = False
    i = 0
    while i < len(src):
        ch = src[i]
        if in_string:
            out.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
            continue
        # A bare key is an identifier that follows { or , and precedes :
        m = re.match(r"([A-Za-z_$][A-Za-z0-9_$]*)\s*:", src[i:])
        prev = next((c for c in reversed(out) if not c.isspace()), None)
        if m and prev in ("{", ","):
            out.append('"%s":' % m.group(1))
            i += m.end()
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def main():
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "syllabus/magnet-bench-syllabus.html")
    text = path.read_text(encoding="utf-8")

    sources = json.loads(jsify(extract_literal(text, "S", "{", "}")))
    units = json.loads(jsify(extract_literal(text, "UNITS", "[", "]")))
    lib = json.loads(jsify(extract_literal(text, "LIB", "[", "]")))

    classes = []
    n = 0
    for u in units:
        for c in u["classes"]:
            n += 1
            classes.append(
                {
                    "number": n,
                    "id": c["id"],
                    "unit": u["n"],
                    "unit_title": u["title"],
                    "title": c["t"],
                    "minutes": c["len"],
                    "objective": c["obj"],
                    "beats": [dict(zip(("time", "text"), b.split("|", 1))) for b in c["beats"]],
                    "sources": [{"key": s["k"], "note": s["n"]} for s in c["src"]],
                    "artifact": c["art"],
                }
            )

    out = {
        "class_count": len(classes),
        "total_minutes": sum(c["minutes"] for c in classes),
        "source_count": len(sources),
        "sources": sources,
        "units": [
            {"n": u["n"], "title": u["title"], "aim": u["aim"], "check": u["check"], "risk": u["risk"]}
            for u in units
        ],
        "classes": classes,
        "library_groups": lib,
    }
    json.dump(out, sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main()
