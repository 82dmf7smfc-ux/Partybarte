# Contributing

This guide explains how to work on the project. It is written for a smart reader
who may not be a full-time Python programmer.

## Ground rules

- The tools must run fully offline. Never add a runtime network call.
- Use only these Python packages: pandas, numpy, openpyxl, python-pptx,
  matplotlib, pytest. Every new package is an IT approval request, so ask first.
- Keep the browser tool a single self-contained HTML file. No outside scripts,
  no content delivery networks, no fonts fetched from the web.
- Match the writing style of the existing comments. Short sentences. Plain
  words. No em dashes.

## Set up a development environment

You need Python and the pinned packages. On a machine with internet:

    python -m venv .venv
    .venv\Scripts\python.exe -m pip install -r requirements.txt

On an offline machine, get the wheel files from IT and run `setup_venv.bat`
with the wheel folder. See the README for details.

## Run the tests

    .venv\Scripts\python.exe -m pytest -q

The tests use a small hand-built sample log. The correct answers were worked out
by hand and stored in `tests/data/expected_summary.json`. If a change makes a
test fail, the change altered the analysis. Confirm the new numbers are right
before you update the golden file.

## Branch and pull request workflow

- `main` is the trunk. It should always pass CI.
- Do your work on a branch. Give it a short, clear name.
- Open a pull request into `main`. CI runs the tests on your branch.
- Keep the changelog current. Add a line under "Unreleased" in `CHANGELOG.md`.

## Add support for a new tool vendor

You do not need to change any Python file. Open
`alarm_pareto/config/vendor_columns.json`. Copy a block. Rename it. Change the
column names on the right to match the new file headers. The internal names on
the left stay the same. The README explains what each internal name means.

The browser tool does not use this file. It guesses columns and lets the user
fix them in the page.

## Keep the two tools in agreement

The browser tool and the Python tool must produce the same numbers for the same
input. When you change the analysis in one, change it in the other, and check
both against the sample log.

## Cut a release

Releases are built and published by GitHub Actions. To make one:

    git tag v1.2.0
    git push origin v1.2.0

The release workflow runs the tests, builds the two zip packages, and attaches
them to a new GitHub Release. It uses `tools/build_zips.py`, so the packages are
the same every time.
