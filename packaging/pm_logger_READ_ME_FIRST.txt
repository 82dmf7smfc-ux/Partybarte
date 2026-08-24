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


SET THIS UP ONCE: where the files land
--------------------------------------
Do this before anything else. It takes a minute and saves you a step every
single day.

  1. Make a folder for this on the PC side. A OneDrive folder is ideal,
     something like:  Documents\OneDrive\PM Rounds
  2. On the tablet, open Edge and go to:
       Settings > Downloads > Location > Change
     Point it at that folder.
  3. While you are there, make sure "Ask me what to do with each download"
     is turned OFF.

Now every export lands straight in OneDrive and syncs to your PC on its own.
No copying, no USB stick, no emailing it to yourself.

Worth doing too: keep pm_logger.html itself in that same folder. Then the tool
and its data travel together, and there is only one place to look.

A page opened from a file cannot choose where a download goes. That is a
browser security rule, not something the tool can work around. The Edge
setting above is the way to control it.

One more thing: the tool itself never touches the network, but OneDrive, Teams
and email do. If this data is sensitive, check that sending it that way is
allowed, or point the download folder at a USB stick or a mapped drive
instead.


The three export buttons
------------------------
On the Data tab:

  Export this round (CSV)          pm_round_2026-08-24.csv
  Export everything for Excel      pm_readings_through_2026-08-24.csv
  Export full backup (JSON)        pm_backup_through_2026-08-24.json

USE THE FIRST ONE EVERY DAY. It holds that one day's round, and it is named
for the day the readings were TAKEN, not the day you pressed the button. So
if you back-fill a missed Tuesday on Thursday, the file is still named for the
Tuesday. It also appears as a button on the "Round complete" card, so
finishing the round and filing it is one tap.

Use the second one when you want to chart a trend. It holds everything, in one
file, ready to pivot.

Use the third before anything risky - swapping tablets, or letting IT touch
the machine. It is an exact copy, including tools you have set up but never
logged yet. A CSV cannot carry those, because a tool with no readings has no
rows in it.

All three import back.


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


The better way, once you have a few weeks of daily files
--------------------------------------------------------
If your daily round files are all piling up in one OneDrive folder, Excel can
read the whole folder as a single table and keep itself up to date. Set this
up once and you never export the "everything" file again.

  1. In a new workbook: Data > Get Data > From File > From Folder.
  2. Pick your PM Rounds folder. Click Combine > Combine & Load.

Excel stacks every daily file into one table. Build your PivotTable on that.
From then on, when new daily files appear in the folder, just open the
workbook and click Data > Refresh All. The chart updates itself.

This is built into Excel. There is nothing to install.

To find every bad reading fast: select the header row, Data > Filter, then
filter the Status column to LOW and HIGH.


Restoring after a wipe
----------------------
1. Open pm_logger.html.
2. Data tab > Import.
3. Pick your files. You can select MANY AT ONCE - press Ctrl+A in the folder
   picker to take every daily round file you have. CSV and JSON can be mixed
   in the same go.
4. Choose "Replace" if the tablet is empty, which it will be after a wipe.

It tells you how many tools, readings and days it found before changing
anything, so you can back out if the number looks wrong.

If one file in the batch is damaged or is not a PM export, it is skipped by
name and the rest still go in.

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


Running out of room
-------------------
The Data tab shows how full the browser's storage is. For scale: eight tools
with ten readings each, logged every working day, is about 0.36 MB a year, and
the allowance is about 5 MB. So you have years.

Two things worth knowing anyway. That allowance is SHARED with any other tool
you open from a file on the same tablet. And if it ever does fill up, the page
says so in red at the top rather than letting a save fail quietly. If you see
that: export everything, then Erase all data, then import back just the recent
months you still want on the tablet.


Updating to a newer version
---------------------------
Just replace pm_logger.html with the new one. Your readings are untouched.

That works because the browser keeps your data separately from the file, not
inside it. So a new file - even one with a different name, in a different
folder - picks up exactly the same data. Nothing to export first, nothing to
import afterwards.

The version number is at the bottom right of the Data tab, next to
"Diagnostics". Quote it if you ever report a problem.

One thing to avoid: do not keep old copies of pm_logger.html lying around in
Downloads. If you open an old one by mistake it will notice that your data
came from a newer version, refuse to touch it, and say so in red at the top.
Nothing is lost, but it is a confusing five minutes. Delete old copies.


If something goes wrong
-----------------------
At the very bottom of the Data tab there is a small grey "Diagnostics" line.
It is deliberately out of the way. Tap it and you get a description of this
tablet and this tool: version numbers, how full storage is, how much you have
logged, and any errors the page has hit.

Send that report and I can usually work out what happened. Without it, I am
guessing.

  Copy to clipboard    Copies the report, ready to paste into a message.
  Download as a file   Saves pm_diagnostics_<date>.txt. Use this if the copy
                       button will not work.
  Run self-test        Checks the fiddly parts still work on this tablet -
                       the CSV round trip, the limit checking, the dates. It
                       cannot touch your readings, and it proves that by
                       checking them before and after.
  Clear error log      Wipes the recorded errors. Your readings are not
                       affected.

Two things worth knowing about that report:

Tool and reading names are NOT included unless you tick the box. Counts and
structure are enough to diagnose almost anything, so your equipment names do
not need to leave the fab. Tick it only if you are asked to.

No reading value ever appears in it, ticked or not. It counts things - how
many rounds, how many out of range - never what the numbers were.

There is also a USAGE section counting what you do: rounds finished, exports
taken, how often you back-fill a missed day. Nothing is sent anywhere from it.
It is there so that when you do send a report, the tool can be improved in the
places you actually use.


The tablet capability test
--------------------------
There is a second page in the project, pm_logger_capability_test.html. You do
not need it to log a round. It answers one question that can only be answered
on the real tablet: can this browser write straight into a folder you choose,
and does it REMEMBER that folder tomorrow?

That matters because if the answer is yes, exports could go directly into your
OneDrive folder with no taps at all. If it only remembers until you close the
browser, it is not worth building, and the Edge download-folder setting above
stays the better answer.

Run it when you first set up a tablet, or if IT changes the browser:

  1. Double-click pm_logger_capability_test.html.
  2. Run test 1, then test 2.
  3. CLOSE the page completely, reopen it, then run test 3. The restart is the
     whole point of the test - do not skip it.
  4. Send on what the Result boxes say.

It stores nothing except the folder you pick, and it cannot touch your
readings. Keep it for the next tablet.


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
