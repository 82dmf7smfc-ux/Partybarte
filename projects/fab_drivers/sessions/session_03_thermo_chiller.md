# Session 3 of 10: Thermo Neslab and ThermoFlex chiller driver

Work in the Partybarte repository, in the project `projects/fab_drivers`.

Read `projects/fab_drivers/CLAUDE.md` before anything else. It is the standing
brief for every driver session and it loads automatically. `DECISIONS.md` holds
the reasoning behind the design, and `REVIEW.md` records what has actually been
verified and what was only assumed.

## Where things stand

The shared core is built and tested. It covers the command policy that enforces
read-only, raw frame audit logging, daily CSV history, a mock serial port, the
serial transport, the driver base class with its one second timeout and two
retries, the poller, and the trend page generator. The generator now draws a
column on a linear or a log axis, per column, which session 2 added. 167 tests
pass across the repository and none of them need hardware.

Two drivers exist.

- `devices/lakeshore/` for the Lakeshore 218, 224 and 336 temperature monitors.
- `devices/granville_phillips/` for the Granville-Phillips 275, 375, 350 and 356
  pressure gauges.

Read all four files of one of them before starting, because the shape is what
you are copying. The Granville-Phillips one is the closer match for a device
with an address in its frame, and it is the more recent:

- `fab_drivers/devices/granville_phillips/PROTOCOL.md`
- `fab_drivers/devices/granville_phillips/driver.py`
- `fab_drivers/devices/granville_phillips/mock.py`
- `fab_drivers/devices/granville_phillips/trend.py`
- `tests/test_granville_phillips.py`

**Read both driver sections of `REVIEW.md` too.** Neither driver was written
from a manual. This machine's network egress policy refuses every manufacturer
and distributor site, and both sections list item by item what is a worked
example and what is a guess. Do not copy the situation. Copy the habit of saying
which is which.

## Build the driver

**Device:** Thermo Scientific chillers, the Neslab line and the ThermoFlex line.
They supply process cooling water. Bath temperature, setpoint readback, pump
pressure, and fault and alarm state are what a trend wants.

**This is the first one that is not plain ASCII.** It is a binary framed
protocol with a checksum. That is the whole reason it sits third in the build
order, and it is what makes this session different from the two before it.

## Do this in order

1. **Research first.** Find the official Thermo instruction manuals for these
   chillers. Verify the frame layout, the checksum, the command bytes and the
   reply layout against worked examples in the manual.

   Search the web and download them. Be warned by what happened in session 2:
   the egress proxy on this machine refused `mks.com`, `idealvac.com`,
   `lesker.com`, `manualslib.com` and every university and national lab mirror
   found, with a 403 on the CONNECT. `github.com` and the package registries
   were reachable and nothing else was. Test early whether you can reach
   anything, so you know within a few minutes which kind of session this is.

   Two routes worked in session 2 and are worth knowing about.

   - **The web search tool can read PDFs this machine cannot download.** Ask it
     narrow questions and it returns specific statements from the document,
     sometimes including a worked example. That is manual content relayed by a
     summariser, not a manual. Rank it accordingly and say so.
   - **Open source control system code on GitHub is reachable and is a real
     cross-check.** `epics-modules/vac` gave session 2 the Series 350 command
     set. For a chiller, look at EPICS support modules, at
     `github.com/CINF/PyExpLabSys` which has a drivers folder, and at any lab
     group repository that logs a chiller. `add_repo` attaches a public
     repository and then it clones like any other. Vendor or community source
     code is weaker than a manual and carries no worked examples, so anything
     resting on it alone is unverified.

   If the network refuses, say so and write a fetch prompt using
   `manuals/README.md`, then hand it over as a file.
   `manuals/FETCH_PROMPT_GRANVILLE_PHILLIPS.md` is the most recent worked
   example, and the part of it worth copying is the numbered list of questions
   the documents have to answer.

   Whatever you end up with, name it in `PROTOCOL.md` and say how strong it is.
   Anything not confirmed by a manual goes in `REVIEW.md` as unverified.

2. **Write `devices/thermo_chiller/PROTOCOL.md`** from the sources, before the
   code. The byte layout of a frame, the checksum algorithm with a worked
   example, the serial settings, the command bytes, the reply layout, error
   handling, the read-only commands used in version 1, and anything banned
   outright with the reason. Name every source and rank it.

3. **Write `devices/thermo_chiller/driver.py`.** A class inheriting
   `core.device.Device`, writing `build_frame` and `parse_reply`. Build its
   `CommandPolicy` with the read-only allowed list and banned commands with
   reasons.

4. **Write `devices/thermo_chiller/mock.py`.** A responder for `MockSerial` that
   answers like a real chiller, including the failure cases: silence, a bad
   checksum, a truncated frame, and whatever the chiller returns when it is in
   an alarm state or switched off at the front panel.

5. **Write `tests/test_thermo_chiller.py`** against the mock. It must pass with
   no hardware, because that is what CI runs. Cover the good path, the checksum
   both ways, a chiller in alarm, a command that must be refused, and the
   framing.

6. **Build its trend page** with `core.trend_page.write_trend_page`. Do not
   write a new page. `devices/granville_phillips/trend.py` is the thin wrapper
   pattern to copy. Temperature is linear, so this one does not need the log
   axis, but read `pressure_scales` in that file to see how a driver asks for
   one. Generate a page from sample data and open it once, to check it shows
   what you meant. Session 2 found two real defects that way which its tests had
   not caught.

7. **Record what you did.** A dated entry in `DECISIONS.md`, and anything you
   could not verify added to `REVIEW.md`, item by item.

8. **Run `pytest -q` from the repository root**, commit, and push. Note that
   `projects/alarm_pareto` needs pandas and openpyxl to collect, so a fresh
   container needs `pip install -r projects/alarm_pareto/requirements.txt`
   before the root run works.

9. **Write the next session's prompt** as `sessions/session_04_edwards_pumps.md`,
   covering the Edwards nXDS, iXL and nEXT pumps, and hand that file over. Hand
   over the file itself rather than pasting the prompt into the chat as text.
   Update the table in `sessions/README.md` at the same time.

## Five decisions this device forces, which the core has not met yet

Do not guess at these. Decide them, and write the reasoning into `DECISIONS.md`.

1. **A binary protocol against a text-shaped base class.** Both existing drivers
   return text from `parse_reply` and turn it into a number in a separate step.
   A binary protocol has no text stage. Decide whether `parse_reply` returns
   bytes, a parsed structure, or a number, and whether the base class needs to
   change at all. It probably does not, because `parse_reply` returns whatever
   the driver wants. Check that before touching shared code, and if you do touch
   it, remember eight more drivers inherit whatever you do.

2. **A checksum has to be proved before it is trusted.** `core/device.py` says
   directly that a driver checks its checksum in `parse_reply`, and
   `tests/test_device.py` has the CTI checksum as a stand-in protocol, verified
   against three worked examples from the Brooks manuals. That is the standard
   to meet. **Find worked examples in the manual and test your checksum against
   them, byte for byte, in a test of their own.** A checksum implemented from a
   prose description and never checked against a real frame is the classic way
   this goes wrong, because it will happily agree with a mock that has the same
   mistake in it.

   If you cannot find a worked example, that is a finding and it belongs at the
   top of the `REVIEW.md` section for this driver.

3. **Hardware access exists for this one.** The chiller is the device somebody
   can actually put a cable on, which is why it is third in the order rather
   than fifth. That changes what is worth doing. Write down, in `PROTOCOL.md`,
   the exact first bench session: which port settings to set, which single
   command to send first, and what a good reply looks like byte for byte. Make
   it short enough that somebody standing at the machine will follow it.

   It also changes what "unverified" means here. For the first time an item in
   `REVIEW.md` might be checked within a week rather than never, so write the
   items so they can be checked one at a time.

4. **Neslab and ThermoFlex may not be one protocol.** The two existing drivers
   each cover several models with one class and a model setting, because the
   models turned out to share a protocol. Do not assume that here. Check whether
   the older Neslab units and the newer ThermoFlex units actually speak the same
   frames. If they do not, decide whether that is two classes or one class with
   two frame builders, and say why. Two genuinely different protocols in one
   class with a flag is how a driver becomes unreadable.

5. **A chiller has a setpoint, and reading one is not writing one.** These
   instruments almost certainly have a command to read the temperature setpoint
   and a command to change it, and they will look similar. Reading the setpoint
   is worth having, because a chiller drifting from its setpoint is exactly the
   thing a trend should catch. Writing it is a control action on process cooling
   water feeding live equipment.

   Get the two commands distinguished carefully from the manual, put the read on
   the allowed list, and put the write on the banned list with a reason. If the
   manual is not clear about which is which, allow neither and say so. This is
   the closest any driver has come so far to a command where a misreading of the
   manual becomes a machine action.

## Rules that do not bend

Read-only. Research first, and say what your sources were. Always send through
`Device.query`. One process owns the port. Log every raw frame. Add a package
only in the change that imports it. Nothing reaches the internet at runtime.
Short sentences, plain words, no em dashes, boring explicit code with comments,
written for a beginner in Python.

The full versions are in `CLAUDE.md`.
