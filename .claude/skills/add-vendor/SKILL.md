---
name: add-vendor
description: Add support for a new tool vendor's alarm log format, or fix a column mapping that reads the wrong field. Use when a new elog file will not import, when column headers differ from an existing vendor block, when set and clear arrive as separate rows, or when someone asks to support a new tool, chamber, or fab.
---

# Adding a vendor log format

Adding a vendor is a JSON edit. It is not a code change. If you find yourself
editing a Python file to support a new log format, stop and reconsider.

## Where it goes

`alarm_pareto/config/vendor_columns.json`. Copy an existing block, rename it,
and change the values on the right to match the real column headers.

The keys on the left are internal names and never change. The values on the
right are the exact headers in that vendor's file, including spaces and case.

## The internal names

| Name | Meaning | Required |
|---|---|---|
| `ts_set` | Alarm onset timestamp | Yes |
| `fault_code` | Vendor fault or alarm code | Yes |
| `description` | Human readable fault text | Yes |
| `equipment` | Equipment or module identifier | Yes |
| `ts_clear` | Alarm clear timestamp | Only if a row holds a whole interval |
| `event_type` | Marker saying set or clear | Only if set and clear are separate rows |
| `duration_s` | Downtime already in the log | Only if the log has a duration column |

## The three downtime shapes

Pick the one the log actually uses. Getting this wrong gives numbers that look
plausible and are wrong.

1. **A duration column.** The log already says how long each alarm lasted. Set
   `duration_s` and set `duration_unit` to `seconds`, `minutes`, or `hours`.
2. **Set and clear rows.** Each alarm appears twice. Set `event_type` and
   `event_values`, and set `pairing_keys` to the columns that identify one
   alarm, usually equipment and fault code.
3. **Neither.** Ranking is by count only. Leave the downtime fields out.

## Steps

1. Get a real sample of the log. Do not guess at headers. If you do not have
   one, ask for it rather than inventing a mapping.
2. Copy a block in `vendor_columns.json` and edit it. Keep the `description`
   field honest about whether the headers are real or placeholders.
3. Run the Python tool against the real file with `--vendor <yourname>` and
   check the row count and the date range against what the file shows.
4. Sanity check the numbers. Attributed downtime is always greater than or equal
   to wall-clock downtime. If it is not, the mapping is wrong.
5. Add a line to `CHANGELOG.md` under "Unreleased".

## The browser tool

The browser tool does not read this file. It guesses columns and lets the user
correct them in the page. If a vendor's headers are unusual enough that the
guess fails, the fix is to add a keyword to `guessColumn` in
`alarm_pareto.html`. That is a code change, so the parity rules apply. See the
`change-the-analysis` skill.
