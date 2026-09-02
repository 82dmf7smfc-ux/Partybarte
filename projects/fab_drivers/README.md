# Fab equipment driver library

Small, read-only monitoring tools for semiconductor fab equipment. Each driver
reads values from one kind of box, writes every raw frame to an audit log, and
trends the readings into daily CSV files.

This is one project inside the Partybarte repository. The repository read me at
the root explains the shared setup.

## Safety, read this before connecting anything

These tools attach to production equipment. Get these four things right and the
worst case is that you read nothing. Get them wrong and you can interfere with a
running tool.

1. **Service and spare ports only.** Never connect to a port the tool controller
   is actively using. On the CTI On-Board terminal that is the rear Host port.
   Use the front Service port or the rear AUX port.
2. **Confirm electrical isolation.** Use a USB isolator when tapping powered
   equipment. The laptop and the tool do not share a ground you can count on.
3. **Read-only means read-only.** Version 1 of every driver here reads values
   and nothing else. No setpoint writes. No control actions. The code enforces
   this, see below.
4. **Stop if another port holds a lockout.** If a device reports that another
   serial port has locked it out, stop polling and say so on screen. Do not sit
   in a retry loop against a device the tool software is talking to.

## How read-only is enforced

Not by remembering. Every driver declares the exact list of commands it may
send. Anything not on that list is refused before the frame is even built, so a
banned command never becomes bytes on a wire. Commands known to be dangerous are
listed separately with the reason, so the next person reads why and not just
that it failed.

A command and a sub-unit address are checked separately. A cryopump terminal
with twenty pumps and eight read commands needs eight allowed entries, not one
hundred and sixty. An allowed list that has to be maintained by hand for every
address would stop being maintained, and a safety gate nobody maintains is not
one.

That means adding a command is a deliberate act. If a command only reads a
value, add it to the driver's allowed list and record the decision in
`DECISIONS.md`. If it changes what the machine is doing, it does not belong in
this version.

## What is here now

The shared core, and no device drivers yet. The core was built first so that the
first real driver drops into a tested template instead of inventing one.

| File | Job |
|---|---|
| `fab_drivers/core/policy.py` | Decide which commands may be sent. The safety gate. |
| `fab_drivers/core/audit.py` | Write every raw frame to a dated log file. |
| `fab_drivers/core/history.py` | Write readings to daily CSV files for trending. |
| `fab_drivers/core/mock_serial.py` | A fake serial port, so you can work with no hardware. |
| `fab_drivers/core/transport.py` | Own the one real port. One exchange at a time. |
| `fab_drivers/core/device.py` | The base class a driver builds on. Retries and staleness. |
| `fab_drivers/core/poller.py` | Read a set of values on a gentle repeating loop. |
| `fab_drivers/devices/` | One folder per piece of equipment. Empty for now. |

## The standards every driver follows

- **Research first.** Find the official protocol or programming manual. Verify
  the command syntax against worked examples before writing any code. Do not
  write a driver from memory of a protocol. If the manual cannot be found, the
  driver is blocked on the document, and that is the honest answer.
- **Read-only version 1.** Setpoint writes and control actions are excluded
  until someone asks for them explicitly.
- **Python and pyserial.** Standard library everywhere else. `pymodbus` and
  `secsgem` come later, for the two drivers that need them.
- **One process owns the port.** Poll gently. Time out at one second. Retry
  twice. Then mark the reading stale rather than pretending.
- **Log every raw frame with timestamps.** When something looks wrong, the first
  question is always what we actually sent and what came back.
- **Each driver ships four things.** A `PROTOCOL.md` written from the manual, a
  driver module, a mock device class, and an entry in `DECISIONS.md`.

## Writing a new driver

Make a folder under `fab_drivers/devices/`. Put four things in it.

1. `PROTOCOL.md`. The frame format, the checksum if there is one, the result
   codes, the commands used in version 1, and the commands banned outright.
   Write it from the manual, and name the manual and its part number.
2. `driver.py`. A class that inherits from `core.device.Device` and writes two
   methods, `build_frame` and `parse_reply`. Build its `CommandPolicy` here, with
   the read-only command list and the banned list with reasons. Always send
   through `self.query`. Calling `self.transport.exchange` directly goes around
   the safety gate, and then nothing is stopping a control command.
3. `mock.py`. A responder function for `MockSerial` that answers like the real
   device, including the failure cases. Silence and a bad checksum are as
   important to fake as a good reading.
4. Tests under `tests/`, using the mock. They must pass with no hardware
   attached, because that is what runs on GitHub.

## Running the tests

From the repository root, this runs every project's tests:

```
.venv\Scripts\python.exe -m pytest -q
```

To run only this project's tests:

```
.venv\Scripts\python.exe -m pytest -q projects\fab_drivers
```

Every test here runs against the mock serial port. None of them need hardware.

## Before you review this

`REVIEW.md` is the handover for a critical read of this project. It says what was
actually verified, what was only assumed, and the known weak points, including
the one place the safety gate can be bypassed. Read it before trusting anything
here. `DECISIONS.md` has the reasoning behind each design choice.

Nothing in this project has ever talked to real hardware. Every test runs against
a mock serial port. That is the largest open risk and no amount of further
testing of the same kind reduces it.

## Rolling a driver out

Recommended phases, not gates. The warnings say what you risk by skipping ahead.

| Phase | What you do | Risk if you skip it |
|---|---|---|
| 0. Bench | Run against the mock. Prove the poller, the audit log, and the CSV export all work with nothing attached. | You debug the software and the wiring at the same time, on a tool. |
| 1. Listen only | Plug into the service port. Read the identity and the device list, nothing else. Confirm what you see matches the physical hardware. | You chase ghosts from a wrong address later. |
| 2. Read-only monitoring | Turn on the full read-only set. Log for a full day. Confirm the tool software reports no comm errors. | You find a port conflict during production instead of on a quiet shift. |
| 3. Share it | Pin the CSV columns and audit fields, then hand it to the team. | Format churn after people build habits around it. |
