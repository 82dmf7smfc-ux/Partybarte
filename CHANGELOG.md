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
- PM Round Logger: a per-round CSV export named for the date the readings were
  taken rather than the date of export, so back-filling a missed day still
  files it correctly. The cumulative export and the JSON backup are now named
  for the last day they contain.
- PM Round Logger: import accepts many files at once, so a wiped tablet can be
  restored from a whole folder of daily round files in one go. A damaged or
  unrelated file is reported by name and skipped without stopping the rest.
- PM Round Logger: a storage-fullness readout on the Data tab, and a warning
  banner past 80 per cent. A save that fails because storage is full is now
  told apart from a browser that blocks storage outright, and says so.
- `tools/build_zips.py` now also builds `dist/pm_logger.zip`, holding the
  logger, its read me, the tablet capability test and a screenshot. The release
  workflow attaches it alongside the two existing packages.
- `docs/pm_logger_screenshot.png`, so the package explains itself to someone
  opening it cold.
- `pm_logger_capability_test.html`, a standalone offline page that reports what
  a browser opened from a local file is allowed to do, and whether a chosen
  backup folder is remembered across a restart. Kept alongside the logger so
  the question can be re-answered on a new tablet or after a browser change.
- PM Round Logger: version numbers. `APP_VERSION` is shown in the Data tab
  footnote and leads every diagnostics report, and the data records which
  version created it and which last touched it. A `migrateData()` hook exists
  ready for any future change to the stored layout, and refuses to run
  backwards: an older build opened against newer data warns, declines to save
  at all, and leaves the data intact.
- PM Round Logger: a diagnostics panel behind a small footnote on the Data
  tab, closed by default. Reports versions, browser, storage use, data counts,
  browser capabilities, captured errors and usage counters. Tool and reading
  names are excluded unless explicitly ticked, and no reading value ever
  appears. Copy, download as a text file, or clear the error log.
- PM Round Logger: JavaScript errors are captured as they happen into a
  separate storage slot, capped at 20, surviving a browser restart. Kept apart
  from the readings so exports stay clean and clearing them is always safe.
- PM Round Logger: a built-in self-test covering the CSV round trip with
  awkward characters, limit checking at its boundaries, and date arithmetic
  across month ends. It runs against synthetic data, never calls save, and
  verifies the stored readings are byte-identical afterwards.
- `packaging/pm_logger_READ_ME_FIRST.txt`, plain-language instructions for the
  PM Round Logger, including pointing Edge's download folder at OneDrive, how
  to pivot the CSV in Excel, and how to combine a folder of daily files with
  Get Data > From Folder.
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
