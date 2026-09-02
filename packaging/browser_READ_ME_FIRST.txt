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
3. The page guesses which column is the timestamp, the fault code, and so on.
   Fix any wrong guess with the drop-downs. Only Timestamp and Fault code are
   required.
4. Choose how downtime is stored: a duration column, or separate set and clear
   rows to pair, or none (rank by count only).
5. Set the window length and the top-N cutoff. To cover one shift, pick a
   shift preset or fill in the two time-of-day boxes yourself. Leave them empty
   for all hours. A "from" later than a "to" wraps past midnight, so 22:00 to
   06:00 is the night shift. Alarms are picked by the time they started, so an
   alarm that runs past the end of the range still counts its whole duration.
   Click "Analyze".
6. Read the summary and the Pareto charts. Use the tabs to switch grouping
   level. Download a CSV summary, or use "Print / Save as PDF" for a report.

Files in this folder
--------------------
alarm_pareto.html      The tool. This is the only file you need.
sample_alarm_log.csv   A small example elog you can import to test it.
screenshot.png         What the tool looks like when it has run.

The three downtime numbers
--------------------------
The page shows three downtime totals. They answer different questions and must
never be mixed.

  Attributed     Each fault credited its whole duration. Best for ranking
                 which fault costs the most.
  True wall clock  Overlapping faults merged so shared time counts once. Best
                 for "how long was the tool down" over a plain window.
  In range       Overlaps merged, and each fault also cut down to the hours
                 the report covers. Best for anything to do with a shift.

The third one matters as soon as you pick a shift. A fault that starts at 17:50
and runs four hours is credited entirely to the day shift by the first two,
because that is when it started. In range splits it the way the clock does: ten
minutes of day shift, three hours fifty of night shift. It is also the only one
that cannot exceed the length of the report, so it is the one to use when you
want to say "the tool was down for X percent of night shift".

Pick it in the "Downtime ranking method" box. All three totals are shown
whichever one you rank by.

How much data it can handle
---------------------------
There is no row limit. What limits you is the memory in your browser tab.
Measured on generated logs:

  100,000 rows   (8 MB)     about 1 second
  500,000 rows   (40 MB)    about 3 seconds
  1,000,000 rows (81 MB)    about 10 seconds
  2,000,000 rows (162 MB)   about 21 seconds
  4,000,000 rows (324 MB)   runs out of memory, the tab crashes

Two to three million rows is the practical ceiling. One single file also
cannot be larger than 512 MB, though splitting the same data into several
files gets around that.

While the page is reading or analyzing it will not respond. That is normal,
not a crash. It tells you before it starts and warns you when an import is
large enough to be slow.

If you regularly have more than about two million rows, split the import by
date range, or use the Python tool.

Note
----
Because it runs in the browser, it does not create native Excel chart files.
If you need clickable Excel charts or a PowerPoint deck, use the Python tool.
It reads CSV and delimited text, not binary .xls or .xlsx files. Export those
to CSV first.
