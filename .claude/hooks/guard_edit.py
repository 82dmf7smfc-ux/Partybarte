#!/usr/bin/env python3
"""Block edits that break a hard rule of this project.

Claude Code runs this before every Write, Edit, and NotebookEdit. It reads the
proposed file content on standard input as JSON and decides what to do.

Two levels of response.

- Deny. The edit does not happen. Used for the four hard rules: no runtime
  network calls, no unapproved dependencies, no outside references in the
  browser tool, and no unpinned versions. Breaking one of these makes the tool
  unusable on a fab bench, so a warning is not enough.
- Warn. The edit happens and a note is added for Claude to see. Used for style,
  where a rule can have a fair exception.

The check runs on the new content only, so existing code is never flagged. It
uses the standard library alone and makes no network call.

Exit codes Claude Code understands:
    0  allow, anything on stdout is shown to Claude
    2  deny, stderr explains why
"""

import json
import re
import sys
from pathlib import Path

# Packages approved for the shipped tools. Adding to this list means an IT
# approval request, so it is deliberately short. Keep it in step with
# requirements.txt and CONTRIBUTING.md.
APPROVED_PACKAGES = {
    "pandas", "numpy", "openpyxl", "pptx", "matplotlib", "pytest",
}

# The standard library is always allowed. This covers what the project uses.
STDLIB_ALLOWED = {
    "argparse", "collections", "contextlib", "csv", "dataclasses", "datetime",
    "functools", "io", "itertools", "json", "math", "os", "pathlib", "re",
    "shutil", "string", "subprocess", "sys", "tempfile", "textwrap", "time",
    "typing", "unittest", "warnings", "zipfile", "hashlib", "statistics",
}

# Paths that ship to the user. Runtime rules apply here. Test and tool files are
# development only, so they are held to a lighter standard.
RUNTIME_PREFIXES = ("alarm_pareto/", "alarm_pareto.html")


def load_event():
    try:
        return json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return {}


def proposed_content(event):
    """Return the text this edit would put in the file, and the file path."""
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


def strip_comments(text, path):
    """Remove comments so a rule written in prose is not mistaken for code."""
    if path.endswith(".py"):
        return "\n".join(re.sub(r"#.*$", "", line) for line in text.splitlines())
    if path.endswith((".html", ".js", ".mjs")):
        text = re.sub(r"/\*[\s\S]*?\*/", "", text)
        text = re.sub(r"<!--[\s\S]*?-->", "", text)
        return "\n".join(re.sub(r"//.*$", "", line) for line in text.splitlines())
    return text


def check_network(code, rel, denials):
    """Rule 1. Shipped code must never reach the network."""
    if not rel.startswith(RUNTIME_PREFIXES):
        return

    patterns = [
        (r"\bimport\s+requests\b|\bfrom\s+requests\b", "the requests package"),
        (r"\bimport\s+urllib|\bfrom\s+urllib\b", "urllib"),
        (r"\bimport\s+http\.client|\bfrom\s+http\b", "http.client"),
        (r"\bimport\s+socket\b", "socket"),
        (r"\bimport\s+ftplib\b|\bimport\s+smtplib\b", "a network module"),
        (r"\bfetch\s*\(", "fetch()"),
        (r"\bXMLHttpRequest\b", "XMLHttpRequest"),
        (r"\bnavigator\.sendBeacon\b", "navigator.sendBeacon"),
        (r"\bnew\s+WebSocket\b", "a WebSocket"),
        (r"\bnew\s+EventSource\b", "an EventSource"),
        (r"""https?://(?!www\.w3\.org)[^\s"'<>)]+""", "a remote URL"),
    ]
    for pattern, label in patterns:
        if re.search(pattern, code):
            denials.append(
                f"{rel} would use {label}. The shipped tools must run fully "
                f"offline. Machines on the bench have no route to the internet, "
                f"and a network call is what gets the tool rejected by IT. "
                f"Solve this without leaving the machine."
            )


def check_dependencies(code, rel, denials):
    """Rule 2. Only approved packages may be imported by shipped code."""
    if not rel.endswith(".py"):
        return
    if rel.startswith("tests/") or rel.startswith("tools/"):
        return

    for match in re.finditer(r"^\s*(?:from|import)\s+([A-Za-z_][\w.]*)", code, re.MULTILINE):
        top = match.group(1).split(".")[0]
        if top in APPROVED_PACKAGES or top in STDLIB_ALLOWED:
            continue
        if top in {"alarm_pareto", "tests", "conftest"} or match.group(0).lstrip().startswith("from ."):
            continue
        denials.append(
            f"{rel} would import '{top}', which is not on the approved list. "
            f"Approved packages are: {', '.join(sorted(APPROVED_PACKAGES))}. "
            f"Every new package is an IT approval request that takes weeks. "
            f"Use the standard library, or stop and ask before adding this."
        )


def check_single_file_html(code, rel, denials):
    """Rule 3. The browser tool stays one self-contained file."""
    if not rel.endswith("alarm_pareto.html"):
        return

    if re.search(r"<script[^>]+\bsrc\s*=", code, re.IGNORECASE):
        denials.append(
            f"{rel} would load a script from outside the file. The browser tool "
            f"has to work as a single file copied to a USB stick. Inline the "
            f"code instead."
        )
    if re.search(r"<link[^>]+\brel\s*=\s*[\"']?stylesheet", code, re.IGNORECASE):
        denials.append(
            f"{rel} would load an outside stylesheet. Put the styles in the "
            f"<style> block in the same file."
        )
    if re.search(r"@import\s+url|fonts\.googleapis|cdn\.|unpkg\.com|jsdelivr", code, re.IGNORECASE):
        denials.append(
            f"{rel} would pull a font or a library from a content delivery "
            f"network. The file must work with no internet."
        )


def check_pinned_versions(code, rel, denials):
    """Rule 4. Requirements stay pinned to exact versions."""
    if not rel.endswith("requirements.txt"):
        return
    for line in code.splitlines():
        line = line.split("#")[0].strip()
        if not line:
            continue
        if re.search(r"[><~!]=|\*", line) or "==" not in line:
            denials.append(
                f"requirements.txt line '{line}' is not pinned to one exact "
                f"version. This tool has to build the same way in eighteen "
                f"months. Write it as name==version."
            )


def check_style(text, rel, warnings):
    """Style. Worth a note, not worth blocking."""
    if rel.endswith((".json", ".lock")) or "/data/" in rel:
        return

    if "—" in text or "–" in text:
        warnings.append(
            "This text contains an em dash or en dash. The project writes "
            "without them. Use a period or a comma instead."
        )

    if rel.endswith(".py"):
        for line in text.splitlines():
            if len(line) > 100 and not line.lstrip().startswith(("#", '"', "'")):
                warnings.append("A line is over 100 characters. Keep code easy to read on a laptop.")
                break


def main():
    event = load_event()
    path, text = proposed_content(event)
    if not path or not text:
        return 0

    rel = relative(path)
    code = strip_comments(text, rel)

    denials, warnings = [], []
    check_network(code, rel, denials)
    check_dependencies(code, rel, denials)
    check_single_file_html(code, rel, denials)
    check_pinned_versions(code, rel, denials)
    check_style(text, rel, warnings)

    if denials:
        print("Blocked. This edit breaks a hard rule in CLAUDE.md.\n", file=sys.stderr)
        for d in denials:
            print("  - " + d + "\n", file=sys.stderr)
        print(
            "Do not work around this rule. If the task truly needs it, stop and "
            "tell the user why.", file=sys.stderr,
        )
        return 2

    if warnings:
        for w in warnings:
            print("Style note: " + w)

    return 0


if __name__ == "__main__":
    sys.exit(main())
