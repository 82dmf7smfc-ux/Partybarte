"""Attempt to fetch every URL in library/sources.json, append the outcome to
library/verified.log, and write the result back into sources.json.

This records what actually happened, failures included. A blocked or dead link
is a result worth keeping, not something to retry until the log looks clean.
The "contains" line stays UNKNOWN until a human or a later session has actually
read the source, because a title is not evidence of contents.

Usage:
    python3 tools/verify_sources.py             # attempt every source
    python3 tools/verify_sources.py hall coils  # attempt named keys only
"""

import json
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "library" / "sources.json"
LOG = ROOT / "library" / "verified.log"
TIMEOUT = "25"


def attempt(url):
    """Return (result, detail). result is ok, http_NNN, blocked, or error."""
    proc = subprocess.run(
        ["curl", "-sS", "-o", "/dev/null", "-L", "--max-time", TIMEOUT,
         "-w", "%{http_code} %{size_download}B %{content_type}", url],
        capture_output=True, text=True,
    )
    err = " ".join(proc.stderr.split())
    out = proc.stdout.strip()
    if proc.returncode != 0:
        if "CONNECT tunnel failed" in err or "403" in err:
            return "blocked", "egress proxy refused CONNECT (%s)" % err
        return "error", err or "curl exit %d" % proc.returncode
    code = out.split(" ", 1)[0]
    return ("ok" if code.startswith("2") else "http_%s" % code), out


def main():
    data = json.loads(SOURCES.read_text())
    keys = sys.argv[1:] or list(data["sources"])
    today = date.today().isoformat()
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = ["\n=== verification pass %s (%d of %d sources) ===\n"
             % (stamp, len(keys), len(data["sources"]))]
    tally = {}
    for key in keys:
        src = data["sources"][key]
        result, detail = attempt(src["url"])
        tally[result] = tally.get(result, 0) + 1
        v = src.setdefault("verification", {})
        v["last_attempt"] = today
        v["result"] = result
        v["detail"] = detail
        lines.append(
            "%s  %-12s %-8s %s\n"
            "                          detail:   %s\n"
            "                          contains: %s\n"
            % (today, key, result, src["url"], detail,
               v.get("contains") or "UNKNOWN, never fetched, do not cite")
        )
        print("%-12s %-8s %s" % (key, result, src["url"][:64]))

    lines.append("summary: %s\n" % ", ".join("%s=%d" % kv for kv in sorted(tally.items())))
    with LOG.open("a") as fh:
        fh.writelines(lines)
    SOURCES.write_text(json.dumps(data, indent=1) + "\n")
    print("\n" + lines[-1].strip())


if __name__ == "__main__":
    main()
