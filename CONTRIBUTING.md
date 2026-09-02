# Contributing

This guide explains how to work on the code here. It is written for a smart
reader who may not be a full-time Python programmer.

## How the repository is organised

This repository holds more than one project. Each project lives in its own
folder under `projects` and owns its code, its tests, its sample data, and its
read me. Anything shared by every project stays at the root: the pinned package
list, the environment setup script, the pytest settings, the packaging script,
and these documents.

When you add a project, make a new folder under `projects`. Give it a read me,
a `tests` folder, its own `requirements.txt`, and a `conftest.py` that puts the
project folder on the import path, the way `projects/alarm_pareto/conftest.py`
does. Add the new requirements file to the list at the top of the root
`requirements.txt`, and add a row to the project table in the root read me. You
do not have to touch the CI workflow.
It runs `pytest -q` from the root, and `pytest.ini` points that at every project
folder.

Keep projects independent. Do not import one project's code from another. If two
projects genuinely need the same code, say so in the pull request and we will
decide where shared code should live before it is written.

## Ground rules

- These rules apply to every project in the repository, not just one.
- Nothing leaves the building. Never reach the internet, at any point, for any
  reason. No telemetry, no content delivery networks, no fonts fetched from the
  web.
- Talking to equipment is not the same thing. A driver reading a gauge over
  RS-232, or over a socket to a tool on the fab network, is doing its job. The
  rule above is about the internet, not about local links. This wording replaced
  a blanket ban on network calls, which the driver library would have broken on
  its first day for no good reason.
- Every new package is an IT approval request, so ask first. Add a package in the
  same change that first imports it, so nobody is asked to approve a wheel that
  nothing uses. What is pinned today: alarm_pareto uses pandas, numpy, openpyxl,
  python-pptx and matplotlib; fab_drivers uses pyserial; both use pytest.
- Keep the browser tool a single self-contained HTML file. No outside scripts,
  no content delivery networks, no fonts fetched from the web.
- Match the writing style of the existing comments. Short sentences. Plain
  words. No em dashes.

## Set up a development environment

You need Python and the pinned packages. Each project pins what it needs in its
own `requirements.txt`, and the file at the root gathers them. There is one
environment for the whole repository, built at the root and shared by every
project. On a machine with internet, run this from the repository root:

    python -m venv .venv
    .venv\Scripts\python.exe -m pip install -r requirements.txt

On an offline machine, get the wheel files from IT and run `setup_venv.bat`
with the wheel folder. See the README for details.

Adding a package means adding a pinned line to `requirements.txt`, and it means
someone has to get that wheel approved. Ask before you do it.

## Run the tests

From the repository root, this runs every project's tests:

    .venv\Scripts\python.exe -m pytest -q

To run one project's tests while you work on it, name its folder:

    .venv\Scripts\python.exe -m pytest -q projects\alarm_pareto

Naming the folder is the only way to narrow it down. Moving into a project
folder first does not, because pytest looks upward for `pytest.ini`, finds the
one at the root, and runs everything it points at.

The alarm_pareto tests use a small hand-built sample log. The correct answers
were worked out by hand and stored in `tests/data/expected_summary.json`, inside
that project. If a change makes a test fail, the change altered the analysis.
Confirm the new numbers are right before you update the golden file.

## Branch and pull request workflow

- `main` is the trunk. It should always pass CI.
- Do your work on a branch. Give it a short, clear name.
- Open a pull request into `main`. CI runs the tests on your branch.
- Keep the changelog current. Add a line under "Unreleased" in `CHANGELOG.md`.

## Add support for a new tool vendor

This section is about the alarm_pareto project.

You do not need to change any Python file. Open the vendor config at
`projects/alarm_pareto/alarm_pareto/config/vendor_columns.json`. Copy a block.
Rename it. Change the column names on the right to match the new file headers.
The internal names on the left stay the same. That project's read me explains
what each internal name means.

The browser tool does not use this file. It guesses columns and lets the user
fix them in the page.

## Keep the two alarm_pareto tools in agreement

The browser tool and the Python tool must produce the same numbers for the same
input. When you change the analysis in one, change it in the other, and check
both against the sample log.

## Cut a release

Releases are per project. This repository holds more than one tool, and they
ship to different people on different days, so one version number across the
whole repository would be misleading. The tag says which project is being
released.

    git tag alarm-pareto-v1.5.0
    git push origin alarm-pareto-v1.5.0

    git tag fab-drivers-v0.1.0
    git push origin fab-drivers-v0.1.0

The release workflow reads the project name off the tag, runs every project's
tests, builds only that project's packages, and attaches them to a new GitHub
Release. It uses `tools/build_zips.py`, so the packages are the same every time.
A tag that does not name a project is refused, with a message saying the two
forms that work.

Releases v1.0.0 through v1.4.0 were cut before the repository held more than one
project. They were all alarm_pareto. Its version numbers carry on where they left
off, so the next one is `alarm-pareto-v1.5.0`. Only the tag name changed.

To build the packages by hand:

    python tools/build_zips.py                  every project
    python tools/build_zips.py alarm_pareto     one project
