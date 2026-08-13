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
4. Set the window length, the top-N cutoff, and the downtime method. Click
   "Analyze".
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
