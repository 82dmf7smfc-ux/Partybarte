# Changelog

All notable changes to this project are recorded here.

The format follows Keep a Changelog. Versions follow Semantic Versioning.

## [Unreleased]

## [1.3.0] - 2026-08-14

### Added
- Browser tool: estimate downtime from the messages. A new "Derive from
  messages (pair down/up per chamber)" mode reads the chamber name from the
  message text, then pairs a "down" message with the next "online" message for
  that chamber. Each pair becomes an estimated downtime interval, so the same
  attributed and wall-clock math, the Paretos, and the CSV export are reused.
  Repeat downs while a chamber is already down are ignored, an "up" with no open
  down is ignored, and a down that never closes is capped at the last timestamp
  and flagged. A plain fault can optionally start downtime too.
- Browser tool: estimated-downtime Paretos by Chamber/Module and by Fault
  (ID + text), plus tool-level numbers. "Restricted" is any chamber offline
  (the union) and "full tool down" is every chamber seen offline at once (the
  intersection). Everything derived is labelled "estimated".
- Browser tool: a paired-interval validation table (chamber, start, end,
  duration, down message, up message) with flags for unresolved and
  suspiciously long intervals, so the estimates can be checked by eye.
- Browser tool: editable down/up phrase lists and a chamber-name list for the
  derive mode, with defaults seeded near the top of the file, because vendors
  word these messages differently. A second built-in "message-log sample"
  button demonstrates the mode offline.
- Browser tool: full column vocabulary for real elogs. Roles now include Date,
  Time, a combined Timestamp, Severity, Module/equipment, Message ID, and
  Description. Date and Time in separate columns are combined into one event
  time. Several columns tagged Description are joined, so a message split by
  commas across columns is put back together.
- Browser tool: severity filter. Rank only faults, only warnings, or both, with
  preset buttons and a checkbox per severity found. Default is faults and
  warnings, so routine trace and prompt lines are left out.
- Browser tool: the fault Pareto pairs each Message ID with its most common
  message text, so bars read "ID - description".
- Browser tool: "Auto-map columns" guesses every role from the column values
  (works with no headers), and the column list is now a vertical layout that
  scrolls down instead of sideways.

### Changed
- Browser tool: the fault grouping level is now "Fault (ID + text)"; the other
  levels are "Module" and "Message text".

## [1.1.0] - 2026-08-14

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
