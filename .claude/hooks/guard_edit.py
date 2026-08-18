#!/usr/bin/env python3
"""Block an edit that would break a hard rule, before it is written.

Claude Code runs this before every Write, Edit, and NotebookEdit. It reads the
proposed content on standard input as JSON and decides what to do.

The rules live in tools/project_rules.py, shared with tools/check_rules.py and
with continuous integration. This file only handles the editor's side of it: it
pulls the proposed text out of the event and turns a finding into an exit code.

This guard sees edits made through the editor. It does not see a shell redirect
or a sed command, so it is fast feedback rather than the real gate. The real
gate is tools/check_rules.py, which runs on files on disk from a git hook and
from CI.

Exit codes Claude Code understands:
    0  allow, anything on stdout is shown to Claude
    2  deny, stderr explains why
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools import project_rules as rules  # noqa: E402


def load_event():
    try:
        return json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return {}


def proposed_content(event):
    """Return the file path and the text this edit would put in it."""
    tool = event.get("tool_name", "")
    args = event.get("tool_input", {}) or {}
    path = args.get("file_path") or args.get("notebook_path") or ""

    if tool == "Write":
        return path, args.get("content", "")
    if tool == "Edit":
        # Only the incoming text can introduce a problem.
        return path, args.get("new_string", "")
    if tool == "NotebookEdit":
        return path, args.get("new_source", "")
    return path, ""


def relative(path):
    try:
        return str(Path(path).resolve().relative_to(Path.cwd().resolve())).replace("\\", "/")
    except (ValueError, OSError):
        return str(path).replace("\\", "/")


def main():
    event = load_event()
    path, text = proposed_content(event)
    if not path or not text:
        return 0

    denials, warnings = rules.check_text(relative(path), text)

    if denials:
        print("Blocked. This edit breaks a hard rule in CLAUDE.md.\n", file=sys.stderr)
        for denial in denials:
            print("  - " + denial + "\n", file=sys.stderr)
        print("Do not work around this rule. If the task truly needs it, stop "
              "and tell the user why.", file=sys.stderr)
        return 2

    for warning in warnings:
        print("Style note: " + warning)
    return 0


if __name__ == "__main__":
    sys.exit(main())
