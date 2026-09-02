# Session 2 of 10: Granville-Phillips gauge controller driver

Work in the Partybarte repository, in the project `projects/fab_drivers`.

Read `projects/fab_drivers/CLAUDE.md` before anything else. It is the standing
brief for every driver session and it loads automatically. `DECISIONS.md` holds
the reasoning behind the design, and `REVIEW.md` records what has actually been
verified and what was only assumed.

## Where things stand

The shared core is built and tested. It covers the command policy that enforces
read-only, raw frame audit logging, daily CSV history, a mock serial port, the
serial transport, the driver base class with its one second timeout and two
retries, the poller, and the trend page generator. 122 tests pass and none of
them need hardware.

One driver exists, for the Lakeshore 218, 224 and 336 temperature monitors. It
is the example this one follows. Read all four of its files before starting,
because the shape is what you are copying:

- `fab_drivers/devices/lakeshore/PROTOCOL.md`
- `fab_drivers/devices/lakeshore/driver.py`
- `fab_drivers/devices/lakeshore/mock.py`
- `tests/test_lakeshore.py`

**Read the Lakeshore section of `REVIEW.md` too.** That driver was written from a
research file rather than a manual, and the file lists item by item what is a
worked example and what is a guess. Do not copy the situation. Copy the habit of
saying which is which.

## Build the driver

**Device:** Granville-Phillips 275 and 375 Convectron gauges, and 350 and 356
Micro-Ion gauges. They read chamber and foreline pressure. ASCII over RS-232 or
RS-485, with `#` address framing.

## Do this in order

1. **Research first.** Find the official Granville-Phillips instruction manuals
   for these models. Verify the frame format, the address field, the serial
   settings, the terminator and the reply format against worked examples in the
   manual.

   Search the web and download them. `idealvac.com` hosts a lot of vacuum
   equipment manuals free and without a login, and these are short manuals. If
   the network refuses, say so and write a fetch prompt using
   `manuals/README.md`, then hand it over as a file.

   Whatever you end up with, name it in `PROTOCOL.md` and say how strong it is.
   Anything not confirmed by a manual goes in `REVIEW.md` as unverified.

2. **Write `devices/granville_phillips/PROTOCOL.md`** from the sources, before
   the code. Serial settings, the `#` framing and how the address sits inside
   it, the terminator, command format, reply format, error handling, the
   read-only commands used in version 1, and anything banned outright with the
   reason. Name every source and rank it.

3. **Write `devices/granville_phillips/driver.py`.** A class inheriting
   `core.device.Device`, writing `build_frame` and `parse_reply`. Build its
   `CommandPolicy` with the read-only allowed list, banned commands with
   reasons, and the gauge addresses as `targets`.

4. **Write `devices/granville_phillips/mock.py`.** A responder for `MockSerial`
   that answers like the real controller, including the failure cases: silence,
   a malformed reply, a wrong address, and whatever the controller returns for a
   gauge that is off or faulted.

5. **Write `tests/test_granville_phillips.py`** against the mock. It must pass
   with no hardware, because that is what CI runs. Cover the good path, an
   unreadable gauge, a command that must be refused, and the framing.

6. **Build its trend page** with `core.trend_page.write_trend_page`. Do not
   write a new page. Look at `devices/lakeshore/trend.py`, which is the thin
   wrapper pattern to copy. Generate one from sample data and open it once, to
   check it shows what you meant.

   Pressure spans decades. The shared generator plots linearly. Read the
   decision below before doing anything about that.

7. **Record what you did.** A dated entry in `DECISIONS.md`, and anything you
   could not verify added to `REVIEW.md`, item by item.

8. **Run `pytest -q` from the repository root**, commit, and push.

9. **Write the next session's prompt** as `sessions/session_03_thermo_chiller.md`,
   covering the Thermo Neslab and ThermoFlex chillers, and hand that file over.
   Hand over the file itself rather than pasting the prompt into the chat as
   text. Update the table in `sessions/README.md` at the same time.

## Four decisions this device forces, which the core has not met yet

Do not guess at these. Decide them, and write the reasoning into `DECISIONS.md`.

1. **A log scale on the trend page.** This is the big one, and it is the first
   thing this device asks of shared code. Pressure runs from atmosphere down to
   1e-9 torr. On a linear axis every reading below about 1 torr sits flat on the
   bottom of the chart, so the pumpdown that matters is invisible. The Lakeshore
   driver did not hit this because temperatures span one decade, not nine.

   The trend page generator is shared by all ten drivers. Three of them read
   pressure. So the fix belongs in `core/trend_page.py` as a per-column choice,
   not in this driver, and not by writing a second page. `CLAUDE.md` says so
   directly: if the shared generator cannot do something a device genuinely
   needs, improve the generator so every driver gets it.

   Watch the gap rule while you do it. A gap must still break the line. And
   decide what a zero or a negative reading does to a log axis, because a gauge
   that is off may well report one.

2. **The address is in the frame, not in the command.** `#` framing puts a gauge
   address in every message. That is exactly what `targets` in `CommandPolicy`
   is for. Do not fold the address into the command string. Read the Lakeshore
   driver's `build_frame` for how the two are kept apart.

   Check what the address range actually is, and whether there is a broadcast
   address. If there is, think hard before allowing it.

3. **RS-485 is a shared bus.** RS-232 is one controller on one cable. RS-485 can
   be several on one pair, which is a different safety situation, because a frame
   meant for one gauge reaches all of them. The core assumes one device per
   transport today. Decide whether version 1 supports a multi-drop bus or one
   controller at a time, and say which. If it is one at a time, say so plainly
   rather than leaving it to be discovered.

4. **Units.** These controllers can report torr, mbar or pascal, and the setting
   lives in the instrument. A trend file that silently changes units halfway
   through is worse than useless, because the numbers stay plausible. Find out
   whether there is a read-only query that says which units are configured. If
   there is, read it at start up and put the unit in the column name. If there
   is not, that is a real finding and belongs in `REVIEW.md`.

   Do not add a command that sets the units. That is a write.

## Rules that do not bend

Read-only. Research first, and say what your sources were. Always send through
`Device.query`. One process owns the port. Log every raw frame. Add a package
only in the change that imports it. Nothing reaches the internet at runtime.
Short sentences, plain words, no em dashes, boring explicit code with comments,
written for a beginner in Python.

The full versions are in `CLAUDE.md`.
