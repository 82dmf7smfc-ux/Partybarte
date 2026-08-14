Alarm Log Pareto - Browser tool
===============================

What this is
------------
A single web page that ranks alarm faults from a semiconductor tool. It runs
fully offline in your web browser. There is nothing to install. No Python. No
package approval. Nothing you load ever leaves your computer.

How to use it
-------------
1. Double-click alarm_pareto.html. It opens in Edge or Chrome.
2. Click "Choose Files" and pick one or more elog files from the same tool.
   CSV and delimited text files work. Or click "Load built-in sample" to try it.
3. Set "First data row" to the line where the data starts. Preamble lines above
   it are skipped. The page reads down until the first blank line. The same start
   row is used for every file you import.
4. Click "Auto-map columns". The page lists one row per column with sample
   values and guesses each role. Fix any that are wrong. Roles include Date,
   Time, Timestamp, Severity, Module, Message ID, and Description. You need a
   Timestamp (or a Date plus a Time) and a Message ID. If a message with commas
   splits across two columns, tag both as Description to join them.
5. Choose how downtime is stored: a duration column (tag it "Duration"), or
   separate set and clear rows to pair (tag the marker column "Alarm state"), or
   none (rank by count only).
6. If you mapped a Severity column, pick which severities to include. Presets:
   "Faults only", "Warnings only", "Faults + warnings" (the default). Set the
   window length and the top-N cutoff. Click "Analyze".
7. Read the summary and the Pareto charts. The fault chart pairs each message ID
   with its most common text. Use the tabs to switch grouping level. Download a
   CSV summary, or use "Print / Save as PDF" for a report.

Files in this folder
--------------------
alarm_pareto.html      The tool. This is the only file you need.
sample_alarm_log.csv   A small example elog you can import to test it.
screenshot.png         What the tool looks like when it has run.

Note
----
Because it runs in the browser, it does not create native Excel chart files.
If you need clickable Excel charts or a PowerPoint deck, use the Python tool.
It reads CSV and delimited text, not binary .xls or .xlsx files. Export those
to CSV first.
