PM Round Logger - browser tool
==============================

What this is
------------
A single web page for logging preventative maintenance readings on your daily
round. You pick a tool, type what its screen says, save, and move to the next
one. It shows you which tools you have not done yet today.

It runs fully offline in your web browser. There is nothing to install. No
Python. No package approval. Nothing you type ever leaves the tablet.


READ THIS PART FIRST
--------------------
Your readings are kept in the browser's own storage on this one tablet.

That storage is NOT a database. It is wiped, with no warning and no undo, if:

  - anyone clicks "Clear browsing data" in Edge,
  - IT re-images or resets the tablet,
  - the tablet is replaced.

So export regularly. The exported file is the real record. The tablet is a
clipboard. The page will nag you about this, gently after one day and loudly
after three. Do not ignore it.


How to use it
-------------
1. Double-click pm_logger.html. It opens in Edge.

2. First time only: go to the Tools tab and add the machines you walk. For
   each one, add the readings you take at it. Give each reading a unit, and a
   min and max if you want it checked.

   In a hurry? Tap "Load an example setup to try it" to see how it works with
   two made-up tools, then delete them.

   Setting up a second machine of the same type? Add it, then use "Copy its
   readings here" instead of retyping the list.

3. Every day: open the Today tab. Tap a tool, type its readings, and tap
   "Save and next tool". It takes you straight to the next tool you have not
   done. When the last one is saved you get a "Round complete" card with an
   export button on it.

4. Tap a tool you have already logged to fix a typo. Saving again replaces
   what was there.

5. Missed a day? Use the arrows either side of the date to go back and fill
   it in.


About the limits
----------------
A reading outside its min or max turns red and says why. The value still
saves, every time. Nothing is ever refused or blocked.

That is deliberate. On a round you record what the tool screen actually says,
good or bad. A tool that argues with you about a bad number is a tool that
gets fed made-up numbers.

Leave min and max blank for a reading you just want logged, not checked.


Getting the data onto your PC
-----------------------------
On the Data tab there are two export buttons.

  Export for Excel (CSV)      pm_readings_2026-08-24.csv
  Export full backup (JSON)   pm_backup_2026-08-24.json

Both save to the tablet's Downloads folder. The page tells you the filename.
From there, move the file however you normally do - OneDrive, Teams, email, or
a USB stick.

One thing worth knowing: the tool itself never touches the network, but
OneDrive, Teams and email do. If this data is sensitive, check that sending it
that way is allowed, or use a USB stick or a mapped drive instead.


Which export do I use?
----------------------
Use the CSV for Excel. Use it weekly.

Use the JSON before anything risky - swapping tablets, or letting IT touch the
machine. It is an exact copy, including tools you have set up but never
logged yet. The CSV cannot carry those, because a tool with no readings has
no rows in it.

Both can be imported back.


Trending it in Excel
--------------------
Double-click the CSV. It opens straight into Excel.

The file has one row per reading, like this:

  Date        Tool       Data point         Unit    Value   Min  Max  Status
  2026-08-24  Etcher 3   Chamber pressure   mTorr   9.4     8    12   OK
  2026-08-24  Etcher 3   He leak rate       sccm    2.9          2.5  HIGH

That is one row per reading rather than a wide grid, on purpose: your tools
each log different things, so a grid would be mostly empty boxes.

To chart it:

  1. Click any cell in the data.
  2. Insert > PivotTable > OK.
  3. Drag Date into Rows.
  4. Drag Data point into Columns.
  5. Drag Value into Values, then set it to Average or Max rather than Count.
  6. With the pivot selected: Insert > Line Chart.

To look at one tool only, drag Tool into Filters as well.

To find every bad reading fast: select the header row, Data > Filter, then
filter the Status column to LOW and HIGH.


Restoring after a wipe
----------------------
1. Open pm_logger.html.
2. Data tab > Import > pick your most recent export.
3. Choose "Replace" if the tablet is empty, which it will be after a wipe.

"Merge" is for when the tablet already has readings you want to keep. It adds
days that are missing and leaves everything already on the tablet alone. It
tells you how many it skipped.


Moving to a different tablet
----------------------------
1. On the old tablet: export the JSON backup.
2. Copy pm_logger.html and the backup file to the new tablet.
3. Open the page there, then Data tab > Import > Replace.


A note on renaming
------------------
Renaming a tool or a reading is safe. Its history stays attached, because the
page tracks them by a hidden id rather than by name.

The one place names do matter is importing, since a file has names in it, not
ids. So do not give two tools the same name. The Tools tab warns you if you
do.


Files in this folder
--------------------
pm_logger.html    The tool. This is the only file you need.
READ_ME_FIRST.txt This file.


Changing it yourself
--------------------
Open pm_logger.html in Notepad. The colours are at the top, in one block. The
code is at the bottom, split into labelled sections that say what each one
does. The spots you are most likely to want to change - the export columns,
how impatient the export reminder is, the limit colours - each have a comment
marking them.
