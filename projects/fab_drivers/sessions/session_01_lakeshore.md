# Session 1 of 10: Lakeshore temperature monitor driver

Work in the Partybarte repository, in the project `projects/fab_drivers`.

Read `projects/fab_drivers/CLAUDE.md` before anything else. It is the standing
brief for every driver session and it loads automatically. `DECISIONS.md` holds
the reasoning behind the design, and `REVIEW.md` records what has actually been
verified and what was only assumed.

## Where things stand

The shared core is built and tested. It covers the command policy that enforces
read-only, raw frame audit logging, daily CSV history, a mock serial port, the
serial transport, the driver base class with its one second timeout and two
retries, the poller, and the trend page generator. 92 tests pass and none of them
need hardware.

No device drivers exist yet. `fab_drivers/devices/` is empty. This is the first
one, so it sets the example the other nine will follow. Take the extra care that
deserves.

## Build the driver

**Device:** Lakeshore 218, 224 and 336 temperature monitors. They read cryo stage
and cold head temperatures. RS-232, and Ethernet on some models. The protocol is
a SCPI style ASCII, for example `KRDG? A` to read a temperature.

## Do this in order

1. **Research first.** The manuals are in `manuals/lakeshore/`, supplied by the
   project owner. Verify the exact command syntax, the serial settings, the line
   terminator, and the reply format against worked examples in them.

   Write nothing from memory of SCPI. Do not fetch anything yourself, and do not
   substitute a search result or a vendor's own source code for the manual.
   `manuals/README.md` has the rule and the reason.

   If `manuals/lakeshore/` is empty or is missing one of the three models, the
   session is blocked. Update `manuals/FETCH_PROMPT.md` with what is still
   wanted, hand it over as a file, and stop. A driver blocked on a document is an
   honest outcome. Plausible command syntax that was never verified is worse than
   no driver, because it looks finished.

2. **Write `devices/lakeshore/PROTOCOL.md`** from the manual, before the code.
   Serial settings, terminator, command format, reply format, error handling, the
   read-only commands used in version 1, and anything banned outright with the
   reason. Name the manual and its part number, and say where it was found.

3. **Write `devices/lakeshore/driver.py`.** A class inheriting
   `core.device.Device`, writing `build_frame` and `parse_reply`. Build its
   `CommandPolicy` with the read-only allowed list, any banned commands with
   reasons, and the sensor inputs as `targets`.

4. **Write `devices/lakeshore/mock.py`.** A responder for `MockSerial` that
   answers like the real instrument, including the failure cases: silence, a
   malformed reply, and whatever the instrument returns for a sensor that is not
   connected or is out of range.

5. **Write `tests/test_lakeshore.py`** against the mock. It must pass with no
   hardware, because that is what CI runs. Cover the good path, an unreadable
   sensor, and a command that must be refused.

6. **Build its trend page** with `core.trend_page.write_trend_page`. Do not write
   a new page. Generate one from sample data and open it once, to check it shows
   what you meant.

7. **Record what you did.** A dated entry in `DECISIONS.md`, and anything you
   could not verify added to `REVIEW.md`. The review pass at the end depends on
   knowing what was checked and what was assumed.

8. **Run `pytest -q` from the repository root**, commit, and push.

9. **Write the next session's prompt** as
   `sessions/session_02_granville_phillips.md`, covering the Granville-Phillips
   gauge controllers, and hand that file over. Hand over the file itself rather
   than pasting the prompt into the chat as text. Update the table in
   `sessions/README.md` at the same time.

## Three decisions this device forces, which the core has not met yet

Do not guess at these. Decide them, and write the reasoning into `DECISIONS.md`.

1. **One driver for all three models, or one each?** The 218, 224 and 336 differ
   in channel count and in what they can report. One class with a model setting
   is probably right, but the manual decides that, not this prompt.

2. **Ethernet.** The 336 has it. `core/transport.py` assumes a serial port today.
   If Ethernet is in scope for version 1, the core needs a socket transport
   alongside the serial one, which is a change to shared code that every later
   driver inherits. If it is not in scope, say so and move on. Do not bolt a
   socket into the driver.

3. **Sensor inputs are sub-units.** Inputs A, B, C and D are exactly what the
   `targets` mechanism in `CommandPolicy` is for. Use it. Do not fold the input
   letter into the command string. That was the first design and it did not
   scale.

## Rules that do not bend

Read-only. Research first. Always send through `Device.query`. One process owns
the port. Log every raw frame. Add a package only in the change that imports it.
Nothing reaches the internet at runtime. Short sentences, plain words, no em
dashes, boring explicit code with comments, written for a beginner in Python.

The full versions are in `CLAUDE.md`.
