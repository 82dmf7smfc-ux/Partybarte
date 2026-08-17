"""Check that the version number matches everywhere it is written down.

The version lives in two places in the repository and a third place in git:

    alarm_pareto/__init__.py   __version__ = "1.4.0"
    CHANGELOG.md               ## [1.4.0] - 2026-08-17
    the git tag                v1.4.0

They are one fact, so they must agree. They drifted once already: the package
still read 1.0.0 long after the repository had tagged 1.3.0. Nothing caught it,
because nothing was looking. This script looks.

Run it by hand:

    python tools/check_version.py

It exits 0 when the two files agree and 1 when they do not, so CI can gate on
it. It also backs the release-on-stamp workflow, which asks it which version
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

# "## [1.4.0] - 2026-08-17". The Unreleased heading has no version number, so
# this pattern skips over it and finds the newest real release below it.
VERSION_HEADING = re.compile(r"^##\s*\[(\d+\.\d+\.\d+)\]")
VERSION_ASSIGN = re.compile(r"""^__version__\s*=\s*['\"](\d+\.\d+\.\d+)['\"]""", re.M)


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
    if changelog and package and changelog != package:
        problems.append(
            "The version numbers disagree.\n"
            "  CHANGELOG.md newest release: {}\n"
            "  alarm_pareto/__init__.py:    {}\n"
            "Stamping a release means moving both, and then tagging v{}.".format(
                changelog, package, changelog
            )
        )

    if problems:
        print("Version check failed.\n", file=sys.stderr)
        for problem in problems:
            print(problem, file=sys.stderr)
            print(file=sys.stderr)
        return 1

    print("Version check passed: {} in both the changelog and the package.".format(changelog))
    return 0


if __name__ == "__main__":
    sys.exit(main())
