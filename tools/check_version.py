"""Check that the version number matches everywhere it is written down.

The version lives in three places in the repository and a fourth place in git:

    alarm_pareto/__init__.py   __version__ = "1.4.0"
    CHANGELOG.md               ## [1.4.0] - 2026-08-17
    pyproject.toml             version = "1.4.0"
    the git tag                v1.4.0

They are one fact, so they must agree. They drifted once already: the package
still read 1.0.0 long after the repository had tagged 1.3.0. Nothing caught it,
because nothing was looking. This script looks.

Run it by hand:

    python tools/check_version.py

It exits 0 when the files agree and 1 when they do not, so CI can gate on it. It also backs the release-on-stamp workflow, which asks it which version
the changelog is claiming:

    python tools/check_version.py --print-changelog-version

Only the standard library is used, on purpose. This has to run anywhere,
including a container with no network and no pandas.
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHANGELOG = ROOT / "CHANGELOG.md"
INIT = ROOT / "alarm_pareto" / "__init__.py"
PYPROJECT = ROOT / "pyproject.toml"

# "## [1.4.0] - 2026-08-17". The Unreleased heading has no version number, so
# this pattern skips over it and finds the newest real release below it.
VERSION_HEADING = re.compile(r"^##\s*\[(\d+\.\d+\.\d+)\]")
VERSION_ASSIGN = re.compile(r"""^__version__\s*=\s*['\"](\d+\.\d+\.\d+)['\"]""", re.M)
# 'version = "1.4.0"' under [project]. Read with a regex rather than a TOML
# parser so this keeps working on a Python without tomllib and stays dependency
# free, which is the whole point of this script.
PYPROJECT_VERSION = re.compile(r"""^version\s*=\s*['\"](\d+\.\d+\.\d+)['\"]""", re.M)


def changelog_version():
    """The newest released version in the changelog, or None if there is none."""
    for line in CHANGELOG.read_text(encoding="utf-8").splitlines():
        found = VERSION_HEADING.match(line)
        if found:
            return found.group(1)
    return None


def package_version():
    """The version the Python package reports, or None if it is missing."""
    found = VERSION_ASSIGN.search(INIT.read_text(encoding="utf-8"))
    return found.group(1) if found else None


def pyproject_version():
    """The version declared in pyproject.toml, or None if it is not there."""
    if not PYPROJECT.exists():
        return None
    found = PYPROJECT_VERSION.search(PYPROJECT.read_text(encoding="utf-8"))
    return found.group(1) if found else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--print-changelog-version",
        action="store_true",
        help="print the newest changelog version and exit, for the workflows",
    )
    args = parser.parse_args()

    changelog = changelog_version()
    package = package_version()
    project = pyproject_version()

    if args.print_changelog_version:
        if changelog is None:
            print("no released version heading found in CHANGELOG.md", file=sys.stderr)
            return 1
        print(changelog)
        return 0

    problems = []
    if changelog is None:
        problems.append(
            "CHANGELOG.md has no released version heading. Expected a line "
            "like '## [1.4.0] - 2026-08-17'."
        )
    if package is None:
        problems.append(
            "alarm_pareto/__init__.py has no __version__. Expected a line "
            'like \'__version__ = "1.4.0"\'.'
        )
    # pyproject.toml is only checked when it exists, so this script keeps
    # working on an older checkout that predates it.
    if PYPROJECT.exists() and project is None:
        problems.append(
            "pyproject.toml has no version. Expected a line under [project] "
            'like \'version = "1.4.0"\'.'
        )

    declared = {
        "CHANGELOG.md newest release": changelog,
        "alarm_pareto/__init__.py": package,
    }
    if PYPROJECT.exists():
        declared["pyproject.toml"] = project

    known = [v for v in declared.values() if v is not None]
    if len(set(known)) > 1:
        lines = ["The version numbers disagree."]
        width = max(len(name) for name in declared)
        for name, value in declared.items():
            lines.append("  {:<{w}}  {}".format(name + ":", value, w=width + 1))
        lines.append(
            "Stamping a release means moving every one of them, and then "
            "tagging v{}.".format(changelog or package)
        )
        problems.append("\n".join(lines))

    if problems:
        print("Version check failed.\n", file=sys.stderr)
        for problem in problems:
            print(problem, file=sys.stderr)
            print(file=sys.stderr)
        return 1

    where = "the changelog, the package and pyproject.toml" if PYPROJECT.exists() \
        else "both the changelog and the package"
    print("Version check passed: {} in {}.".format(changelog, where))
    return 0


if __name__ == "__main__":
    sys.exit(main())
