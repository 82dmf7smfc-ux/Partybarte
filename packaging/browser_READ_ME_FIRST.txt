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

Note
----
Because it runs in the browser, it does not create native Excel chart files.
If you need clickable Excel charts or a PowerPoint deck, use the Python tool.
It reads CSV and delimited text, not binary .xls or .xlsx files. Export those
to CSV first.
