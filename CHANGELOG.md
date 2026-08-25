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
### Fixed
- PM Round Logger: "Copy its tool readings here" did nothing. Two functions
  were both named `copyPoints`, so the later one silently replaced the button's
  handler from 1.4.0 onward, with no error anywhere. The file-format helper is
  now `copyPointList`, and a test covers the button.

### Added
- PM Round Logger 1.6.0: reading suggestions. Every reading defined on any
  chamber type or tool is offered as type-ahead in each "add a reading" box,
  showing its unit, limits and where it came from, and filling those in when
  picked. Suggestions copy rather than link, so a limit changed on one type
  never moves another. The spelling already in use wins, so one reading cannot
  quietly become two columns in a PivotTable. The list is derived from what
  already exists rather than stored, so it needs no migration, cannot fall out
  of step, and updates the moment a reading is added or removed.
- PM Round Logger 1.6.0: "Copy its readings here" on a chamber type, mirroring
  the tools' button, for setting up a type much like one that already exists.
- PM Round Logger 1.6.0: the setup screen warns when one reading name is
  logged in two different units across types, which Excel would silently
  combine into a single column.
- PM Round Logger 1.5.0: per-chamber limit overrides. A chamber can set its
  own min and max for any reading while still taking the reading list, name and
  unit from its type, so two chambers running the same process to different
  specs stay comparable in Excel. A reading left on the type default still
  follows the type when the type changes; only the overridden reading stops.
  Entry hints say when a limit belongs to that chamber alone, and typing the
  type's own numbers back in clears the override rather than storing a copy.
- PM Round Logger 1.5.0: exports record the limit each chamber was actually
  checked against, so the Min and Max columns always agree with the Status
  beside them. A JSON backup restores the type-and-override split exactly; a
  CSV restores the effective limits, rebuilding the split from whichever
  chamber it meets first, which preserves what every chamber is checked
  against even where the bookkeeping differs.
- PM Round Logger 1.5.0: stored data layout moves to version 3. Nothing needs
  converting, but the number still moves so that an older build refuses the
  data rather than applying a type's limits to a chamber that has its own and
  reporting an out-of-spec reading as good.
- PM Round Logger 1.4.0: chambers. A tool may have chambers, and each chamber
  has a TYPE that carries its reading list, so chambers of the same kind log
  the same things and a type written once is shared by every chamber using it,
  across tools. Tools keep readings of their own for whatever belongs to the
  whole machine. Tapping a chambered tool lists its units, each with its own
  done mark and its own limit checking, so one chamber can flag while its twin
  passes; a tool with no chambers is unchanged and still opens straight into
  its readings. A tool counts as logged only once every chamber is in.
- PM Round Logger 1.4.0: the export gains `Chamber` and `Chamber type`
  columns, left empty on tool-level rows so an Excel filter separates the two.
  Import reads files with or without those columns, so exports taken before
  chambers existed still restore correctly.
- PM Round Logger 1.4.0: stored data layout moves to version 2. The migration
  hook added in 1.2.0 does the work: existing tools gain an empty chamber list
  and existing entries an empty chamber record, with every logged reading left
  exactly where it was. This is the first real use of that hook.
- PM Round Logger 1.3.0: an "Export this round to a folder you pick" button,
  opening a real Save As dialog, shown only where the browser supports it. A
  failure falls back to an ordinary download rather than losing the export, and
  says so. Added after testing on the tablet showed the Save As API works while
  a remembered backup folder re-prompts for permission every session, which
  would have cost a tap every morning and was therefore not built.
- PM Round Logger 1.3.0: warns when the page is running from a Windows
  temporary folder, which is what happens when the HTML is opened from inside
  the zip rather than extracted. Windows deletes that folder eventually.
- `pm_logger_capability_test.html`: step 3 now says to close every browser
  window rather than "this page", since closing only the tab can leave the
  permission alive and produce a false pass. The measured result is recorded in
  the file so it need not be repeated except on a new tablet.
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
