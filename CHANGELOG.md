# Changelog

All notable changes to this project are recorded here.

The format follows Keep a Changelog. Versions follow Semantic Versioning.

## [Unreleased]

### Added
- PM Round Logger, `pm_logger.html`. A second self-contained browser tool, for
  logging preventative maintenance readings on a daily round. Runs fully
  offline from a local file. Define tools and the readings taken at each, work
  down a round that shows what is still outstanding, and keep the data in
  browser storage. Optional min and max per reading colour an out-of-range
  value without ever refusing to save it. Exports a tidy one-row-per-reading
  CSV for Excel and an exact JSON backup, and imports either one back with a
  merge or replace choice.
- `packaging/pm_logger_READ_ME_FIRST.txt`, plain-language instructions for the
  PM Round Logger, including how to pivot the CSV in Excel.
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
