# Notes for the second-round review

This project was built in a first pass. A second, critical pass is expected to
go over it on a different machine. This file is the handover. It says what was
actually checked, what was only assumed, and where to push hardest.

Nothing here is a defence of the code. It is a list of the places most likely to
be wrong, written by the person who wrote them, while they are still fresh.

## The Lakeshore driver was built without reading a Lake Shore manual

**Read this before trusting `devices/lakeshore/`. It is the largest single risk
in this project, ahead of the mock.**

The driver was written from `lakeshorecommsresearch.md`, a research file the
project owner supplied on 2026-09-02. That file is careful and it cites the
official manuals, Lake Shore's own Python driver, and forum threads, saying which
fact came from where. It is still not a manual. `lakeshore.com` and every mirror
found were refused by this machine's network policy, so no Lake Shore manual was
opened at any point.

Lake Shore's own Python driver was read directly, from
`github.com/lakeshorecryotronics/python-driver`, and used only as a cross-check.
Where it agrees with the research file, that is noted below. It has no worked
examples of its own.

So the whole driver rests on a secondary source. The first person to hold one of
these manuals should read `devices/lakeshore/PROTOCOL.md` against it. Until then,
everything in the next two lists is a claim, not a fact.

### Backed by a worked example in the research file

These are the strongest things here, and they are still second hand.

1. **The 218 frame.** `KRDG?0` followed by `0x0D 0x0A` returns eight comma
   separated signed readings followed by `0x0D 0x0A`. Traced to a PLC
   implementation talking to a real instrument.
2. **The 218 port settings.** 9600 baud, 7 data bits, odd parity, 1 stop bit, no
   flow control, half duplex. Traced to the 218 manual and to an NI forum thread
   that reports it working.
3. **The identity reply shape.** `LSCI,MODEL218S,<serial>,<firmware>`.

### Assumed, and worth checking first on a bench

1. **The space between a command and its input.** This driver sends `KRDG? A`.
   The only worked example in the research file, on a 218, has no space:
   `KRDG?0`. Both are said to work and the spaced form is the one the command
   reference uses. If an instrument goes quiet, try it without the space before
   suspecting anything else. It is a one character change in `build_frame`.

2. **The `RDGST?` bit weights.** 1 invalid reading, 16 temperature under range,
   32 temperature over range, 64 sensor units zero, 128 sensor units over range.
   These come from Lake Shore's Python driver, not from the research file, which
   only says a nonzero value flags an old reading or an out of range condition.
   The driver treats any nonzero value as bad, so the weights only affect the
   words in an error message, not the safety of a reading. Still wrong is wrong.

3. **What an unplugged sensor actually does.** The driver and the mock assume it
   answers `KRDG?` with a number and sets `RDGST?` to 128. That it answers with
   a number rather than staying silent is the important half and is well
   supported. That the status is specifically 128 is a guess. `STATUS_NOT_
   CONNECTED` in `mock.py` is the one place to change it.

4. **The 224 and 336 port settings.** 57600 baud, 7 data bits, odd parity, 1 stop
   bit. The research file and the vendor driver agree, which is the strongest
   agreement available here. Neither says whether 57600 is the only rate offered
   or what the instruments ship set to. If a 224 will not answer, the speed is
   the first thing to try.

5. **The 224 and 336 input names.** 224 as A, B, C1 to C5, D1 to D5. 336 as A to
   D. Nothing here has been seen against a physical instrument.

6. **The `336-3062` model,** where the 3062 option expands input D into D1 to D5.
   Entirely from the research file's note. No confirmation that the naming is
   what a fitted card actually reports.

7. **No batch read on the 224 or 336.** `KRDG? 0` is used on the 218 only,
   because that is where the worked example is. Lake Shore's own driver does use
   `KRDG? 0` on a 336, so the batch form very likely works there too. Turning it
   on would cut a 336 sweep from four queries to one plus statuses. It was left
   off because a wrong reply length silently pairs readings with the wrong
   inputs, and that is a bad failure to introduce on an unverified guess. The
   check is already written: `_read_all_at_once` refuses a reply with the wrong
   number of values.

8. **The 50 millisecond pacing.** From working implementations, not from a
   manual. It is `pace_s` on the driver and easy to change.

9. **Whether `INNAME?` returns the name bare or in quotes.** The mock returns it
   bare. Lake Shore's driver sends quotes when writing a name with `INNAME`,
   which hints the reply may carry them. If it does, a trend column will be
   called `"Cold head"` with the quotes in it. Harmless and ugly.

### What the tests do and do not prove

30 tests cover this driver and they all run against the mock. They prove the
driver frames what `PROTOCOL.md` says it frames, refuses what it says it
refuses, retries silence, does not retry a broken reply, and turns a flagged
sensor into a hole rather than a zero.

They cannot prove the frame is the one the instrument wants, because the mock
was written from the same research file as the driver. Both would be wrong
together. That is not a gap more tests of this kind can close.

### First bench visit, in order

1. Port settings. 7 data bits and odd parity, which no adapter defaults to.
2. `*IDN?`, and read what comes back before anything else.
3. One `KRDG?` on a known good input, with the audit log open.
4. Unplug a sensor deliberately and read `RDGST?`. That settles item 3 above.

## What was verified, and how

- **122 automated tests pass**, 100 of them for this project, 30 of those for
  the Lakeshore driver. Run `pytest -q projects/fab_drivers` from the repository
  root.
- **The Lakeshore driver never touches the transport directly.** Checked by
  grepping `devices/lakeshore/` for `exchange(` and `transport.`. The only match
  is the word in a docstring. Every command goes through `Device.query`, so the
  safety gate holds for this driver. Do the same grep on the next nine.
- **The trend page was generated and looked at**, not only asserted on. A six
  hour cooldown on a 336, four inputs, with a deliberate forty minute gap in one
  of them. The gap draws as a break in the line rather than a join, and the
  summary table counts 320 points for that column against 360 for the others.
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

11. **The trend page has only ever been viewed by its own tests.** They assert
    it fetches nothing external, that a gap breaks the line, and that a device
    name is escaped rather than injected. They do not assert it looks right. One
    sample page was generated and eyeballed during the build. It has not been
    opened in Edge on a bench machine, which is where it will actually be read.

12. **The trend page holds every reading inside the file.** A week of one minute
    polling is around ten thousand rows. Nobody has checked what that does to
    the file size or to how long the page takes to open. If it becomes a
    problem, the fix is to thin the data when building the page, and that
    changes what the chart means, so it is a decision rather than a tweak.

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

- **Nine of the ten drivers.** Only the Lakeshore one exists.
- **A service layer and a user interface.** Both are described in the plan. This
  pass covers the core only.
- **Control actions of any kind.** Version 1 reads. That is the whole scope.
