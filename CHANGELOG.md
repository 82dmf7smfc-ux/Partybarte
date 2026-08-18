# Changelog

All notable changes to this project are recorded here.

The format follows Keep a Changelog. Versions follow Semantic Versioning.

## [Unreleased]

### Added
- Parity check between the browser tool and the Python tool. `tools/check_parity.mjs`
  runs the real JavaScript out of `alarm_pareto.html` on plain Node and compares
  every number to the same golden files the Python tests use. Nothing is copied,
  so the check cannot go stale. It also catches the case where the sample log
  baked into the HTML drifts from `tests/data/sample_alarm_log.csv`. This closes
  the "shared golden fixtures" item on the roadmap.
- Tests for the set and clear pairing path and the paired-interval path, which
  had no coverage. This closes an engineering hygiene item on the roadmap.
- `tests/data/sample_setclear_log.csv` and `tests/data/expected_setclear.json`,
  a hand-worked golden case covering a simple pair, two alarms open at once, a
  clear with no matching set, and a set that never clears.
- CI now runs the parity check on every push and pull request.
- A working agreement for Claude Code. `CLAUDE.md` holds the project rules,
  `.claude/hooks/` enforces the ones that must never be broken, and
  `.claude/skills/` holds step by step procedures for recurring jobs.
  `docs/claude-system.md` explains the setup and how to move it to another
  project.
- Project scaffolding for continuous build and clear history.
- GitHub Actions CI that runs the test suite on every push and pull request,
  across Python 3.11 and 3.12.
- GitHub Actions release workflow that builds the zip packages and publishes
  them as a GitHub Release when a version tag is pushed.
- `tools/build_zips.py`, a standard-library script that builds both zip
  packages the same way every time.
- `ROADMAP.md`, `CONTRIBUTING.md`, and this changelog.

## [1.0.0] - 2026-08-13

### Added
- Python tool. Reads an alarm log, filters to a trailing window measured from
  the latest timestamp in the file, and ranks faults by count and by downtime
  across three grouping levels. Writes an Excel workbook with native charts and
  a PowerPoint deck.
- Two downtime numbers that are never mixed: attributed downtime and true
  wall-clock downtime with an overlap merge.
- Config-driven vendor column mapping, so a new tool format is a JSON edit.
- Browser tool, `alarm_pareto.html`. A single self-contained page that runs
  fully offline with no install. Imports one or more elog files, guesses the
  columns, and shows the Pareto results in the page. Exports a CSV summary and
  supports print to PDF.
- Golden-file test suite with a hand-built sample log, including an overlapping
  alarm pair to exercise the downtime logic.
