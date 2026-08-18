# Working agreement for this project

This file is read at the start of every Claude Code session. It holds the rules
that are not obvious from the code. Read it before you change anything.

The rules below are not style preferences. Each one exists because breaking it
makes the tool unusable on a fab bench. A change that violates a hard rule is a
broken change, even if the tests pass.

## What this project is

Two tools that read a semiconductor tool's alarm log and rank faults by how
often they happen and by how much downtime they cause.

- `alarm_pareto.html` is the browser tool. One file. No install. This is what
  people actually use on the bench.
- The `alarm_pareto` Python package writes an Excel workbook with native charts
  and a PowerPoint deck. This is for when those exact file formats are needed.

Both use the same math. That is the central fact about this codebase.

## Hard rules

These are enforced by a hook. An edit that breaks one is blocked, not warned.

1. **No network calls at runtime.** Not in Python, not in JavaScript. The tools
   run on machines with no internet and often no route out at all. No
   `requests`, no `urllib`, no `fetch`, no `XMLHttpRequest`, no remote URL in
   shipped code. This is the rule that gets the tool approved for the bench.
2. **No new runtime dependencies.** The approved list is pandas, numpy,
   openpyxl, python-pptx, matplotlib, and pytest. Every addition is an IT
   approval request that takes weeks. If a task seems to need a new package, say
   so and stop. Do not add it. The standard library is always fine.
3. **`alarm_pareto.html` stays one self-contained file.** No script tags
   pointing outward, no content delivery network, no web fonts, no external
   stylesheet. Someone copies this file to a USB stick and it has to work.
4. **Versions stay pinned.** `requirements.txt` holds exact versions, never
   ranges. This tool has to build the same way in eighteen months.

## The parity rule

The analysis is written twice. Once in Python, once in JavaScript. They must
agree.

If you change the math in one, change it in the other in the same commit. Then
run the parity check:

    node tools/check_parity.mjs

`tests/data/expected_summary.json` is the golden file. It governs both tools.
The numbers in it were worked out by hand. If a change makes it fail, the change
altered the analysis. That is the point of the file. Confirm the new numbers are
right by hand before you update it. Never update the golden file to make a test
go green.

The overlap merge in `merged_seconds` and `mergedSeconds` is the highest risk
code in the project. Two downtime numbers exist and must never be mixed:

- **Attributed downtime.** Each alarm gets credit for its own full duration.
  Sums to more than wall clock. Use it to rank which fault costs the most.
- **Wall-clock downtime.** Overlapping alarms are merged first, so shared time
  counts once. Use it to answer how long the tool was actually down.

`alarm_pareto.html` also carries its own copy of the sample log in `SAMPLE_CSV`.
It must stay identical to `tests/data/sample_alarm_log.csv`. The parity check
verifies this.

Two rules about time. Both were bugs once.

- **Timestamps are read as UTC, never as local time.** An alarm log carries no
  timezone, so both tools treat the times as plain clock numbers. If the browser
  tool used local time, an alarm spanning a daylight saving change would measure
  differently depending on where the laptop is. Never use `getHours` and friends
  in the browser tool. Use the `getUTC` versions.
- **An impossible date is rejected, not nudged.** JavaScript turns month 13 into
  January and February 30th into March 2nd. That invents alarms. `utcDate` reads
  the pieces back out and returns null if they changed.

Ties in a ranking are broken by name, in both tools. Without that the order
depends on how each tool happened to group the rows, and a Pareto chart is read
top to bottom.

## Writing style

Match the existing voice. It is written for a smart reader who is not a
full-time programmer. This applies to comments, docstrings, documentation,
commit messages, and anything shown to a user.

- Short sentences. One idea each.
- Plain words. Say "use" and not "utilize".
- **No em dashes.** Use a period or a comma. This one is checked by a hook.
- Explain why, not just what. A comment that restates the code is noise.
- Say what a reader should do when something goes wrong.

## How to verify a change

Run these before you say a change is done. Do not report success without them.

    node tools/check_parity.mjs      # browser tool agrees with the golden file
    python -m pytest -q              # the Python analysis is still correct

If a Python package is missing, see `.claude/skills/offline-setup`. Do not
install anything outside `requirements.txt` to make a test pass.

## Layout

    alarm_pareto/parse.py         read the log file into a table
    alarm_pareto/normalize.py     rename vendor columns to internal names
    alarm_pareto/window.py        keep the trailing window of rows
    alarm_pareto/aggregate.py     the math, and the overlap merge
    alarm_pareto/render_xlsx.py   write the Excel workbook
    alarm_pareto/render_pptx.py   write the PowerPoint deck
    alarm_pareto/main.py          wire the steps together
    alarm_pareto/config/vendor_columns.json   column mapping per vendor

    alarm_pareto.html             the whole browser tool, one file

    tools/browser_core.mjs        load the browser code so tests can call it
    tools/browser_summary.mjs     run the browser analysis, print JSON
    tools/check_parity.mjs        compare the browser tool to the golden file
    tools/build_zips.py           build the release packages

Adding a new vendor is a JSON edit, not a code change. See
`.claude/skills/add-vendor`.

## Habits that make changes good here

- Change the smallest thing that solves the problem. This code is read by people
  who did not write it.
- When you fix a bug in the analysis, add a test that fails without the fix.
- Keep `CHANGELOG.md` current. Add a line under "Unreleased".
- Do not reformat code you did not otherwise change.
- If a task conflicts with a hard rule, stop and say so. Do not find a clever
  way around the rule.
