# Changelog

All notable changes to this project are recorded here.

The format follows Keep a Changelog. Versions follow Semantic Versioning.

## [Unreleased]

### Changed
- Reorganised the repository to hold more than one project. The alarm_pareto
  tool moved from the root into `projects/alarm_pareto`, with its code, tests,
  sample data, packaging read me, screenshot, and read me all inside that
  folder. The pinned package list, the environment setup script, the packaging
  script, and the project documents stayed at the root and are now shared. The
  contents of the two download packages did not change.
- Added `pytest.ini`, so `pytest -q` from the repository root runs every
  project's tests, and two projects can each have a `tests` folder without
  their test files colliding.
- Split the pinned package list. Each project now pins what it imports, in its
  own folder, and the file at the root gathers them. A download package no
  longer asks people to approve packages the tool never imports.
- Releases are now per project, tagged `alarm-pareto-vX.Y.Z` or
  `fab-drivers-vX.Y.Z`. The workflow reads the project off the tag and builds
  only that project's packages. A tag that names no project is refused. The five
  existing releases, v1.0.0 to v1.4.0, were all alarm_pareto and are untouched;
  its numbering carries on at `alarm-pareto-v1.5.0`.
- `tools/build_zips.py` takes an optional project name, and builds everything
  when given none, which is what CI does.
- Reworded the offline rule. It always meant that nothing reaches the internet.
  Read literally it also banned talking to equipment over a local socket, which
  is what the driver library exists to do.

### Added
- `projects/fab_drivers`, a new project. A library of small, read-only
  monitoring drivers for fab equipment. This change adds the shared core only:
  the command policy that enforces read-only, raw frame audit logging, daily CSV
  history, a mock serial port for working with no hardware, the serial
  transport, the driver base class with the one second timeout and two retries,
  and a gentle poller that marks readings stale instead of guessing. No device
  driver yet, so the first one lands in a tested template. 56 tests, none of
  which need hardware.
- `projects/fab_drivers/REVIEW.md`, the handover for a critical second pass. It
  records what was actually verified, what was only assumed, the known weak
  points, and the one place the read-only gate can be bypassed.
- `projects/fab_drivers/CLAUDE.md`, the standing brief for a driver session. The
  ten drivers are built one per session, and each session starts with no memory
  of the last, so the build order and the rules live in the repository rather
  than in anyone's head.
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
