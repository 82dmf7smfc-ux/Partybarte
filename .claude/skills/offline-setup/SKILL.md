---
name: offline-setup
description: Get the Python tests running when packages are missing, pip cannot reach an index, or the machine has no internet. Use on errors like "No matching distribution found", "Could not find a version", pip timeouts, a missing venv, or when tests cannot run because pandas or pytest is not installed.
---

# Getting the tests to run

This project runs on machines with no internet. Package installs fail in ways
that look like a broken project but are not. Work through this in order.

## First, decide whether you actually need Python here

The browser parity check needs only Node:

    node tools/check_parity.mjs

If the change was only to `alarm_pareto.html`, that check plus continuous
integration may be all you need. Say clearly which checks you ran and which you
could not.

## If a virtual environment already exists

Use its interpreter directly. Do not rely on the shell being activated.

    .venv/bin/python -m pytest -q            # Linux and macOS
    .venv\Scripts\python.exe -m pytest -q    # Windows

## If there is no environment

On a machine with internet:

    python -m venv .venv
    .venv/bin/python -m pip install -r requirements.txt

On a machine without internet, packages come from a wheel folder that IT
supplies:

    python -m venv .venv
    .venv/bin/python -m pip install --no-index --find-links /path/to/wheels -r requirements.txt

On Windows, `setup_venv.bat` does this. Point it at the wheel folder.

## If pip cannot reach an index

Errors like `No matching distribution found for pandas==2.2.2` with
`(from versions: none)` mean there is no package index reachable. This is normal
on a bench machine and in some containers. It is not a project problem.

What to do:

- Do not change the pinned versions in `requirements.txt` to something that
  installs. The pins exist so this builds the same way in eighteen months.
- Do not add or swap packages to get around it.
- Run the checks that do work, say plainly which ones you could not run, and let
  continuous integration cover the rest. It runs the full suite on every push.

## If a wheel version does not match

If IT supplies wheels at different versions than `requirements.txt` names, edit
`requirements.txt` to match the wheels you were given, keep exact pins, and note
the change in `CHANGELOG.md`. Then run the full suite, because a version change
can move numbers.

## What never to do

- Never edit `tests/data/expected_summary.json` to make a test pass.
- Never mark a test as skipped to get a green run.
- Never report a change as verified when the tests did not run. Say which checks
  ran and which did not.
