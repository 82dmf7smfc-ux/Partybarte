# Session 4 of 10: Edwards nXDS, iXL and nEXT pump driver

Work in the Partybarte repository, in the project `projects/fab_drivers`.

Read `projects/fab_drivers/CLAUDE.md` before anything else. It is the standing
brief for every driver session and it loads automatically. `DECISIONS.md` holds
the reasoning behind the design, and `REVIEW.md` records what has actually been
verified and what was only assumed.

## Where things stand

The shared core is built and tested. It covers the command policy that enforces
read-only, raw frame audit logging, daily CSV history, a mock serial port, the
serial transport, the driver base class with its one second timeout and two
retries, the poller, and the trend page generator. 227 tests pass across
`fab_drivers` and none of them need hardware.

The core grew twice in session 3, and both changes are yours to inherit.

- **`SerialTransport` can read a reply by a length written inside it**, not only
  up to a terminator. Pass `reply_size`, a function that is given the bytes so
  far and returns the total frame length or `None` for "cannot tell yet". Leave
  it out and the transport reads up to the terminator exactly as before. The
  Edwards pumps are ASCII with a terminator, so you will not need it. It is
  worth knowing it is there.
- **The trend page generator can draw two lines on one pair of axes.** Pass
  `overlays`, a dictionary of column name to the column drawn over it. It exists
  for a reading and the setpoint it is holding. Read `setpoint_overlay` in
  `devices/thermo_chiller/trend.py` for how a driver asks for it, and read the
  docstring on `render_trend_page` for why separate charts could not answer the
  question.

Three drivers exist.

- `devices/lakeshore/` for the Lakeshore 218, 224 and 336 temperature monitors.
- `devices/granville_phillips/` for the Granville-Phillips 275, 375, 350 and 356
  pressure gauges.
- `devices/thermo_chiller/` for the Thermo NESLAB and ThermoFlex chillers.

**Read all four files of one of them before starting**, because the shape is
what you are copying. Granville-Phillips is the closest match for an ASCII
protocol with a terminator, which is what you are building:

- `fab_drivers/devices/granville_phillips/PROTOCOL.md`
- `fab_drivers/devices/granville_phillips/driver.py`
- `fab_drivers/devices/granville_phillips/mock.py`
- `fab_drivers/devices/granville_phillips/trend.py`
- `tests/test_granville_phillips.py`

Then read the Thermo chiller's `PROTOCOL.md` sources section and its `REVIEW.md`
section, even though the protocol is nothing like yours. It is the only one so
far written with a manual open, and it is the example of what a well sourced
`PROTOCOL.md` looks like and of how to say which half of a driver is solid and
which half is not.

**Read all three driver sections of `REVIEW.md`.** Sessions 1 and 2 had no
manual at all and say item by item what is a worked example and what is a guess.
Session 3 had two manuals and still has an unverified half. Copy the habit of
saying which is which.

## Build the driver

**Device:** Edwards vacuum pumps. The nXDS dry scroll pumps, the iXL dry pumps,
and the nEXT turbomolecular pumps with their TIC or the pump's own controller.

**What a trend wants:** pump speed or frequency, motor power, motor and body
temperature, running hours, and the pump's status and fault bits. On a turbo,
speed against time during spin-up and the current draw at speed are the two
numbers that show a bearing going.

**This one should be the easiest protocol since session 1.** It is ASCII, it has
a terminator, and the query forms are short. That is the point of it sitting
fourth: after a binary framed protocol with a checksum, this is a chance to
build something quickly and well rather than to fight the wire.

## Do this in order

1. **Research first, and start with GitHub.** This is the lesson session 3
   learned and it is worth more than anything else in this list.

   The egress proxy on this machine refuses every manufacturer and distributor
   site. Sessions 1, 2 and 3 all confirmed it: `lakeshore.com`, `mks.com`,
   `idealvac.com`, `lesker.com`, `manualslib.com`, `thermofisher.com`,
   `edwardsvacuum.com` is very likely the same, and every university and
   national lab mirror tried. The WebFetch tool is refused by the same policy.
   `github.com` and the package registries are reachable and nothing else is.
   **Test that in the first two minutes** so you know which kind of session you
   are in.

   Then, before writing any fetch prompt:

   - **Search GitHub for the manual itself.** Session 3 found two Thermo NESLAB
     manuals as ordinary PDF files in the `manuals/` folder of
     `github.com/octopode/bathtime`, cloned the repository, extracted the text
     with `pypdf` and read the protocol appendices in full. That single step
     turned the session from guesswork into a driver written from the
     manufacturer's own document. Lab groups keep manuals next to the code that
     drives the instrument. Search for `edwards nxds`, `edwards next`, `edwards
     tic`, and look in any hit's `manuals/`, `docs/` or `doc/` folder.
     `pypdf` needs a clean virtualenv on this machine, because the system
     `cryptography` package is broken. `python3 -m venv /tmp/pdfenv` then
     `/tmp/pdfenv/bin/pip install pypdf` works.
   - **Search GitHub for driver code.** Look at EPICS support modules,
     `github.com/CINF/PyExpLabSys`, and any lab group repository that logs a
     turbo pump. Vendor or community source code is weaker than a manual and
     carries no worked examples.
   - **The web search tool can read PDFs this machine cannot download.** Ask it
     narrow questions and it returns specific statements, sometimes a worked
     example. That is manual content relayed by a summariser, not a manual.
     Rank it accordingly and say so.

   `add_repo` attaches a public repository and then it clones like any other.

   If all of that fails, say so and write a fetch prompt using
   `manuals/README.md`. `manuals/FETCH_PROMPT_THERMO_CHILLER.md` is the most
   recent and is the example to copy when part of the protocol is already
   sourced. `manuals/FETCH_PROMPT_GRANVILLE_PHILLIPS.md` is the one to copy when
   none of it is.

   Whatever you end up with, name it in `PROTOCOL.md` and say how strong it is.
   Anything not confirmed by a manual goes in `REVIEW.md` as unverified.

2. **Write `devices/edwards_pumps/PROTOCOL.md`** from the sources, before the
   code. The message format, the terminator, the query and the reply forms, the
   serial settings, the object or parameter numbering if there is one, the error
   returns, the read-only commands used in version 1, and anything banned
   outright with the reason. Name every source and rank it.

3. **Write `devices/edwards_pumps/driver.py`.** A class inheriting
   `core.device.Device`, writing `build_frame` and `parse_reply`. Build its
   `CommandPolicy` with the read-only allowed list and banned commands with
   reasons.

4. **Write `devices/edwards_pumps/mock.py`.** A responder for `MockSerial` that
   answers like a real pump, including the failure cases: silence, a malformed
   reply, whatever the pump returns for an unknown command, and a pump that is
   stopped, accelerating, or in a fault state.

5. **Write `tests/test_edwards_pumps.py`** against the mock. It must pass with
   no hardware, because that is what CI runs. Cover the good path, the framing,
   a pump at each of its states, a fault, and a command that must be refused.

6. **Build its trend page** with `core.trend_page.write_trend_page`. Do not
   write a new page. Speed, power and temperature are all linear.
   **Generate a page from sample data and open it in a browser.** Chromium is
   installed at `/opt/pw-browsers/chromium-1194/chrome-linux/chrome` and
   Playwright drives it if you pass `executable_path` and `--no-sandbox`.
   Sessions 2 and 3 each found a real defect that way that the tests had missed.
   That is now two out of two, so treat it as a required step and not a nicety.

7. **Record what you did.** A dated entry in `DECISIONS.md`, and anything you
   could not verify added to `REVIEW.md`, item by item.

8. **Run `pytest -q` from the repository root**, commit, and push. Note that
   `projects/alarm_pareto` needs pandas and openpyxl to collect, so a fresh
   container needs `pip install -r projects/alarm_pareto/requirements.txt`
   before the root run works. `pytest` itself is not installed either.

9. **Write the next session's prompt** as `sessions/session_05_mks.md`, covering
   the MKS 937B and 946 gauge controllers, and hand that file over. Hand over
   the file itself rather than pasting the prompt into the chat as text. Update
   the table in `sessions/README.md` at the same time.

## Five decisions this device forces, which the core has not met yet

Do not guess at these. Decide them, and write the reasoning into `DECISIONS.md`.

1. **Three pump families that are probably not one protocol, and this time the
   answer is likely to be no.** The nXDS is a scroll pump, the iXL is a dry
   pump, and the nEXT is a turbo. They are different products from different
   parts of the range and they may well not share a message format at all.

   The two drivers that cover several models with one class did so because the
   models turned out to share a protocol, and session 3 checked that explicitly
   for the chiller rather than assuming it. Do the same here and be ready for
   the opposite answer. If the nEXT and the nXDS genuinely differ, that is
   **two driver classes in one folder**, not one class with a flag, and it is
   better to ship two honest classes than one that pretends.

   The thing that decides is the framing and the reply shape, not the command
   list. Different commands with the same framing is one class with model
   profiles, which is what `ModelProfile` in the chiller and gauge drivers is
   for. Different framing is two classes.

2. **A turbo pump controller may be a box with pumps behind it.** The Edwards
   TIC instrument controller drives several pumps and gauges from one serial
   port. If it does, the pump or channel is an address and belongs in
   `CommandPolicy(targets=...)`, checked separately from the command, and it
   goes in the frame rather than in the command string. Both existing addressed
   drivers do this. Do not fold the address into the command.

   And if the reply echoes which channel answered, **check it against the
   channel you asked for**. That check has caught nothing yet because nothing
   has run on hardware, and it is the single cheapest protection in the library.

3. **A pump has states, and a number from a stopped pump is not a reading.**
   This is the trap every device in this project has had in a different shape. A
   Lakeshore sensor that is disconnected answers with a plausible temperature. A
   gauge that is off answers `9.99E+09`. A chiller reports a bath temperature
   whether or not it is running.

   A stopped turbo reports a speed of zero, which is a true number and a
   meaningless one, and it will average into a trend as though the pump were
   running slowly. An accelerating turbo reports a speed that is climbing for
   real. Those two need to be told apart.

   So decide what the driver returns for a pump that is not at speed, and decide
   it against the status word rather than against the number. Read the status
   alongside every speed, the way the Lakeshore driver reads `RDGST?` alongside
   every temperature.

4. **Running hours is a counter, not a measurement, and the trend page has never
   met one.** Every column so far has been a quantity that goes up and down.
   Hours only ever increase, and what anybody wants from it is not the line but
   the number, or the rate of change.

   Decide whether it goes on the trend page at all. It may belong only in the
   summary table, or only in the CSV. If the shared generator genuinely needs
   something new for it, put it in the generator so every driver gets it, and be
   honest about whether it is needed rather than adding it because it is
   interesting. Session 3 added `overlays` because opening the page showed the
   page could not answer the question it existed for. That is the bar.

5. **A pump start and a pump stop are on the other side of the line, and they
   will be one character away from the reads.** This is the same shape as the
   chiller's Read Setpoint at `70` and Set Setpoint at `F0`, and it deserves the
   same treatment.

   Stopping a turbo under a process is worse than most things in this library.
   Starting one against a vented chamber is worse still. Get the read and the
   write forms distinguished carefully from the manual, put the reads on the
   allowed list and the writes on the banned list with reasons.

   **Look for a structural rule as well as a list.** The chiller had one: every
   write command in both manuals has bit 7 set, so `build_frame` refuses any
   command byte at or above `0x80` outright, as a second line of defence behind
   the allowed list. Edwards ASCII protocols usually distinguish a query from a
   command by a character in the message itself. If they do, refuse the command
   form structurally in `build_frame` and say in `PROTOCOL.md` whether that rule
   is stated in the manual or merely observed across its tables. If the manual
   is not clear about which form is which, allow neither and say so.

## Rules that do not bend

Read-only. Research first, and say what your sources were. Always send through
`Device.query`. One process owns the port. Log every raw frame. Add a package
only in the change that imports it. Nothing reaches the internet at runtime.
Short sentences, plain words, no em dashes, boring explicit code with comments,
written for a beginner in Python.

The full versions are in `CLAUDE.md`.
