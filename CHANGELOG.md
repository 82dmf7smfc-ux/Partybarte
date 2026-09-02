# Changelog

All notable changes to this project are recorded here.

The format follows Keep a Changelog. Versions follow Semantic Versioning.

## [Unreleased]

### Added
- Time-of-day filter. `--start-time` and `--end-time` on the Python tool, and a
  matching pair of boxes with shift presets in the browser tool, narrow the
  report to a range of clock hours so it can cover one shift. The range is half
  open, so two shifts add up to one day with nothing counted twice, and a start
  later than the end wraps past midnight for the night shift. Alarms are picked
  by the time they started, the same rule the trailing window uses. The chosen
  hours are printed on the workbook, the deck, the page, and the CSV export.
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
