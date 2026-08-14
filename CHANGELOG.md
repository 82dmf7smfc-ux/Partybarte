# Changelog

All notable changes to this project are recorded here.

The format follows Keep a Changelog. Versions follow Semantic Versioning.

## [Unreleased]

### Added
- Browser tool: a "First data row" setting. The tool now starts reading at the
  chosen row, skipping any preamble, and reads down until the first blank line.
  The trailing-window date filter then drops older rows.
- Browser tool: column labelling that works with no header row. Each column gets
  a preview and a drop-down to say what it holds (Timestamp, Fault code,
  Description, Equipment, Duration, Alarm state, Ignore, or a typed "Other").
  Headerless files show columns as "Column 1", "Column 2", and so on.
- Manual dispatch trigger for the release workflow, so a release can be cut from
  the Actions tab when a tag cannot be pushed directly.
- Proprietary `LICENSE` (all rights reserved). The license is now included in
  both zip packages.

### Changed
- The release publish step is now idempotent. A re-run uploads the zips and
  overwrites old copies instead of failing.

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
- Project scaffolding: GitHub Actions CI that runs the test suite on every push
  and pull request across Python 3.11 and 3.12, a tag-triggered release
  workflow, `tools/build_zips.py`, `ROADMAP.md`, `CONTRIBUTING.md`, and this
  changelog.
