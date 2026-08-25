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

   If a tool has CHAMBERS, see "Tools with chambers" below before you start.

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


Finding your way around the Tools tab
-------------------------------------
Chamber types and tools show as one-line summary rows. Tap one to open it,
tap again to close. Only the one you are editing is open, so the whole setup
fits on a screen or two however many tools you add.

Each row says what is inside it - "PVD, 4 chambers, 3 readings" - and turns
amber if something still needs doing.

At the top, a "Setup not finished" panel lists anything incomplete: chamber
types with no readings, and tools that are not on the round because nothing on
them can be logged yet. It disappears once everything is set up.

A chamber whose type has no readings has nothing to log, so it is SKIPPED on
the round rather than counted. Before, such a chamber made its tool impossible
to finish. It still shows on the tool screen under "Not set up yet" so you
remember to finish it.

Pressing Enter in any "add" box does the same as tapping the button beside it.
Adding six readings is type-Enter-type-Enter rather than six trips across the
screen.


Tools with chambers
-------------------
A cluster tool's chambers wear differently. PM1 and PM3 do not share a process
kit and do not share RF hours, so they are logged separately.

Three ideas, and only the first is new:

  A CHAMBER TYPE is a name plus a list of readings, like "Etch" or "Strip".
  A CHAMBER is a name and a type, like "PM1 is an Etch chamber".
  TOOL READINGS belong to the whole machine, like facility nitrogen.

Chambers of the same type log the same things. So you write the Etch reading
list ONCE, and every etch chamber on every tool uses it. Two identical etchers
share one definition rather than two copies that slowly drift apart.

Setting it up:

  1. Tools tab, "Chamber types" at the top. Add a type, for example Etch.
     Add the readings taken at any etch chamber, with their limits.
  2. Add a second type if your tool has different chambers, for example Strip.
  3. Further down, on the tool itself, add each chamber by name (PM1, PM2)
     and pick its type from the drop-down.
  4. Put anything that belongs to the whole machine under "Readings logged at
     the tool itself". Leave it empty if everything you log is per chamber.

Walking a tool with chambers:

  Tap the tool and you get a list: its tool readings, then each chamber, each
  with its own done or not-done mark. Tap one, type its readings, then
  "Save and next" walks you through the rest. The tool is only counted as
  logged once every chamber is in.

A tool with no chambers is unchanged. Tap it and you are straight into its
readings, exactly as before. A wet bench needs no chambers at all.

If a chamber was not run today, leave it blank. Blank readings never appear in
the export.

Changing a reading on a TYPE changes it for every chamber of that type, on
every tool. That is the point of types, and it is also the thing to be careful
about. A type that is still in use cannot be deleted; the page says which tool
is in the way.


Typing each reading only once
-----------------------------
Every reading you set up anywhere becomes a suggestion everywhere else. Start
typing a name in any "add a reading" box and the ones you have already used
drop down, showing their unit, limits and which type they came from. Pick one
and the unit and limits are filled in for you.

It is a SUGGESTION, not a link. Once added, that type owns its copy, so
changing a limit on Etch Standard never touches CVD Teos. An etch chamber and
a sputter chamber can measure the same thing to different specs.

One thing it does enforce: the spelling already in use wins. Type "rf time on"
and you get "RF Time On". Two spellings of one reading become two separate
columns in Excel, which is the kind of mistake you only notice months later
when a chart looks wrong.

Setting up a type much like one you already have? Use "Copy its readings here"
at the bottom of the type. Pick the similar type, tap once, and adjust
whatever differs. For two CVD types or two etch types this is usually faster
than adding readings one at a time.

The setup screen also warns if the same reading name is logged in two
different units - say "RF Time On" in hours on one type and minutes on
another. Nothing breaks on the tablet, but Excel would treat them as one
column and add hours to minutes.


When one chamber runs to a different spec
-----------------------------------------
Sometimes two chambers do the same process but are held to different numbers -
a tighter kit life on one, a looser leak rate on another. A chamber can set
its own min and max for any reading, without affecting the others.

  1. Tools tab, find the chamber, press "Limits".
  2. Each reading shows its type default, and boxes for this chamber's own
     min and max.
  3. Change a number and that reading turns amber and is marked "custom".
     The button then reads "Limits (1 custom)" so you can see it at a glance.
  4. "Use the type default again" puts a reading back on the type.

Only the min and max can differ. The reading's name and unit always come from
the type, so the chambers stay comparable in Excel. Type the type's own numbers
back in and the custom setting simply disappears - there is no difference
between "uses the type" and "happens to agree with the type".

While a reading is on the type default, changing the type still moves it. Once
a chamber has its own number, that chamber stops following the type for that
one reading only.

On the entry screen a custom limit says so: "Expected 60 or below (set for
this chamber)". Nobody should have to wonder why the identical chamber next
door flags at a different number.

The export always shows the limit a chamber was ACTUALLY checked against, so
the Min and Max columns always agree with the Status beside them.


Kit life, and the fleet summary email
-------------------------------------
Some readings are not measurements, they are consumption: kit life, target
life, RF energy. The number climbs until the part is replaced, and what you
care about is how much is left.

Tell the tool which readings work that way. On the Tools tab, tick
"Counts up to a limit" on the reading and put the rated life in Max. From then
on:

  - The entry screen shows "62% of life remaining" as you type.
  - The Today tab shows a fleet table of every chamber, with anything low
    coloured, before you start the round.
  - The Data tab can build the summary email for you.

Only ticked readings get a percentage. A reading like chamber pressure, with a
min AND a max, is a process window rather than a consumable, and reporting a
percentage of it would be meaningless.

  % remaining  =  (rated life - logged value) / rated life

Nothing logged, no rated life, or a chamber that does not take that reading all
show as N/A, which is why your table has N/A in it.

A chamber past its rated life shows a NEGATIVE percentage, not zero. A kit at
130% of life reads -30%, because "used up" and "thirty percent overdue" are
different things to know.

If a chamber has its own kit rating, set through its Limits button, that rating
is what it is measured against.


Sending the summary
-------------------
Data tab, "Generate email". It builds the message - opening line, date, and
the table - and shows it to you first.

  Copy for Outlook     Puts the table on the clipboard as real formatting.
                       Paste into Outlook and the colours come with it.
  Download as a file   Saves fleet_summary_2026-08-24.html for when the
                       clipboard is blocked, or you want to keep the file.

If the copy button cannot get permission, the table is selected for you
instead - press Ctrl+C and the formatting still comes across.

The opening line and the red and amber thresholds are boxes on that panel.
Defaults are red under 15%, amber under 25%.

The figures are the most recent reading on or before the date you are viewing.
Any chamber not logged in the last two weeks is named underneath, because a
percentage from three weeks ago is not the same fact as today's.


About the limits
----------------
A reading outside its min or max turns red and says why. The value still
saves, every time. Nothing is ever refused or blocked.

That is deliberate. On a round you record what the tool screen actually says,
good or bad. A tool that argues with you about a bad number is a tool that
gets fed made-up numbers.

Leave min and max blank for a reading you just want logged, not checked.


EXTRACT THE ZIP PROPERLY FIRST
------------------------------
Do not double-click pm_logger.html from inside the zip. Windows quietly unpacks
it to a temporary folder to do that, and it works - until Windows clears that
folder and the tool is gone.

Right-click the zip, choose Extract All, and put the pm_logger folder somewhere
permanent. Next to your OneDrive PM folder is ideal. Make your shortcut point
at the extracted file.

If you get this wrong the tool notices and says so in amber at the top of the
page. Your readings are safe either way - the browser stores them against the
address, not the folder - but hunting for a vanished tool mid-round is a bad
morning.


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


The export buttons
------------------
On the Data tab:

  Export this round (CSV)            pm_round_2026-08-24.csv
  Export this round to a folder      the same file, but you choose where
  Export everything for Excel        pm_readings_through_2026-08-24.csv
  Export full backup (JSON)          pm_backup_through_2026-08-24.json

The second one opens a normal Windows "Save as" box, so you can put one file on
a USB stick or in a different folder without changing your Edge settings. It is
for exceptions. For the daily round the first button plus the download-folder
setting above is fewer taps, so use that.

That button only appears if your browser supports it. If saving where you
picked fails for any reason, the file goes to the download folder instead
rather than being lost, and the page tells you that is what happened.

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

  Date        Tool      Chamber  Chamber type  Data point       Value  Status
  2026-08-24  Etcher 3                        Chiller temp     20.4   OK
  2026-08-24  Etcher 3  PM1      Etch          Kit life used    44     OK
  2026-08-24  Etcher 3  PM2      Etch          Kit life used    95     HIGH

Tool readings leave the Chamber columns empty, so filtering on Chamber cleanly
separates the two. To trend one chamber, drag Chamber into Filters. To compare
every chamber of one kind, filter on Chamber type instead.

That is one row per reading rather than a wide grid, on purpose: your tools
each log different things, so a grid would be mostly empty boxes.

To chart it:

  1. Click any cell in the data.
  2. Insert > PivotTable > OK.
  3. Drag Date into Rows.
  4. Drag Data point into Columns. For a chambered tool, drag Chamber in
     above it so each chamber gets its own line.
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

ALREADY ANSWERED on Windows + Edge, 24 August 2026:

  Test 1  Save As dialog ........ WORKS
  Test 2  Pick a backup folder .. WORKS
  Test 3  After a full restart .. PARTLY

PARTLY means the tablet remembered the folder but not the permission. Writing
into it silently would have cost a permission tap every morning, which is worse
than the download-folder setting that costs nothing. So the logger does not do
it. Test 1 passing is why the "Export this round to a folder" button exists.

You only need to run this again on a NEW tablet, or if IT changes the browser:

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
