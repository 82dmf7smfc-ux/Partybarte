# Notes for the second-round review

This project was built in a first pass. A second, critical pass is expected to
go over it on a different machine. This file is the handover. It says what was
actually checked, what was only assumed, and where to push hardest.

Nothing here is a defence of the code. It is a list of the places most likely to
be wrong, written by the person who wrote them, while they are still fresh.

## What was verified, and how

- **78 automated tests pass**, 56 of them for this project. Run
  `pytest -q projects/fab_drivers` from the repository root.
- **The core imports and runs with pyserial absent.** That is the state of the
  GitHub runner. `open_serial_port` gives a clear message instead of a stack
  trace.
- **The CTI checksum algorithm was checked** against the three worked examples in
  the Brooks manuals: body `P01@` gives `b`, `AP A2.01` gives `a`, `@` gives `1`.
  It appears in `tests/test_device.py` only, as a realistic stand-in protocol. It
  is not a shipped driver.

## What was not verified

**No byte in this project has ever reached real hardware.** Everything is tested
against `MockSerial`, which is a model of how pyserial behaves, written from
knowledge of pyserial rather than from measurement. If the model is wrong, the
tests pass and the bench fails. That is the single largest risk here, and it is
not reducible by more testing of the same kind. It needs a real port.

Specific assumptions inside the mock, each worth checking against a real device:

1. `read_until` returns whatever arrived so far when the timeout expires, rather
   than raising or blocking.
2. A reply split across two reads is still reassembled by one `read_until` call,
   because it keeps reading until the terminator or the timeout.
3. `reset_input_buffer` discards the operating system's buffer, not just a
   Python-side one.
4. A device that is not there produces silence, not an error.

## The hole in the safety gate

This is the first thing to attack.

Read-only is enforced in `CommandPolicy`, and `Device.query` calls it before
building a frame. That is airtight **as long as a driver goes through
`Device.query`**. A driver that calls `self.transport.exchange(...)` directly
bypasses the policy completely and can write any bytes it likes to the port.

Nothing in the code currently prevents that. It was left this way because the
alternatives were worse: a transport that refuses to talk to anything but a
Device makes the layer hard to test, and a token passed between the two adds
machinery a beginner has to understand before writing a driver.

So the review question is not whether the gate works. It does. It is whether
every driver actually goes through it. Grep each new driver for `exchange(` and
`transport.` before trusting it.

## Known weaknesses, in the order I would look at them

1. **A sweep has no time budget.** One failed reading costs up to 3.4 seconds:
   one second of timeout, then two retries with a pause. Twenty pumps that are
   all quiet cost about 68 seconds, which quietly overruns a 30 second polling
   interval. The poller does not notice or complain. It just takes longer. Decide
   whether a sweep should have a deadline and give up on the rest.

2. **Timestamps are naive local time.** No timezone, no daylight saving handling.
   When the clocks go back, an hour repeats in the CSV, so two different readings
   carry the same timestamp and a sorted trend is wrong. When they go forward, an
   hour is missing. This was kept deliberately, because the reference CTI logger
   writes the same naive local format and its files feed an existing Excel
   cooldown model. Changing it breaks that compatibility. Changing it is probably
   still right. That is a call for someone who knows what reads these files.

3. **`Poller.sweep` catches bare `Exception`.** A genuine programming mistake, a
   misspelled attribute say, is recorded as a stale reading rather than crashing.
   That is deliberate, because one broken pump must not stop the other nineteen.
   It also means a bug can hide as a hardware fault for a long time. The error
   text does land in the reading, but nobody reads those until something looks
   wrong.

4. **The one-owner-per-port check only sees this process.** `_open_ports` in
   `transport.py` cannot detect another program holding the port, a stray PuTTY
   window for example. On Windows the operating system refuses a second open
   anyway, so the real protection is there and this is a second layer. That claim
   about Windows was not tested and should be.

5. **The audit log opens and closes the file for every single line.** That is on
   purpose, so a program killed mid-exchange still has everything up to that
   moment. It has never been measured. Twenty pumps at two lines each every ten
   seconds is around 240 file opens a minute, forever, on a bench machine.

6. **Nothing ever deletes an audit or history file.** A device logging daily
   leaves 365 files a year, per device. Deliberate, since throwing away evidence
   is worse, but somebody has to own an archive policy before this runs for a
   year.

7. **`retry_pause_s` defaults to 0.2 seconds.** That number came from judgement,
   not from any manual. If a specific device documents how long it needs after a
   dropped frame, use that instead.

8. **The polling floor silently raises a too-fast interval** to ten seconds
   rather than refusing it. A caller asking for one second gets ten and is not
   told. Arguably it should complain.

9. **Numbers are written to CSV with whatever `str()` produces.** No fixed
   decimal places. Check that suits whatever reads these files.

10. **The transport lock is not tested under real threads.** `SerialTransport`
    holds a lock so a future threaded poller cannot interleave two exchanges. No
    test exercises it concurrently, because the poller is currently a plain loop.

## Design choices worth arguing with

These are not defects. They are decisions that went one way and could reasonably
go the other. `DECISIONS.md` has the reasoning for each.

- The command allowed list and the sub-unit address are checked separately, so a
  terminal with twenty pumps needs eight allowed entries rather than one hundred
  and sixty. This is the second version of that design. The first folded the
  address into the command and would not have scaled.
- Silence is retried. A reply that fails its checksum is not.
- A stale reading keeps its last good value on screen, with its age, but writes
  an empty cell to the CSV. The two rules point in opposite directions on
  purpose.
- The poller is a plain loop, not a thread.
- The transport is handed an already open port rather than opening one itself.

## What is deliberately absent

- **Any device driver.** The core was built first so the first real driver lands
  in a tested template. `fab_drivers/devices/` is empty.
- **A service layer and a user interface.** Both are described in the plan. This
  pass covers the core only.
- **Control actions of any kind.** Version 1 reads. That is the whole scope.
