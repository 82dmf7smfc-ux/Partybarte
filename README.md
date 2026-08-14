# Alarm Log Pareto Tool

This tool reads an alarm log from a semiconductor tool. It looks at the last 30
days of faults. It ranks the faults two ways. First by how often each one
happens. Second by how much downtime each one causes.

There are two versions in this project. Pick the one that fits you.

## Which version should I use?

**1. The browser tool: `alarm_pareto.html` (recommended, zero install).**
Double-click the file. It opens in Edge or Chrome. Click a button to pick one or
more elog files. It shows the most frequent faults and the biggest downtime,
with Pareto charts, right in the page. It needs no Python, no packages, and no
IT approval. It runs fully offline. Nothing you load ever leaves your computer.
Use this for day-to-day work on the bench. See "Browser tool" below.

**2. The Python tool: the `alarm_pareto` package.**
Run it from the command line. It writes an Excel workbook with real, clickable
Excel charts, plus a PowerPoint deck. Use this when you need those exact file
formats, or when you want to run the analysis in a script or on a schedule. It
needs Python and a few packages. See "Python tool" below.

Both versions use the same math, including the careful downtime handling.

Both run fully offline. Neither makes a network call.

---

## Browser tool

Open `alarm_pareto.html` in a browser. There is nothing to install.

1. Click "Choose Files" and pick one or more elog files. CSV and delimited text
   files work. So do P5000 Etch elogs, which have a text preamble and columns
   separated by spaces. The Format drop-down is set to "Auto detect", or you can
   force CSV or P5000.
   - For P5000 elogs the tool reads the tool name from the backup path in the
     preamble (for example `E:\Backups\etch4\Data\ELOG.DAT` reads as "etch4") and
     classifies a "dep..." or "etch..." name as a dep or etch tool. The import
     message names the tool. Every row is tagged with a "Tool" column, so you can
     load a dep log and an etch log together, rank by the "Tool" Pareto level, and
     tick which tools to include in the Tool filter to compare them.
2. Point the tool at your data. Set "First data row" to the line where the data
   begins, so any preamble lines above it are skipped. The tool reads from that
   row down until the first blank line. Older rows outside the window are dropped
   later. The same start row is used for every file you import.
3. Click "Auto-map columns". The tool shows one row per column with a few sample
   values and guesses what each column holds from those values. Fix any guess
   that is wrong using the drop-downs. The roles are: Date, Time, Timestamp
   (date and time in one column), Severity, Module / equipment, Tool, Message ID,
   Description, Duration, Alarm state, or Ignore. You need a Timestamp, or a Date
   (plus a Time), and a Message ID. Files with no header row work fine; columns
   show as "Column 1", "Column 2", and so on.
   - If a message with commas splits across two columns, tag both as Description
     and they are joined back together.
   - Pick "Other" to name a column you want to see but not analyze.
4. Tell it how downtime is stored. A duration column (tag it "Duration"), or
   separate set and clear rows (tag the marker column "Alarm state"), or "Derive
   from messages" (estimate downtime by pairing down and up messages per
   chamber), or none, in which case it ranks by count only. Many elogs have no
   downtime column, so "Derive from messages" and "none" are the common picks.
   - "Derive from messages" reads the chamber name from the message text, then
     pairs a "went offline" message with the next "back online" message for that
     chamber. The down and up phrase lists and the chamber-name list are shown
     right there and can be edited, because vendors word these differently.
     Downtime found this way is always labelled "estimated". A paired-interval
     table at the bottom shows each pair so you can check it by eye, with flags
     for pairs that never came back (unresolved) or ran past a sanity cap (long).
     It also reports tool-level numbers: "restricted" when any chamber is offline
     and "full tool down" when every chamber seen is offline at once.
5. If you mapped a Severity column, choose which severities to include. Use the
   preset buttons "Faults only", "Warnings only", or "Faults + warnings", or tick
   the levels by hand. The default is faults and warnings, so routine trace and
   prompt lines are left out. You can also narrow the events further: tick which
   chambers, categories, and tools to include, set a From/To date range, search
   the message text (plain, or a /regex/), and hide groups smaller than a size.
   Set the window length and the top-N cutoff. Click "Analyze".
6. Read the Insights card for the numbers behind the charts: events per day, the
   busiest day and hour, the mean gap between events, how concentrated the events
   are (how many groups make up 80 percent), and a per-chamber breakdown with each
   chamber's share and mean gap. A burst on any one day is flagged.
7. Read the summary and the Pareto charts. The fault chart labels each bar with
   the message ID and its most common text, for example
   "810 - Chamber 2 unable to start recipe". The Pareto opens on the Category
   level; switch grouping with the tabs (Fault, Category, Module, Tool, Message
   text). The "Tool" level ranks events per tool when a batch mixes tools.
   The Category table has a "Matched by" column that says how each category was
   decided (a built-in rule, your rule, or the auto label from the message shape).
   Use the "Chart" picker to switch between the Pareto, horizontal bars (better
   for long labels), and a heatmap of events by hour of day and weekday, with an
   optional log scale. Download a CSV summary, or use "Print / Save as PDF".
   - The "Category" level groups messages that differ only by a chamber tag or a
     number, so repeated template messages fall under one name. Built-in rules
     cover the common cases. Add your own under "Message categories" in step 2, one
     per line, in either form: `pattern => Label` (a case-insensitive regex on the
     message text) or `id:494,807 => Label` (an exact match on the Event Number).
     Because the Event Number is stable while the wording changes with the chamber
     and values, an ID rule is more reliable for events whose text varies. Your
     rules are saved in the browser and run first. Anything left uncategorized shows
     up in the debug log so you can see what rule to add.
   - When a row has no chamber tag, the tool reads a name from the message text
     using the editable "Subsystem / module names" list in step 2, so tool-level
     events land on a real module instead of "(unknown)".

If many messages fall outside your category rules, the "Unknown events" panel
after the analysis ranks the most common uncategorized message shapes and the
most common events with no chamber tag. Click "Add rule" on a shape to drop a
starter rule into the category box, then Analyze again. Tag-less tool or system
events can be grouped under one "System" name with the option in Settings.

If a file does not read the way you expect, press "Show debug log". It lists
short codes for how each file was parsed, such as the detected format, skipped
rows, rejoined lines, 2-digit years, and missing chamber tags. Turn on "Verbose"
for more example lines, the uncategorized event IDs (top 100 by count), and the
ranked unknown-event shapes. An ID with a single message shape is one line; an ID
that carries several distinct messages is split into one line per sub-message, so
each can get its own rule. Use "Copy debug report" to copy the codes, or "Copy
uncategorized IDs" to copy just the ID worklist so you can turn it into category
rules. Nothing there leaves your computer.

Because it runs in the browser, it does not write native Excel chart files. If
you need those, use the Python tool.

---

## Python tool

This version reads the same kind of log. It looks at the last 30 days of faults.
It writes the results to an Excel workbook and a PowerPoint deck.

The tool runs fully offline. It never makes a network call.

## What you get

Two files land in the `output` folder.

1. `alarm_pareto.xlsx`. An Excel workbook with real charts you can click into.
   It has one sheet with the filtered data. It has three summary sheets, one per
   grouping level. Each summary sheet shows a Pareto by count and a Pareto by
   downtime, side by side.
2. `alarm_pareto.pptx`. A slide deck. One Pareto slide per grouping level. Plus
   a summary slide with the headline numbers.

## The two downtime numbers

This is the most important idea in the tool. There are two different ways to
add up downtime. They answer different questions. The tool reports both and
never mixes them.

1. **Attributed downtime.** Each fault is credited its own full duration. If ten
   alarms each lasted four hours, the attributed total is forty hours. Use this
   to rank which fault costs the most. This is the default.
2. **True wall-clock downtime.** Overlapping alarms are merged first, then
   summed. If two alarms are active at the same time, the shared time is counted
   once. Use this to answer how long the tool was actually down.

Every sheet and slide says which method produced the number.

## First time setup

You need Python and the packages listed in `requirements.txt`. On an offline
machine, get the wheel files from IT and put them all in one folder. A wheel is
a pre-built package file. Then run this from the project folder:

```
setup_venv.bat C:\path\to\wheel_folder
```

This builds a private environment in the `.venv` folder. It keeps these packages
away from anything you install later.

## Running the tool

```
.venv\Scripts\python.exe -m alarm_pareto.main --input path\to\your_log.csv --vendor amat
```

### Options

| Option | What it does | Default |
|---|---|---|
| `--input` | Path to the alarm log file. | required |
| `--vendor` | Which config block to use. | `amat` |
| `--config` | Path to the vendor config JSON. | the one that ships with the tool |
| `--window-days` | How many days back to include. | `30` |
| `--top-n` | How many rows before the rest become "Other". | `15` |
| `--downtime-method` | `attributed` or `wallclock`. Drives the downtime ranking. | `attributed` |
| `--output-dir` | Folder for the output files. | `output` |

## Adding a new tool vendor

You do not need to touch any Python file. Open
`alarm_pareto/config/vendor_columns.json`. Copy an existing block. Give it a new
name. Change the column names on the right to match your file headers. Save.
Then run the tool with `--vendor your_new_name`.

The names on the left are fixed internal names. Here is what each one means.

| Internal name | Meaning | When to include it |
|---|---|---|
| `ts_set` | Alarm onset time. | Always. |
| `ts_clear` | Alarm clear time. | Only if each row has both a set and a clear time. |
| `event_type` | A "set" or "clear" marker. | Only if set and clear are separate rows. |
| `fault_code` | The fault or alarm code. | Always. |
| `description` | The fault text. | Always. |
| `equipment` | The equipment or module id. | Always. |
| `duration_s` | The downtime for the row. | Only if the log already has a duration column. |

The tool works out how your log stores downtime from the columns you map.

1. If you map `duration_s`, it uses that duration.
2. If you map both `ts_set` and `ts_clear`, it uses each row as one interval.
3. If you map `event_type`, it pairs set and clear rows. It matches a clear to
   the most recent open set with the same equipment and fault code. You can
   change that pairing key in the config.

## How the code is laid out

The pipeline is split into small modules. Each does one job.

| File | Job |
|---|---|
| `alarm_pareto/parse.py` | Read the file into a raw table. |
| `alarm_pareto/normalize.py` | Rename vendor columns to internal names. |
| `alarm_pareto/window.py` | Keep only the trailing window. |
| `alarm_pareto/aggregate.py` | Build the count and downtime rankings. |
| `alarm_pareto/render_xlsx.py` | Write the Excel workbook. |
| `alarm_pareto/render_pptx.py` | Write the PowerPoint deck. |
| `alarm_pareto/main.py` | Wire it together and read the command line. |

## Running the tests

The tests use a small hand-built sample log. The correct answers were worked out
by hand and stored in `tests/data/expected_summary.json`. If a code change makes
a test fail, the change altered the analysis. That is the safety net.

```
.venv\Scripts\python.exe -m pytest -q
```

The same tests run automatically on GitHub for every push and pull request. See
`.github/workflows/ci.yml`.

## Project documents

| File | What it is for |
|---|---|
| `CONTRIBUTING.md` | How to set up, test, branch, and cut a release. |
| `ROADMAP.md` | Ideas and future improvements, so they are not lost. |
| `CHANGELOG.md` | A dated record of what changed in each version. |
| `tools/build_zips.py` | Rebuilds the two download packages the same way every time. |

## Downloads

Packaged versions of both tools are published on the GitHub Releases page. Each
release has two zip files. One holds the browser tool. One holds the Python
tool. To build them yourself, run `python tools/build_zips.py`.

## License

This project is proprietary. All rights are reserved. No use, copying,
modification, distribution, or commercial use is permitted without the prior
written permission of the copyright holder. See the `LICENSE` file for the full
terms.
