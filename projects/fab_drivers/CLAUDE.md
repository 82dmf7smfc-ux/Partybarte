# Working instructions for this project

Read this before writing any driver in `fab_drivers`. It is the standing brief
for a session that starts with no memory of the ones before it.

The decisions log is `DECISIONS.md`. The handover for the critical review is
`REVIEW.md`. This file is the how-to.

## The plan

Ten drivers, one per session, in this order. The order starts with the easiest
ASCII protocols so the template is proved on something simple, puts the chiller
third because hardware access already exists, and leaves SECS/GEM last because
it has the highest payoff and the highest complexity.

| # | Session order | Device | Protocol | Notes |
|---|---|---|---|---|
| 1 | 1st | Lakeshore 218 / 224 / 336 | SCPI style ASCII, RS-232 or Ethernet | Cryo stage and cold head temperatures. Easiest build. |
| 2 | 2nd | Granville-Phillips 275/375, 350/356 | ASCII, `#` address framing, RS-232/485 | Chamber and foreline pressure. Short free manuals. |
| 4 | 3rd | Thermo Neslab / ThermoFlex chillers | Binary framed, checksummed, RS-232 | Process cooling water. Not plain ASCII. Hardware access exists. |
| 5 | 4th | Edwards nXDS, iXL, nEXT | ASCII `?V` and `?S` query forms | Pump speed, power, temperature, hours. |
| 3 | 5th | MKS 937B / 946 | ASCII, `@` address, `;FF` terminator | Pressure, and flow on the 946. |
| 6 | 6th | Pfeiffer TC110 / TC400 | Pfeiffer Vacuum Protocol telegrams, RS-485 | Speed, drive current, bearing temperature. |
| 9 | 7th | Watlow EZ-Zone | Modbus RTU over RS-485, needs `pymodbus` | Heater zones. Published register maps. |
| 8 | 8th | Advanced Energy MDX, Pinnacle | AE Bus, binary, XOR checksum | Voltage, current, power, arc counts. |
| 7 | 9th | SRS RGA100 / 200 / 300 | ASCII at 28.8k | Gas composition. Scans into CSV. |
| 10 | 10th | SECS/GEM tool monitor | HSMS over TCP, needs `secsgem` | Its own multi-session project. See the warning below. |

After all ten, a critical review pass takes over and hardens them. This pass is
about getting the tools, the research and the functionality right. It is not
about being production hardened. Do not skip things on the grounds that the
reviewer will catch them, and do not gold-plate either.

## Rules that do not bend

1. **Research first. Never write a driver from memory of a protocol.** Find the
   official programming or protocol manual. Prefer free direct PDFs. idealvac.com
   hosts many vacuum manuals. Verify the command syntax against worked examples
   in the manual before writing code that sends anything.

   If the manual cannot be found, say so and stop. A driver blocked on a document
   is an honest outcome. Plausible looking command syntax that was never verified
   is worse than no driver, because it looks finished.

2. **Read-only. Version 1 reads values and does nothing else.** No setpoint
   writes, no control actions, no parameter changes. The `CommandPolicy` enforces
   this. Do not add a control command to an allowed list because it seemed handy.

3. **Always send through `Device.query`.** Calling `self.transport.exchange`
   directly goes around the safety gate. That is the one known hole in the
   design, it is recorded in `REVIEW.md`, and it is only a hole if a driver
   actually does it.

4. **One process owns the port.** Time out at one second. Retry twice. Then mark
   the reading stale. The base class already does this. Do not reimplement it.

5. **Log every raw frame.** The base class already does this too, as long as the
   transport is given an `AuditLog`.

6. **Add a package in the change that first imports it.** `pyserial` is pinned.
   `pymodbus` arrives with the Watlow driver, `secsgem` with SECS/GEM. Every
   package is an IT approval request, so nobody should be asked to approve a
   wheel that nothing imports.

7. **Nothing reaches the internet at runtime.** Talking to equipment over a
   serial port or a local socket is the job. Fetching anything from the web is
   not.

## What a driver session produces

Make a folder under `fab_drivers/devices/`, named after the equipment. Put four
things in it.

1. **`PROTOCOL.md`.** Written from the manual, before the code. The frame format,
   the checksum if there is one, the result or error codes, the serial settings,
   the commands used in version 1, and the commands banned outright with the
   reason. Name the manual and its part number, and say where it was found. This
   document is the durable artifact. The code is downstream of it.
2. **`driver.py`.** A class inheriting `core.device.Device`. It writes two
   methods, `build_frame(command, target=None)` and `parse_reply(raw)`. It builds
   its `CommandPolicy` with the read-only allowed list, the banned list with
   reasons, and the sub-unit addresses if the device has any.
3. **`mock.py`.** A responder for `MockSerial` that answers like the real device.
   Fake the failure cases too, not just a good reading: silence, a bad checksum,
   and whatever error codes the protocol defines. The failure cases are what the
   retry and staleness logic is tested against.
4. **Tests** under `tests/`, named `test_<device>.py`, running against the mock.
   They must pass with no hardware attached, because that is what CI runs.
5. **A trend page.** Every driver gets its own. Build it with
   `core.trend_page.write_trend_page`, saying which columns to plot and what to
   call the device. Do not write a page from scratch. Ten drivers each inventing
   one gives ten pages that look and behave differently, and nine of them get
   copied from whichever was written first, mistakes included. If the shared
   generator cannot do something a device genuinely needs, improve the generator
   so every driver gets it.

Then add a dated entry to `DECISIONS.md` saying what was decided and why,
especially anything the manual made you do that looks odd.

## How to write it

The core does the work that is the same for every device. A driver only says how
that vendor frames a message and how it unwraps a reply.

Commands and addresses are separate. A device that is really a box with several
things behind it, a terminal with twenty pumps or a controller with several
sensors, lists its commands once and its addresses once. Do not fold the address
into the command string. That was the first design and it did not scale.

```python
policy = CommandPolicy(
    "Example 100",
    allowed=["J", "K"],                       # read commands only
    banned={"g": "Locks other ports out, including the tool's own."},
    targets=range(0, 20),                     # or leave out if there are none
)
```

Match the house style. Short sentences. Plain words. No em dashes. Boring
explicit code with comments, written for a smart reader who is a beginner in
Python. A comment saying why is worth more than one saying what.

## Ending a session, and starting the next one

A session starts with no memory of the one before it. So the last act of every
session is to write the next one's starting prompt into `NEXT_SESSION.md`, and to
print that prompt in the chat as well so it can be copied straight into a new
session.

The prompt is not a reminder of what device comes next. It has to carry a session
that begins from nothing. It says where things stand, what to build, the order to
do it in, and the decisions that device forces which the core has not met yet.
That last part is the valuable one. It is written while the design is fresh, by
the session that just saw the gap.

The file lives in the repository rather than in a chat window because a prompt
that exists only in a chat log is one closed tab away from being lost.

## Before finishing a session

- `pytest -q projects/fab_drivers` passes, and so does `pytest -q` from the root.
- The new tests pass with no hardware.
- `PROTOCOL.md` names its source manual and part number.
- Nothing state-changing is on an allowed list.
- `DECISIONS.md` has a dated entry.
- The trend page is generated and opened once, to check it actually shows what
  you meant.
- Anything you could not verify is written down as unverified, in `REVIEW.md`,
  not left implied. The review pass depends on knowing what was checked and what
  was assumed.
- `NEXT_SESSION.md` has been rewritten for the session that follows, and the
  same prompt has been printed in the chat.
- The work is committed and pushed. A session that ends with work only on disk
  has produced nothing, because the next session is a different machine.

## The SECS/GEM warning, for session ten

Most tools accept only one host connection. Connecting a second one can take the
tool's own host offline. That driver needs either an unused additional port or a
tool that is not under host control. Research SEMI E5, E30 and E37 before writing
anything, and treat it as its own multi-session project rather than one more
driver.

## Physical safety, every session

Service and spare ports only. Never a port the tool controller is actively using.
Confirm electrical isolation with a USB isolator when tapping powered equipment.
The full list is in `README.md`, and it is worth rereading before a bench visit.
