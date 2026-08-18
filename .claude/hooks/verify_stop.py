#!/usr/bin/env python3
"""Check the work before the session goes quiet.

Claude Code runs this when Claude is about to stop. If the analysis code was
touched and a check is failing, this sends Claude back to fix it instead of
letting a broken change sit in the working tree.

Only checks that can actually run here are run. On a machine with no packages
installed the Python suite is skipped rather than reported as a failure.

To avoid a loop, this blocks at most once. If Claude has already been sent back
and the checks still fail, the result is reported and the session is allowed to
end, so a human can look at it.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

# Files where a mistake changes the numbers the tool reports.
ANALYSIS_PATHS = ("alarm_pareto/", "alarm_pareto.html", "tests/", "tools/")


def read_event():
    try:
        return json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return {}


def run(cmd, timeout=180):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode, (result.stdout + result.stderr).strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
        return None, str(exc)


def changed_files():
    code, out = run(["git", "status", "--porcelain"], timeout=30)
    if code != 0:
        return []
    names = []
    for line in out.splitlines():
        name = line[3:].strip()
        if "->" in name:
            name = name.split("->")[-1].strip()
        names.append(name)
    return names


def python_can_run():
    for candidate in (".venv/bin/python", ".venv/Scripts/python.exe", "python3", "python"):
        if Path(candidate).exists() or shutil.which(candidate):
            code, _ = run([candidate, "-c", "import pytest, pandas"], timeout=60)
            if code == 0:
                return candidate
    return None


def main():
    event = read_event()

    # Already sent Claude back once. Do not do it again.
    already_blocked = bool(event.get("stop_hook_active"))

    changed = changed_files()
    touched = [f for f in changed if f.startswith(ANALYSIS_PATHS)]
    if not touched:
        return 0

    failures = []
    ran = []

    # The browser tool against the golden file.
    if shutil.which("node") and Path("tools/check_parity.mjs").exists():
        code, out = run(["node", "tools/check_parity.mjs"])
        ran.append("parity check")
        if code != 0:
            failures.append("Parity check failed.\n" + out)

    # The Python analysis against the same golden file.
    python = python_can_run()
    if python:
        code, out = run([python, "-m", "pytest", "-q"])
        ran.append("Python tests")
        if code != 0:
            failures.append("Python tests failed.\n" + out[-3000:])

    if not failures:
        if ran and not already_blocked:
            print("Verified before stopping. No problems found in: " + ", ".join(ran) + ".")
        # A changed analysis usually deserves a changelog line.
        if any(f.startswith(("alarm_pareto/", "alarm_pareto.html")) for f in touched):
            if "CHANGELOG.md" not in changed:
                print(
                    "Note: the analysis changed but CHANGELOG.md did not. "
                    "Add a line under 'Unreleased' if this change is worth recording."
                )
        return 0

    report = "\n\n".join(failures)

    if already_blocked:
        print(
            "Checks are still failing. Reporting instead of retrying again:\n\n" + report
        )
        return 0

    print(
        "Do not stop yet. The analysis code changed and a check is failing.\n\n"
        + report
        + "\n\nFix the cause. Do not update tests/data/expected_summary.json to make "
        "this pass unless you have confirmed the new numbers by hand.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
