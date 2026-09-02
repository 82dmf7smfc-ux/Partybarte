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

## The Granville-Phillips driver was built without a Granville-Phillips manual

**Read this before trusting `devices/granville_phillips/`. It is the same class
of risk as the Lakeshore driver, and in one respect it is worse: that driver had
a research file written for it, and this one did not.**

Every site hosting one of these manuals was refused by this machine's network
egress policy, with a 403 on the CONNECT: `mks.com`, `idealvac.com`,
`lesker.com`, `manualslib.com`, and the mirrors at `bl831.als.lbl.gov`,
`mmrc.caltech.edu`, `nanophys.kth.se` and `kmtnet.kasi.re.kr`. `github.com` was
reachable and package registries were reachable. Nothing else was.
`manuals/FETCH_PROMPT_GRANVILLE_PHILLIPS.md` is the request to get the documents
from a machine that can reach them.

Two sources contributed, and they are not equal.

**Read directly:** `epics-modules/vac`, the APS BCDA synApps vacuum module,
cloned from GitHub and read on disk. It carries EPICS device support for the
Series 350 in `vacApp/src/devVacSen.c` and `devVacSen.h`. Working code aimed at
real controllers, with no worked examples and no statement of which firmware it
applies to. It covers the 350 only.

**Relayed:** manual text returned by the web search tool, which can read PDFs
this machine cannot download. It produced specific statements, including one
worked exchange, attributed to named manuals. This is a summariser's reading of
a manual rather than the manual. There were no page images, no continuous text,
and no way to read a table whole or check a statement against its surroundings.

### Backed by a worked example, or by code read directly

1. **The frame and the one worked exchange.** `#01RD<CR>` returns
   `*01 9.34E-06<CR>`. Start character `#`, two ASCII characters holding the hex
   address, the command, terminator `0x0D`. Relayed from the Series 354 manual.
   `epics-modules/vac` independently builds `#` plus `%02X` and sets both
   end-of-string characters to a bare `\r`, which is the strongest agreement
   available here.
2. **The error reply.** `?01 SYNTX_ER<CR>` when the host sends a string the
   module cannot parse. Relayed from the 354 and 275 manuals, and
   `epics-modules/vac` treats a leading `?` as an error too.
3. **The 350 gauge selectors.** `RD 1`, `RD 2` for the ion gauges and `RD A`,
   `RD B` for the Convectron gauges, with `DGS` and `PC S` alongside. Read
   directly from `devVacSen.h`.
4. **The 350 control commands, which are why they are banned.** `F1 0`, `F1 1`,
   `F2 0`, `F2 1`, `DG0 OFF`, `DG1 ON`. Read directly from `devVacSen.h` as its
   control command table.
5. **The 350 serial settings.** 9600 baud, 8 data bits, no parity, one stop bit.
   Read directly from `docs/vacuum-gauges.md`.
6. **`9.99E+09` means no reading.** Relayed from the 354 manual as the value
   returned for three seconds after power up, and from the 343 manual as five
   seconds. `epics-modules/vac` uses 9.9e+9 as its own no-value marker, arrived
   at independently.
7. **The 375 serial settings.** 9600 baud, 8 data bits, one stop bit, no parity,
   no handshake, ASCII. Relayed from the 375 manual and brochure.

### Assumed, and worth checking first on a bench

1. **How to select a channel on a 375.** Nothing found says. The driver sends a
   bare `RD` and reads whatever answers, and `MODELS["375"].sourced` is False so
   `describe_sources()` says so out loud. **Which gauge that reading comes from
   is unknown.** This is the single biggest hole in this driver. It is ten
   minutes of work for anyone holding the manual.
2. **The 275 and 356 serial settings.** Both manuals have a baud rate section
   that nothing here could read. The driver defaults them to 9600 8-N-1 because
   that is what the 350 and 375 use and these are one product family. If a 275
   will not answer, this is the first thing to try.
3. **The address ranges.** Modules are allowed 0 to 15 because the address
   switch is documented, relayed, as running 0 to 15, that is `00` to `0F` hex.
   Controllers are allowed 0 to 31 because `epics-modules/vac` allows 1 to 31
   for the GP350. Neither range was read from a manual directly, and the two
   were arrived at from different sources.
4. **Whether a broadcast address exists.** None was found in any source. The
   driver has none and allows none. If a later reader finds one, leave it
   banned: on a shared pair a broadcast makes every module answer at once and
   the replies collide into something that still looks like a pressure.
5. **Four of the banned mnemonics.** `SZ`, `SS`, `SE0` and the `SU` stem of
   `SUT`, `SUM`, `SUP` are assumed. The relayed manual names the functions in
   prose, "set span", "set zero", and says the last character of the units
   command selects M, P or T, but the mnemonics themselves were never seen
   written out. Banning a command that turns out not to exist costs nothing,
   because it can never be sent. The `PROTOCOL.md` table has a column saying
   which is which so this is not mistaken for verified.
6. **That the reply always carries the address.** The driver requires it and
   raises if it does not match. `epics-modules/vac` talks to a GP350 on RS-232
   with address 0, where it sends a bare `#` with no address digits and gets
   back `*` and a space and nothing between. So an addressless form exists on at
   least one model. If an instrument answers and this driver rejects every reply
   with an address complaint, that is what is happening, and `build_frame` and
   `parse_reply` are the two places to change.
7. **The 13 character response width.** Relayed from the 354 and 275 manuals as
   "all data field responses will contain 13 characters". `*01 9.34E-06` is 12,
   so either the count includes the terminator or it counts something not seen
   here. The driver does not depend on a fixed width, so this is a curiosity
   rather than a risk, but it means one relayed statement is not fully
   understood.
8. **The 50 millisecond pacing.** Copied from the Lakeshore driver. No source
   here gives a required gap between messages.
9. **That a gauge which is off reports `9.99E+09` rather than an error.** The
   power-up behaviour is sourced. That a gauge switched off behaves the same way
   is an inference from how the family is described, and it is what `mock.py`
   models. If a real module answers `?01 SYNTX_ER` or stays silent instead, the
   driver already handles both, but the mock is then wrong and the tests are
   testing the wrong thing.

### The finding about units, which is not an assumption

**There is no read-units query on these instruments, as far as any source here
goes.** This was searched for specifically, not skipped. Set-unit commands exist
and are banned. A query that reports which unit is configured did not appear in
any manual text relayed, in `epics-modules/vac`, or in any other source.

The consequence is that a trend file's unit is whatever the person who
configured the driver believed, and nothing checks it. `units` is a required
argument with no default so that the belief is at least written down and ends up
in the column name. If somebody changes the units on the front panel and not in
the code, the file will be wrong and silent.

**This is the first thing to look for in the manual when it arrives.** If a read
command exists, read it at start up, put it in the column name, and compare it
with what the caller said on every sweep.

### There is also no identity query

Nothing found describes a command that asks the instrument what it is. The
Lakeshore driver checks `*IDN?` against its model setting. This one cannot. A
275 driver pointed at a 350 will send `#01RD`, and the 350 will most likely
answer something, and nothing anywhere will say the model setting is wrong. Look
for an identity command in the manual too.

### What the tests do and do not prove

35 tests cover this driver and they all run against the mock. They prove it
frames what `PROTOCOL.md` says it frames, refuses what it says it refuses,
retries silence, does not retry a broken reply, rejects a reply from the wrong
address, and turns a gauge that is off into a hole rather than a 9.99e9 torr
reading.

They cannot prove the frame is the one the instrument wants, because the mock
was written from the same sources as the driver. Both would be wrong together.
That is not a gap more tests of this kind can close.

### First bench visit, in order

1. `#01RD` on a module known to be reading, with the audit log open. Check the
   reply shape against `parse_reply`, especially whether the address comes back.
2. The address switch setting against what comes back in the reply.
3. Turn a gauge off and read it. That settles item 9 above and the mock with it.
4. On a 375, work out how a channel is selected. That is item 1 and the largest
   hole here.
5. Find out whether a read-units command exists. That is the finding above.

## The Thermo chiller driver had two manuals, and one family inside it did not

**This is the first driver in this project written with a manufacturer's manual
open.** Two Thermo NESLAB manuals were read directly, in full, from PDFs that
came with the public repository `github.com/octopode/bathtime`. So most of this
driver is not an assumption, and this section is much shorter than the two above
it for that reason.

What the manuals cover is the NESLAB RTE line. What they do not cover is the
ThermoFlex line, and **everything ThermoFlex specific in this driver rests on
one open source library and no manual**. That is the finding, and it is the
first thing to check.

Hardware access exists for this device. Unlike every item in the two sections
above, these can be settled this week rather than never, so each one is written
to be checked on its own.

### The one thing to check before trusting a ThermoFlex reading

1. **The ThermoFlex command bytes are from code, not from a manual.** `read_flow`
   is `10`, `read_supply_pressure` is `28`, `read_suction_pressure` is `29`, and
   the four flow and pressure alarm limits are `30`, `50`, `48` and `68`. All
   seven come from `Python/DvG_dev_ThermoFlex_chiller__fun_RS232.py` in
   `Dennis-van-Gils/MHT_Tunnel`, read directly, which is working code written
   against a real ThermoFlex in 2018.

   It is not a manual. It carries no worked examples and does not say which
   ThermoFlex model or firmware it was written against.

   **How to check it in one command.** Send `read_supply_pressure` and compare
   the number against the front panel. If the pressure on the screen and the
   number in the log agree, the byte is right. Repeat for flow. Ten minutes.

2. **The ThermoFlex fault bit table is from the same code and nothing else.**
   `THERMOFLEX_STATUS_BITS` in `driver.py`. Every name and every bit position in
   it. The RTE table next to it is from the manual's Table 2 and is not in
   doubt.

   This is the item where being wrong looks most like working. A driver that
   puts "low flow fault" in the wrong bit still returns a dictionary of
   plausible names and still trends. Nothing announces it.

   **How to check it.** Cause one fault you can cause safely, most easily a low
   flow or low level warning by closing a valve or dropping the reservoir, and
   read the raw status bytes out of the audit log. Check which bit moved against
   the table. One fault checked is worth more than the whole table assumed.

   The partial comfort is that `read_faults()` counts every bit whose name
   contains "fault", so "is anything wrong at all" comes out right even if an
   individual name is in the wrong place. Only the naming is at risk.

3. **The ThermoFlex serial appendix was never read.** Its manual's Appendix C is
   titled "NC Serial Communications Protocol", the same as the NESLAB one, and
   relayed search results confirmed the master-slave model and the default port
   settings of 9600 8-N-1 with an RS-485 address defaulting to 1. The command
   table and the status table could not be retrieved.
   `manuals/FETCH_PROMPT_THERMO_CHILLER.md` asks for this one document. It would
   close items 1 and 2 together.

### Checked against the manuals, and not in doubt

These are here so a reviewer knows which parts do not need re-checking.

- The frame layout, the checksum rule, and the two lead characters. Quoted from
  both manuals in `PROTOCOL.md`.
- **Nineteen complete frames with their checksums**, taken out of the two
  manuals and made into tests. Eighteen agree with this code exactly. See below
  for the one that does not.
- The command bytes `00`, `09`, `20`, `21`, `40`, `60`, `70`, and the write
  bytes `C0`, `E0`, `F0` to `F6` and `81` that are banned. All from Table 1 in
  one or both manuals.
- The qualifier byte, and that the value is a **signed** 16 bit integer. The
  manual's own worked example of -10.5 degrees as `FF 97` settles it.
- The RTE fault bit table, from Table 2.
- The port settings, the one second timeout, and the RS-485 turnaround delay.

### Small things that are unverified, each checkable on its own

4. **One printed checksum in the Digital Plus manual disagrees with the manual's
   own rule.** Table 1 prints Read Cool Proportional Band as
   `CA 00 01 74 00 84`. Summing gives `75`, and `75 XOR FF` is `8A`. The
   ThermoFlex library also sends `8A`. This driver computes every checksum, so
   it sends `8A` and never copies a printed one.

   Almost certainly a misprint, and possibly an artefact of extracting text from
   the PDF rather than an error in the paper manual. It affects nothing this
   driver sends, because that command is a PID read and is not on any allowed
   list. **How to check it:** look at a paper copy of the table, or send the
   command once and see whether the chiller answers or returns a bad checksum
   error.

5. **The unit names for indexes 2 to 11 are from the ThermoFlex library only.**
   The manual's table names only index 0, no unit, and index 1, degrees C. The
   nine others, including bar, PSI and litres per minute, come from the library.
   The nibble split itself is safe, because it reproduces all four values the
   manual's table lists.

   **How to check it:** read a pressure with the chiller set to bar, then set to
   PSI at the panel, and see which index comes back each time.

6. **Error code `02` is not in either manual.** The manuals list `01` for a bad
   command and `03` for a bad checksum. The ThermoFlex library also handles `02`
   as bad data. The driver reports it and says where the code came from.

7. **The protocol version bytes nobody has seen.** `read_acknowledge` returns
   two version bytes and no source here says what a real chiller reports. The
   ThermoFlex library expects `00 00` or `00 01`. The driver returns them raw
   rather than checking them. **How to check it:** send the command and write
   the bytes down. It is step 4 of the bench session in `PROTOCOL.md`.

8. **The display text command `07` is deliberately not implemented.** The
   ThermoFlex library reads the front panel text with it. It is genuinely useful
   and it is in no manual read here, so it is not on any allowed list. Add it
   once somebody confirms it.

9. **The pacing between commands, 0.05 seconds, is a judgement and not sourced.**
   The same figure as the two earlier drivers. Nothing in either manual gives a
   required gap. The one second timeout is sourced, from both manuals.

10. **The two manuals disagree about the cable.** The RTE 110 manual describes a
    crossover, so a null modem. The Digital Plus manual asks for a straight
    male to female extension. Both are quoted in `PROTOCOL.md` and the bench
    session says to try one then the other.

11. **RS-485 has never been driven by this project.** The lead character, the
    address range and the address checking are implemented and tested against
    the mock. No real RS-485 pair has ever been touched. The 5 millisecond
    turnaround the manual specifies is not managed by this driver, which needs
    an adapter that switches direction itself.

### The core change this driver forced

12. **`SerialTransport` grew a `reply_size` hook and `MockSerial` grew
    `read(n)`.** Eight more drivers inherit this. The terminator path is
    unchanged and a test asserts that, and all 226 other tests passed before and
    after. What has never run against real hardware is the sized-read path
    itself, and this driver is the first user of it. If a frame ever comes back
    one byte short or one byte long on a bench, that code is where to look
    first.

13. **The trend generator grew an `overlays` argument.** Two lines on one pair
    of axes, for a reading and its setpoint. Also inherited by every later
    driver. A page with no overlays renders exactly as before, and a test
    asserts that.

### What the tests do and do not prove

68 tests cover this driver and 8 more cover the two core changes it forced. They
all run against the mock.

**What is different here, and it matters.** In the two drivers above, the mock
was written from the same sources as the driver, so both would be wrong
together, and no number of tests of that kind could close the gap. Here, the
nineteen checksum tests are checked against the manufacturer's own printed
bytes, and the mock computes its checksums with deliberately separate code. So
the framing and the checksum are proved against something outside this project.
That is a genuinely stronger position than either earlier driver is in.

What the tests still cannot prove is that the ThermoFlex command bytes address
the registers their names say, because the mock answers whatever byte the driver
asks for. Only the bench settles that, and items 1 and 2 above say how.

### First bench visit, in order

The full step by step is in `PROTOCOL.md` and is written for somebody standing
at the machine. In review terms the order is:

1. `read_acknowledge`, and write down the exact reply bytes. Settles item 7.
2. `read_internal_temperature`, and check the number and the qualifier byte
   against the front panel. Confirms the framing, the checksum and the qualifier
   in one command.
3. On a ThermoFlex, `read_supply_pressure` and `read_flow` against the panel.
   Settles item 1.
4. Cause one safe fault and read the raw status bytes. Settles item 2, which is
   the one where being wrong looks like working.
5. Check the units index by switching the panel between bar and PSI. Settles
   item 5.

## What was verified, and how

- **227 automated tests pass** for this project. 30 of them are the Lakeshore
  driver, 35 the Granville-Phillips driver, 67 the Thermo chiller driver, and
  the rest the core. Run `pytest -q projects/fab_drivers` from the repository
  root.
- **No driver touches the transport directly.** Checked by grepping
  `devices/lakeshore/`, `devices/granville_phillips/` and
  `devices/thermo_chiller/` for `exchange(` and `transport.`. Every command goes
  through `Device.query`, so the safety gate holds for all three. Do the same
  grep on the next seven.

  The only matches in any of the three are the word transport in a docstring.

  One thing the grep does not catch, so it is written here instead.
  `build_transport()` in the chiller driver constructs a `SerialTransport` with
  the `reply_size` hook this protocol needs. It builds a transport, it does not
  send through one, and every command still goes through `Device.query`.
- **The Lakeshore trend page was generated and looked at**, not only asserted
  on. A six hour cooldown on a 336, four inputs, with a deliberate forty minute
  gap in one of them. The gap draws as a break in the line rather than a join,
  and the summary table counts 320 points for that column against 360 for the
  others.
- **The Granville-Phillips trend page was generated and rendered in a browser,**
  not only asserted on. A six hour pumpdown on a 350, four gauges, from 760 torr
  to 1.7e-4 torr on the chamber Convectron and down to 1.5e-6 torr on the ion
  gauge, with a deliberate forty minute gap in the Convectron column and one
  gauge switched off throughout.

  It was opened in Chromium and looked at, and looking at it found two things
  the tests had not. The decade labels were thinned unevenly, so an eight decade
  axis carried labels at 1E+03 and 1E+02 next to each other and then nothing for
  two decades. And a column with no readings at all still printed "Log scale.
  One gridline per decade." underneath the words "No readings in this window",
  which is noise. Both are fixed. This is the argument for generating the page
  and opening it rather than trusting the assertions.
- **The Thermo chiller checksum was checked against nineteen frames printed in
  two Thermo NESLAB manuals**, read directly from the PDFs. Eighteen agree byte
  for byte. The nineteenth, Read Cool Proportional Band, is printed as `84`
  where the manual's own rule gives `8A`, and one independent implementation
  also sends `8A`. Every one of the nineteen is a parametrised test. The mock
  computes its checksums with deliberately separate code, so the manual's bytes
  are what decides, not agreement between two files in this repository.

  **This is the strongest verification in the project so far**, and it is the
  standard `tests/test_device.py` set with the CTI checksum. It is worth being
  clear about what it does and does not cover: it proves the framing and the
  checksum, not that a ThermoFlex command byte reads the register its name says.

- **The Thermo chiller trend page was generated and rendered in a browser,** not
  only asserted on. Three days of a ThermoFlex at an 18 degree setpoint, with
  the bath drifting five degrees up over the last day as the flow falls away,
  and a deliberate two hour gap in every column.

  Opening it found one real thing the tests had not. The setpoint was on its own
  chart with its own axis, so a flat setpoint filled its chart exactly as much
  as a temperature that had drifted five degrees, and the divergence, which is
  the only thing that page is for, was not visible anywhere. The shared
  generator grew an `overlays` argument as a result and the two now share one
  pair of axes. That is the second time in three sessions that opening the page
  found something the assertions did not.

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
