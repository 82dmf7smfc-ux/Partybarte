# Changelog

All notable changes to this project are recorded here.

The format follows Keep a Changelog. Versions follow Semantic Versioning.

## [Unreleased]

### Added
- A third downtime number, "in range". Overlaps are merged as with wall clock,
  and every fault is also cut down to the parts that fall inside the hours the
  report covers. It answers how much of a shift the tool spent down, which
  neither of the other two numbers can: they credit a fault to the shift it
  started in, whole. Available on both tools, and as
  `--downtime-method in_range` for ranking.
- `alarm_pareto/reporting_range.py`, which works out the blocks of clock time a
  report covers and clips alarms against them. Thirty days of night shift is
  thirty blocks, not one, and that list is what the new number is measured
  against.
- The reports now say how much clock time they cover, in how many blocks, and
  what share of it the tool spent down.
- Import feedback in the browser tool. It now says how much it is reading
  before it starts, and warns when an import is large enough to be slow or to
  risk running the tab out of memory. Reading and analysis block the page, so
  the message is painted before the work starts rather than after it.
- Measured limits for both tools, written up in the README and the browser
  read-me. Neither tool caps the number of rows. The browser tool tops out at
  two to three million rows, and a single file cannot exceed 512 MB.
- Time-of-day filter. `--start-time` and `--end-time` on the Python tool, and a
  matching pair of boxes with shift presets in the browser tool, narrow the
  report to a range of clock hours so it can cover one shift. The range is half
  open, so two shifts add up to one day with nothing counted twice, and a start
  later than the end wraps past midnight for the night shift. Alarms are picked
  by the time they started, the same rule the trailing window uses. The chosen
  hours are printed on the workbook, the deck, the page, and the CSV export.

### Changed
- Expanded the explanation of the night shift in both tools, since a shift
  whose start is later than its end is the one part of the filter that is not
  obvious from reading the code.

### Tests
- `tests/test_night_shift.py`, an exhaustive check of the wrapping case. Every
  one of the 1440 minutes in a day is checked, for every start hour and six
  range lengths, that a range and its complement between them keep every minute
  exactly once. Plus the boundary minutes, month ends, year ends, and a leap
  day.
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
