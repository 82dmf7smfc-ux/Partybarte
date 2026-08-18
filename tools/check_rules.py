"""Check files against the project's hard rules.

The rules themselves live in tools/project_rules.py. This script applies them to
files on disk, so they hold no matter how a file was written. An editor guard
only sees edits made through the editor. A shell redirect, a sed command, or a
hand edit all slip past it. This does not.

Run it on everything git tracks:

    python tools/check_rules.py

Run it on what is staged for commit, which is what the git hook does:

    python tools/check_rules.py --staged

It exits non-zero if any hard rule is broken. Style notes are printed but never
fail the run. It uses the standard library only and makes no network call.
"""

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import project_rules as rules  # noqa: E402

SKIP_SUFFIXES = (".png", ".ico", ".zip", ".xlsx", ".pptx")


def git_files(staged):
    """Return the paths to check, relative to the project root."""
    if staged:
        cmd = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"]
    else:
        cmd = ["git", "ls-files"]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    return [line.strip() for line in out.splitlines() if line.strip()]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--staged", action="store_true",
                        help="Check only files staged for commit.")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    all_denials, all_warnings = [], []
    checked = 0

    for rel in git_files(args.staged):
        if rel.endswith(SKIP_SUFFIXES):
            continue
        path = root / rel
        if not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        denials, warnings = rules.check_text(rel, text)
        all_denials.extend(denials)
        all_warnings.extend(warnings)
        checked += 1

    for warning in all_warnings:
        print("Style note: " + warning)

    if all_denials:
        print("", file=sys.stderr)
        print("Blocked. These files break a hard rule in CLAUDE.md.", file=sys.stderr)
        print("", file=sys.stderr)
        for denial in all_denials:
            print("  - " + denial, file=sys.stderr)
            print("", file=sys.stderr)
        print("Do not work around these rules. If the task truly needs one "
              "broken, stop and say why.", file=sys.stderr)
        return 1

    print("Rules check passed. %d files, no hard rule broken." % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
