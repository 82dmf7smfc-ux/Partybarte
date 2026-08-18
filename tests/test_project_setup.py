"""Check the working agreement itself, not the analysis.

The hooks and skills in .claude are part of the project. They are also easy to
break quietly, because nothing imports them and no test touched them before.
A hook with a syntax error simply stops running, and a skill whose description
does not say when to use it simply never loads. Both fail silently, which is the
worst way to fail.

What these tests do and do not prove:

- They prove each skill is well formed, that its name matches its folder, and
  that its description says when to use it rather than only what it is.
- They prove the rule engine still blocks what it is supposed to block and
  still allows the project's own files.
- They do NOT prove a skill actually loads at the right moment. That depends on
  a model reading the description and choosing it, so it needs an eval that runs
  the model, not a unit test. The description checks here are the part that can
  be tested offline, which is what this project needs.
"""

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
SKILLS_DIR = ROOT / ".claude" / "skills"
HOOKS_DIR = ROOT / ".claude" / "hooks"

sys.path.insert(0, str(ROOT))
from tools import project_rules as rules  # noqa: E402

SKILL_FILES = sorted(SKILLS_DIR.glob("*/SKILL.md"))

# Words that show a description says when to reach for the skill, not just what
# it is about. A description without any of these tends not to get picked up.
TRIGGER_WORDS = ["use when", "use whenever", "use this", "use on", "use for"]


def test_there_are_skills_to_check():
    assert SKILL_FILES, "No skills found in .claude/skills"


@pytest.mark.parametrize("skill_path", SKILL_FILES, ids=lambda p: p.parent.name)
def test_skill_is_well_formed(skill_path):
    text = skill_path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    assert match, "%s must start with a YAML front matter block" % skill_path

    front = match.group(1)
    name = re.search(r"^name:\s*(.+)$", front, re.MULTILINE)
    description = re.search(r"^description:\s*(.+)$", front, re.MULTILINE)

    assert name, "%s has no name" % skill_path
    assert description, "%s has no description" % skill_path

    # The name has to match the folder or the skill cannot be invoked by name.
    assert name.group(1).strip() == skill_path.parent.name, (
        "%s: name '%s' does not match its folder" % (skill_path, name.group(1).strip())
    )

    body = text[match.end():].strip()
    assert len(body) > 200, "%s has almost no content" % skill_path


@pytest.mark.parametrize("skill_path", SKILL_FILES, ids=lambda p: p.parent.name)
def test_skill_description_says_when_to_use_it(skill_path):
    """A description that only says what a skill is about does not get picked."""
    text = skill_path.read_text(encoding="utf-8")
    description = re.search(r"^description:\s*(.+)$", text, re.MULTILINE).group(1).lower()

    assert len(description) > 80, (
        "%s: the description is too short to tell one situation from another" % skill_path
    )
    assert any(word in description for word in TRIGGER_WORDS), (
        "%s: the description never says when to use the skill. Add a sentence "
        "starting with 'Use when'." % skill_path
    )


@pytest.mark.parametrize("skill_path", SKILL_FILES, ids=lambda p: p.parent.name)
def test_skill_follows_the_writing_style(skill_path):
    text = skill_path.read_text(encoding="utf-8")
    assert "—" not in text and "–" not in text, (
        "%s contains an em dash or en dash. The project writes without them." % skill_path
    )


def test_hooks_are_valid_python():
    """A hook with a syntax error stops running and says nothing."""
    import ast
    for hook in sorted(HOOKS_DIR.glob("*.py")):
        ast.parse(hook.read_text(encoding="utf-8"), filename=str(hook))


# ---------------------------------------------------------------------------
# The rule engine. These are the rules the project cannot ship without.
# ---------------------------------------------------------------------------

BLOCKED = [
    ("alarm_pareto/parse.py", "import requests", "a network package"),
    ("alarm_pareto/main.py", "from urllib.request import urlopen", "urllib"),
    ("alarm_pareto.html", 'fetch("/api/data")', "fetch in the browser tool"),
    ("alarm_pareto.html", '<script src="https://cdn.example.com/x.js"></script>', "an outside script"),
    ("alarm_pareto.html", "var h = d.getHours();", "local time in the browser tool"),
    ("alarm_pareto/aggregate.py", "import scipy", "an unapproved package"),
    ("requirements.txt", "pandas>=2.0", "an unpinned version"),
]

ALLOWED = [
    ("alarm_pareto/parse.py", "import pandas as pd"),
    ("alarm_pareto/aggregate.py", "import json"),
    ("alarm_pareto/aggregate.py", "from . import normalize as nz"),
    ("alarm_pareto.html", "var h = d.getUTCHours();"),
    ("requirements.txt", "pandas==2.2.2"),
    ("alarm_pareto/parse.py", "# see https://example.com for the format"),
    ("tests/test_thing.py", "import requests"),
]


@pytest.mark.parametrize("path,content,why", BLOCKED, ids=[b[2] for b in BLOCKED])
def test_the_rules_block_what_they_must(path, content, why):
    denials, _ = rules.check_text(path, content)
    assert denials, "%s in %s should have been blocked" % (why, path)


@pytest.mark.parametrize("path,content", ALLOWED, ids=[a[1][:28] for a in ALLOWED])
def test_the_rules_allow_ordinary_code(path, content):
    denials, _ = rules.check_text(path, content)
    assert not denials, "%s in %s should be fine, got %s" % (content, path, denials)


def test_the_rules_allow_every_file_already_in_the_project():
    """A guard with false alarms gets switched off within a week."""
    import subprocess
    listed = subprocess.run(
        ["git", "ls-files"], cwd=str(ROOT), capture_output=True, text=True, check=True
    ).stdout.split()

    problems = []
    for rel in listed:
        if rel.endswith((".png", ".ico", ".zip")):
            continue
        path = ROOT / rel
        if not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        denials, _ = rules.check_text(rel, text)
        problems.extend(denials)

    assert not problems, "The rules flag files already in the project:\n" + "\n".join(problems)
