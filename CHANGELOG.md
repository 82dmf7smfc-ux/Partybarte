# Changelog

All notable changes to this project are recorded here.

The format follows Keep a Changelog. Versions follow Semantic Versioning.

## [Unreleased]

### Added
- Browser tool: the Pareto now opens on the Category level, and the Category
  table shows a "Matched by" column, so you can see how each category was decided
  (a built-in rule, your rule, or the auto label from the message shape). The
  same detail is in the bar hover tooltip.
- Browser tool: the debug log now includes category metrics: how many messages
  were categorized (count and percent), the number of distinct categories,
  per-rule hit counts, and which rules never matched.
- Browser tool: cleaner categories. Uncategorized messages get a readable label
  from their leading words instead of a raw shape, the normalization strips the
  chamber tag and boilerplate so near-identical messages collapse, and more
  built-in rules cover common P5000 messages.
- Browser tool: an editable "Subsystem / module names" list. When a row has no
  chamber tag, the tool reads one of these names from the message text and uses
  it as the Module, so tool-level events land on a module instead of "(unknown)".

### Changed
- Browser tool: removed the two demo buttons ("Load built-in sample" and "Load
  message-log sample").

### Added (earlier in this cycle)
- Browser tool: an "Unknown events" panel. It ranks the messages that matched no
  category rule, and the events with no chamber tag, by how common each shape is,
  so the biggest unknown groups are obvious. Each uncategorized shape has an "Add
  rule" button that appends a starter rule to the category box, so cleaning up the
  Category Pareto is a few clicks.
- Browser tool: a "Verbose" toggle on the debug log that shows more example lines
  per code and appends the ranked unknown-event shapes to the copyable report.
- Browser tool: an option to label tag-less tool/system events as "System"
  instead of "(unknown)", so they group in one place in the Module Pareto.
- Browser tool: more chart types. A "Chart" picker on the Pareto card switches
  between the Pareto (bars plus the cumulative line), horizontal bars that read
  well when the labels are long, and a heatmap of events by hour of day and
  weekday. A "Log scale" toggle helps when a few groups dwarf the rest. All are
  plain SVG, so the tool stays a single offline file.
- Browser tool: more filters in Settings, on top of the severity filter. Narrow
  the events by chamber/module and by category (checkboxes built from the data),
  by an explicit date range, and by a message search (plain text, or a /regex/).
  A "Hide groups smaller than" floor folds rare groups into "Other" in the
  Paretos. The summary reports how many rows were kept after the filters.
- Browser tool: an Insights card with analytics beyond the Paretos. Headline
  tiles show events per day, the busiest day, the mean gap between events, the
  top group's share, and how many groups make up 80 percent of the events. An
  events-per-day bar chart shows the trend, and a per-chamber table shows each
  chamber's event count, share, mean gap between events, and downtime. A footer
  notes the busiest hour of day and flags a burst when one day runs well above
  the daily average.
- Browser tool: message categories. Templated messages that differ only by a
  chamber tag or a number are grouped under one category, so a new "Category"
  Pareto reads cleanly. Built-in rules cover the common P5000 messages, and you
  can add your own rules ("pattern => Label", one per line) which are saved in
  the browser and run first. A message that matches no rule is grouped by its
  normalized shape and listed under the CAT-UNMATCHED debug code, so it is easy
  to see what rule to add next.
- Browser tool: reads P5000 Etch elogs. A new format layer detects the file, skips
  the text preamble, finds the "Date Time Event Number Event Type Description"
  header, and reads records whose columns are separated by runs of spaces. The
  Description keeps its own spacing. The chamber is read from the `<S4EXT>` style
  tag in the message. The parsed columns feed the existing auto-map, severity
  filter, and Pareto pipeline unchanged.
- Browser tool: a Format drop-down (Auto detect, CSV or delimited, P5000 Etch) so
  the format can be forced when auto-detect is wrong. Auto is the default.
- Browser tool: 2-digit years (MM/DD/YY) are read with a 1969 pivot, so 00 to 68
  is the 2000s and 69 to 99 is the 1900s.
- Browser tool: a hidden debug log with short codes for how each file was read
  (format, preamble, skipped rows, rejoined lines, 2-digit years, missing chamber
  tags, unreadable timestamps). A button copies the report for troubleshooting.
  Nothing there leaves the browser.
- Browser tool: an automated test harness. `tests/browser/run.mjs` drives a real
  headless Chromium against `alarm_pareto.html` and checks the pure data layer
  (now grouped under a `window.AP` name) and a couple of full-page flows. It uses
  only Node built-ins, so there is nothing to install.
- CI: a `browser-tests` job runs the harness on every push and pull request,
  alongside the Python suite.
- `docs/DEBUG_CODES.md`, a reference for the browser tool's debug codes. The
  harness checks that every code the tool emits is listed in the registry.

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
