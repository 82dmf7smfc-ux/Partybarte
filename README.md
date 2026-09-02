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

1. Click "Choose Files" and pick one or more elog files from the same tool.
   CSV and delimited text files work. Or click "Load built-in sample" to try it.
2. The tool guesses which column is the timestamp, the fault code, and so on.
   Fix any guess that is wrong using the drop-downs. Only the timestamp and the
   fault code are required.
3. Tell it how downtime is stored. Three choices. A duration column. Or separate
   set and clear rows that it should pair. Or none, in which case it ranks by
   count only.
4. Set the window length, the top-N cutoff, and the downtime method. To report
   on one shift, pick a shift preset or type the two time-of-day boxes yourself.
   Leave them empty for all hours. A "from" later than a "to" wraps past
   midnight, so 22:00 to 06:00 is the night shift. Click "Analyze".
5. Read the summary and the Pareto charts. Switch grouping level with the tabs.
   Download a CSV summary, or use "Print / Save as PDF" to make a report.

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

## The three downtime numbers

This is the most important idea in the tool. There are three different ways to
add up downtime. They answer three different questions. The tool reports all
three and never mixes them.

1. **Attributed downtime.** Each fault is credited its own full duration. If ten
   alarms each lasted four hours, the attributed total is forty hours. Use this
   to rank which fault costs the most. This is the default.
2. **True wall-clock downtime.** Overlapping alarms are merged first, then
   summed. If two alarms are active at the same time, the shared time is counted
   once. Use this to answer how long the tool was actually down.
3. **In-range downtime.** Overlaps are merged as above, and every fault is also
   cut down to the parts that fall inside the hours the report covers. Use this
   to answer how much of a shift the tool spent down.

### Why the third one exists

Numbers 2 and 3 are the same thing until you narrow the report to a shift. Then
they come apart, because they count by different rules:

| | Counts a fault by | Bounded by the clock |
|---|---|---|
| Attributed | when it started, whole duration | no |
| True wall clock | when it started, overlaps merged | no |
| In range | where its downtime actually landed | yes |

Take an alarm that starts at 17:50 and runs four hours, with a 06:00 to 18:00
day shift and an 18:00 to 06:00 night shift.

- Wall clock puts all four hours on the **day shift**, because that is when the
  fault started, and gives the night shift nothing.
- In range splits it the way the clock does: **ten minutes** of day shift and
  **three hours fifty** of night shift.

This gives the third number a property the other two do not have. Run the same
log for the day shift and for the night shift, and the two in-range figures add
back up to the figure for the whole window. Neither of the other two does that.
It also cannot exceed the length of the report, so "the tool was down for 62% of
night shift" is a sentence you can only write with this number.

Because it follows the clock rather than the fault onset, the in-range number is
built from every alarm in the file, not just the rows that passed the window and
shift filters. An alarm that began before the window opened, or before the shift
started, still had the tool on the floor during the reported hours, and this
number counts that part of it.

### Which to use

- Ranking which fault to go fix: **attributed**. It is the default for a reason.
- Reporting how long the tool was down over a plain window: **wall clock**.
- Anything to do with a shift, or any sentence with a percentage in it:
  **in range**.

Pass `--downtime-method in_range` to rank by it. Every sheet and slide says
which method produced the number, and all three totals appear on the summary
slide and the data sheet whichever one you rank by.

### What the report covers

Once a report is narrowed to a shift, the time it covers is no longer one
unbroken block. Thirty days of night shift is thirty separate blocks, one per
night, each running 18:00 on one day to 06:00 on the next. The tool builds that
list, tells you how many blocks and how many hours it came to, and clips against
it. That list is also what the percentage is measured against.

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
| `--start-time` | Keep only alarms that start at or after this clock time, as `HH:MM`. | no time filter |
| `--end-time` | Keep only alarms that start before this clock time, as `HH:MM`. | no time filter |
| `--top-n` | How many rows before the rest become "Other". | `15` |
| `--downtime-method` | `attributed`, `wallclock`, or `in_range`. Drives the downtime ranking. | `attributed` |
| `--output-dir` | Folder for the output files. | `output` |

### Filtering by time of day

`--start-time` and `--end-time` narrow the report to a range of clock hours, so
it can cover one shift. Give both or neither.

```
.venv\Scripts\python.exe -m alarm_pareto.main --input log.csv --start-time 06:00 --end-time 18:00
.venv\Scripts\python.exe -m alarm_pareto.main --input log.csv --start-time 18:00 --end-time 06:00
```

Three things to know.

1. The range keeps the start minute and stops just before the end minute. That
   is what makes `06:00` to `18:00` and `18:00` to `06:00` add up to a whole day
   with nothing counted twice.
2. A start later than the end wraps past midnight, so `22:00` to `06:00` is the
   night shift.
3. Alarms are picked by the time they started, the same rule the trailing window
   uses. An alarm that starts at 17:50 and runs four hours counts its whole four
   hours against the day shift. The downtime number therefore answers "downtime
   from faults that began in these hours", not "clock time the tool spent down
   during these hours".

The time-of-day filter runs after the trailing window, so the window start and
end printed on the report still describe the file, not the shift.

When you filter to a shift, use `--downtime-method in_range` as well. The other
two numbers credit a fault to the shift it started in, whole, which is not what
you want once you are comparing shifts. See **The three downtime numbers** above.

## How much data can it handle

Neither tool caps the number of rows. There is no row limit, no file count
limit, and no truncation anywhere in the code. What limits you is memory and
patience, and the two tools have very different ceilings.

### Browser tool

Everything happens inside the browser tab, in memory, on one thread. Measured
on generated logs with five columns, running the tool's own parsing and
aggregation code:

| Rows | File size | Time to analyze | Memory used |
|---|---|---|---|
| 100,000 | 8 MB | about 1 second | about 140 MB |
| 500,000 | 40 MB | about 3 seconds | about 400 MB |
| 1,000,000 | 81 MB | about 10 seconds | about 800 MB |
| 2,000,000 | 162 MB | about 21 seconds | about 1.5 GB |
| 4,000,000 | 324 MB | out of memory | tab crashes |

Roughly 800 MB of memory and ten seconds of work per million rows, scaling
linearly. A browser tab has somewhere between two and four gigabytes to work
with, so the practical ceiling is **two to three million rows**. Past that the
tab crashes with no useful message.

Two other hard limits worth knowing:

- A single file cannot exceed **512 MB**, because the page reads it into one
  JavaScript string and that is the largest string the browser engine allows.
  Splitting the same data across several files gets around this, since each
  file is read into its own string.
- Every file is held in memory at once before parsing starts, so total size
  across all files still counts against the memory ceiling above.

The page now tells you what it is doing. It shows how much it is reading before
it starts, warns above 750,000 rows that analysis will take a few seconds, and
warns above 2,000,000 rows that the tab may run out of memory. While it works
the page does not respond. That is normal and not a crash.

If you routinely have more than about two million rows, split the import by
date range, or use the Python tool.

### Python tool

No cap either, and a much higher ceiling, because it is limited by the memory
of the machine rather than a browser tab. It reads the whole file into a pandas
table with every column as text, which costs roughly one to two gigabytes per
million rows of a typical five column log. On an ordinary workstation with
16 GB that is comfortably several million rows.

Note that this is an estimate from the shape of the code, not a measurement.
The measured numbers in the table above are for the browser tool only.

If you ever do exceed what the machine can hold, the fix is to narrow the input
before the tool sees it, not to change the tool: split the log by date range and
run once per range.

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
| `alarm_pareto/window.py` | Keep only the trailing window, then the chosen hours of the day. |
| `alarm_pareto/reporting_range.py` | Work out which blocks of clock time the report covers, and clip alarms to them. |
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
