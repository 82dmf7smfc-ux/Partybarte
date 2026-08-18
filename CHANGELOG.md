# Changelog

All notable changes to this project are recorded here.

The format follows Keep a Changelog. Versions follow Semantic Versioning.

## [Unreleased]

### Fixed
- **The browser tool measured downtime differently depending on the timezone of
  the machine reading the log.** It built timestamps in local time, so an alarm
  spanning a daylight saving change came out an hour short next to the Python
  tool. Timestamps are now read as UTC, which is plain clock time and matches
  the Python tool everywhere. Only logs spanning a daylight saving change are
  affected, and those numbers were wrong before.
- **The browser tool turned impossible dates into real ones.** February 30th
  became March 2nd and month 13 became January of the next year, inventing
  alarms that never happened. Those rows are now rejected and reported as
  unreadable, which is what the Python tool already did.
- **The browser tool showed a wrong percent and a wrong cumulative line on the
  count Pareto chart.** The count ranking and the downtime ranking were built
  from the same objects, so whichever was built second overwrote the first one's
  rank, percent and cumulative percent. Any fault near the top of both rankings
  was affected, in the on-screen table and in the CSV export. The chart bars
  were right. The cumulative line was not.
- **Faults with equal counts could rank in a different order in each tool.**
  Python ordered them by however pandas grouped them, the browser tool by the
  order they appeared in the file. Both tools now break ties by name.
- The check that runs when a session ends went quiet as soon as anything was
  committed, because it only looked at the working tree. It now looks at
  everything the branch has touched, and checks anyway when it cannot tell.
- The parity check kept its own copy of the vendor column mapping, so it could
  have passed while `vendor_columns.json` said something different. It now reads
  that config, which makes the config the only copy.

### Added
- The project's hard rules now live in one place, `tools/project_rules.py`, and
  are applied from three directions: before an edit, before a commit through
  `.githooks/pre-commit`, and on every push in CI. Previously only edits made
  through the editor were checked, so anything written by a shell command went
  straight past. CI is the layer that actually holds, because a local hook can
  be skipped or never installed.
- `tests/test_project_setup.py`, which checks the hooks parse, the rules still
  block what they must, the rules flag nothing already in the project, and each
  skill is well formed with a description that says when to use it.
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
- The parity check now compares the ranking itself, not only the group totals.
  Order, percent, cumulative percent and the "Other" bucket past the top N are
  all checked, at a top N small enough to force that bucket. This is what caught
  the percent bug above. The check grew from 76 compared values to 512.
- `tests/data/sample_dst_log.csv` and `tests/data/expected_dst.json`, a log
  spanning both daylight saving changes and carrying one impossible date. It
  exists to keep the two tools reading timestamps the same way.
- CI now runs the parity check on every push and pull request, three times,
  under three timezones, and runs the Python suite under a timezone that
  observes daylight saving.
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
