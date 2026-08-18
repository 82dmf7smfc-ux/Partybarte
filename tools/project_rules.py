"""The project's hard rules, in one place.

These rules are checked from three directions, and all three read this file so
they cannot drift apart:

- `.claude/hooks/guard_edit.py` checks an edit before it is written.
- `tools/check_rules.py` checks files on disk, from a git hook or by hand.
- Continuous integration runs `tools/check_rules.py` on every push, which is
  the backstop. A local hook can be skipped or never installed. CI cannot.

Two levels of finding.

- A denial. The rule exists because breaking it makes the tools unusable on a
  fab bench. No network calls, no unapproved packages, no outside references in
  the browser file, no unpinned versions.
- A warning. Style, where a fair exception exists. Warnings never fail a build.

This module uses the standard library only and makes no network call.
"""

import re

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

# Paths that ship to the user. The runtime rules apply here. Test and tool files
# are development only, so they are held to a lighter standard.
RUNTIME_PREFIXES = ("alarm_pareto/", "alarm_pareto.html")

# Files that are data, not prose or code. Style rules do not apply.
DATA_SUFFIXES = (".json", ".csv", ".lock", ".png", ".ico")

# Files that have to contain the characters the style rule looks for, because
# they are the ones doing the looking. Without this the guard warns about its
# own source on every run, and a warning nobody can act on is how warnings stop
# being read.
STYLE_EXEMPT = ("tools/project_rules.py", "tests/test_project_setup.py")


def strip_comments(text, path):
    """Remove comments so a rule written in prose is not read as code."""
    if path.endswith(".py"):
        return "\n".join(re.sub(r"#.*$", "", line) for line in text.splitlines())
    if path.endswith((".html", ".js", ".mjs")):
        text = re.sub(r"/\*[\s\S]*?\*/", "", text)
        text = re.sub(r"<!--[\s\S]*?-->", "", text)
        return "\n".join(re.sub(r"//.*$", "", line) for line in text.splitlines())
    return text


def _check_network(code, rel, denials):
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
                "%s would use %s. The shipped tools must run fully offline. "
                "Machines on the bench have no route to the internet, and a "
                "network call is what gets the tool rejected by IT. Solve this "
                "without leaving the machine." % (rel, label)
            )


def _check_dependencies(code, rel, denials):
    """Rule 2. Only approved packages may be imported by shipped code."""
    if not rel.endswith(".py"):
        return
    if rel.startswith(("tests/", "tools/", ".claude/")):
        return
    for match in re.finditer(r"^\s*(?:from|import)\s+([A-Za-z_][\w.]*)", code, re.MULTILINE):
        top = match.group(1).split(".")[0]
        if top in APPROVED_PACKAGES or top in STDLIB_ALLOWED:
            continue
        if top in {"alarm_pareto", "tests", "conftest"}:
            continue
        if match.group(0).lstrip().startswith("from ."):
            continue
        denials.append(
            "%s would import '%s', which is not on the approved list. Approved "
            "packages are: %s. Every new package is an IT approval request that "
            "takes weeks. Use the standard library, or stop and ask before "
            "adding this." % (rel, top, ", ".join(sorted(APPROVED_PACKAGES)))
        )


def _check_single_file_html(code, rel, denials):
    """Rule 3. The browser tool stays one self-contained file."""
    if not rel.endswith("alarm_pareto.html"):
        return
    if re.search(r"<script[^>]+\bsrc\s*=", code, re.IGNORECASE):
        denials.append(
            "%s would load a script from outside the file. The browser tool has "
            "to work as a single file copied to a USB stick. Inline the code "
            "instead." % rel
        )
    if re.search(r"<link[^>]+\brel\s*=\s*[\"']?stylesheet", code, re.IGNORECASE):
        denials.append(
            "%s would load an outside stylesheet. Put the styles in the <style> "
            "block in the same file." % rel
        )
    if re.search(r"@import\s+url|fonts\.googleapis|cdn\.|unpkg\.com|jsdelivr", code, re.IGNORECASE):
        denials.append(
            "%s would pull a font or a library from a content delivery network. "
            "The file must work with no internet." % rel
        )


def _check_pinned_versions(code, rel, denials):
    """Rule 4. Requirements stay pinned to exact versions."""
    if not rel.endswith("requirements.txt"):
        return
    for line in code.splitlines():
        line = line.split("#")[0].strip()
        if not line:
            continue
        if re.search(r"[><~!]=|\*", line) or "==" not in line:
            denials.append(
                "requirements.txt line '%s' is not pinned to one exact version. "
                "This tool has to build the same way in eighteen months. Write "
                "it as name==version." % line
            )


def _check_local_time(code, rel, denials):
    """Rule 5. The browser tool reads timestamps as UTC, never as local time.

    This was a real bug. Local time made an alarm spanning a daylight saving
    change measure differently depending on where the laptop was.
    """
    if not rel.endswith("alarm_pareto.html"):
        return
    local_getters = re.findall(
        r"\.get(?:FullYear|Month|Date|Hours|Minutes|Seconds|Day)\s*\(", code
    )
    if local_getters:
        denials.append(
            "%s uses a local time getter such as getHours. The browser tool "
            "reads timestamps as UTC so the same log gives the same downtime on "
            "every machine. Use the getUTC versions instead." % rel
        )


def _check_style(text, rel, warnings):
    """Style. Worth a note, never worth blocking."""
    if rel.endswith(DATA_SUFFIXES) or "/data/" in rel or rel in STYLE_EXEMPT:
        return
    if "—" in text or "–" in text:
        warnings.append(
            "%s contains an em dash or en dash. The project writes without "
            "them. Use a period or a comma instead." % rel
        )


def check_text(rel, text):
    """Check one file's content. Returns (denials, warnings).

    rel is the path relative to the project root, using forward slashes.
    """
    code = strip_comments(text, rel)
    denials, warnings = [], []
    _check_network(code, rel, denials)
    _check_dependencies(code, rel, denials)
    _check_single_file_html(code, rel, denials)
    _check_pinned_versions(code, rel, denials)
    _check_local_time(code, rel, denials)
    _check_style(text, rel, warnings)
    return denials, warnings
