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

1. **Research first. Never write a driver from memory of a protocol.** Verify
   the command syntax against worked examples in the manufacturer's own manual
   before writing code that sends anything.

   **Research the web directly.** Search for the manual, download it, read it.
   The owner may also hand over a PDF or a research file, and that counts as a
   source too. If the network refuses a download, say so and use what you can
   reach.

   Whatever the source turns out to be, name it in `PROTOCOL.md` and say how
   much weight it carries. A manual read directly is the strongest. A research
   file compiled by someone else is weaker, and anything in it that no manual
   confirmed goes in `REVIEW.md` as unverified. Never write from memory of a
   protocol alone.

   A stage blocked on a document is an honest outcome. Plausible looking command
   syntax that was never verified is worse than no driver, because it looks
   finished and nobody goes back to it.

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

## When you need a document you do not have

This applies to any stage of any project here, and to any external document: a
programming manual, a register map, a protocol specification, a standard, a
vendor application note.

1. **Look in `manuals/` first.** The owner may already have put it there.
   `manuals/` has one folder per manufacturer and a `MANIFEST.md` saying what
   arrived and from where.

2. **Otherwise go and get it.** Search for it, download it, read it. Prefer the
   manufacturer's own site, then a university or national lab mirror.

3. **If the network refuses, say so and write a fetch prompt.**
   `manuals/README.md` has the shape one takes. Hand it over as a file. The
   owner can run it somewhere with better access.

4. **Record what the source actually was.** This is the part that matters.
   `PROTOCOL.md` names it. Anything taken from a weaker source than a manual, or
   from no source at all, goes in `REVIEW.md` as unverified, item by item. The
   next reader has to be able to tell a checked fact from a plausible one.

A search snippet is a lead, not a worked example. Chase it to the document it
came from where you can, and where you cannot, label what rests on it.

A vendor's own source code is a useful cross-check and is not a manual. Several
of these manufacturers publish drivers on GitHub. Read them, and note where they
disagree with the manual. On its own that code carries no worked examples and
does not say which models or firmware revisions its choices apply to, so
anything resting only on it is unverified.

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
session is to write the next one's starting prompt as a file in `sessions/`,
named `session_<number>_<device>.md`, and to hand that file over. Hand over the
file itself. Do not print the prompt into the chat as text. It is something to be
opened and used, not read in a transcript.

The file holds the prompt and nothing else, so it can go straight to a new
session with nothing to trim.

The prompt is not a reminder of what device comes next. It has to carry a session
that begins from nothing. It says where things stand, what to build, the order to
do it in, and the decisions that device forces which the core has not met yet.
That last part is the valuable one. It is written while the design is fresh, by
the session that just saw the gap.

These live in the repository rather than in a chat window because a prompt that
exists only in a chat log is one closed tab away from being lost. Update the
table in `sessions/README.md` at the same time, so it stays obvious which session
runs next.

## Before finishing a session

- `pytest -q projects/fab_drivers` passes, and so does `pytest -q` from the root.
- The new tests pass with no hardware.
- `PROTOCOL.md` names every source it was written from, and says how strong each
  one is.
- Anything not confirmed by a manual is listed in `REVIEW.md` as unverified.
- Nothing state-changing is on an allowed list.
- `DECISIONS.md` has a dated entry.
- The trend page is generated and opened once, to check it actually shows what
  you meant.
- Anything you could not verify is written down as unverified, in `REVIEW.md`,
  not left implied. The review pass depends on knowing what was checked and what
  was assumed.
- The next session's prompt has been written as a file in `sessions/` and handed
  over as a file, not pasted into the chat as text. The table in
  `sessions/README.md` is up to date.
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
