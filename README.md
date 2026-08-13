# Alarm Log Pareto Tool

This tool reads an alarm log from a semiconductor tool. It looks at the last 30
days of faults. It ranks the faults two ways. First by how often each one
happens. Second by how much downtime each one causes. It writes the results to
an Excel workbook and a PowerPoint deck.

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
