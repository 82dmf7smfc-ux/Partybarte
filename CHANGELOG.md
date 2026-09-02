# Changelog

All notable changes to this project are recorded here.

The format follows Keep a Changelog. Versions follow Semantic Versioning.

## [Unreleased]

### Changed
- The shared trend page generator draws a column on a linear or a logarithmic
  axis, chosen per column by the driver. Pressure runs from atmosphere down to
  1e-9 torr, and on a linear axis every reading below about 1 torr lands on the
  bottom pixel of the chart, so the part of a pumpdown that matters is
  invisible. Three of the ten planned drivers read pressure, so the fix belongs
  in the shared generator rather than in one driver. A log axis is snapped to
  whole decades with one gridline each. A gap still breaks the line, and a zero
  or negative reading becomes a gap too, counted and reported under the chart,
  because a log axis has nowhere to put it.
- The trend page summary table shows a number outside the range 0.01 to 100000
  in scientific notation. A reading of 1e-9 torr previously showed as `0.00`.
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
- `fab_drivers/devices/granville_phillips/`, a read-only driver for the
  Granville-Phillips 275, 375, 350 and 356 pressure gauges. ASCII messages with
  `#` address framing over RS-232 or RS-485. The gauge address is checked
  separately from the command, and the address the instrument echoes back is
  checked against the one that was sent, which is the only way to notice a
  second module on a shared pair answering with a plausible pressure from the
  wrong gauge. A reading of `9.99E+09` means the gauge has nothing to give and
  is recorded as a gap rather than trended as a pressure. 35 tests, none of
  which need hardware.

  No Granville-Phillips manual could be opened. Every site hosting one is
  refused by the network egress policy. The driver rests on one worked exchange
  relayed through a web search tool and on the EPICS `epics-modules/vac` device
  support read directly from GitHub, and the Granville-Phillips section of
  `REVIEW.md` lists item by item what is verified and what is assumed.
- `projects/fab_drivers/manuals/FETCH_PROMPT_GRANVILLE_PHILLIPS.md`, the request
  for the gauge manuals, with thirteen numbered questions the documents have to
  answer. Two of them decide whether the driver is correct: how a Series 375
  selects a gauge channel, and whether any of these instruments can be asked
  which pressure units it is configured for.
- `LICENSE`, BSD 3-Clause. The copyright holder line carries a placeholder until
  the exact name is supplied.
- `fab_drivers/core/trend_page.py`, the shared trend page generator. Each driver
  gets its own page, built from one design rather than ten. The page carries its
  own data and fetches nothing, because these machines have no internet and a
  page opened from disk cannot read a neighbouring file anyway. A gap in the
  readings is drawn as a break in the line, never joined across.
- `projects/fab_drivers/sessions/`, one starting prompt per driver session in
  build order. The ten drivers are built one per session and each session starts
  with no memory of the last, so writing the next prompt is the last step of
  every session rather than something reconstructed afterwards. Each file holds
  the prompt and nothing else, and is handed over as a file rather than pasted
  into a chat as text.
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
