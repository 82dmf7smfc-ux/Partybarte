# Granville-Phillips gauge modules and controllers

The protocol notes this driver was written from. Read this before changing
`driver.py`.

Covered here: the Series 275 Mini-Convectron module, the Series 375 Convectron
controller, the Series 350 ion gauge controller, and the Series 356 Micro-Ion
Plus module. They read chamber and foreline pressure.

## Sources, and how much each one is worth

Read this section before trusting anything below it.

**No Granville-Phillips manual was opened on this machine.** Every manufacturer
and distributor site that hosts one was refused by this machine's network egress
policy: `mks.com`, `idealvac.com`, `lesker.com`, `manualslib.com`, and the
university and national laboratory mirrors at `bl831.als.lbl.gov`,
`mmrc.caltech.edu` and `nanophys.kth.se` were all blocked at the proxy with a
403 on the CONNECT. `manuals/FETCH_PROMPT_GRANVILLE_PHILLIPS.md` is the request
to get them from a machine that can reach them.

What was actually read, strongest first.

1. **`epics-modules/vac`, read directly from the source, 2026-09-02.** The APS
   BCDA synApps vacuum module. Cloned from
   `https://github.com/epics-modules/vac` at the head of the default branch and
   read on disk. It carries EPICS device support for the Series 350 controller
   in `vacApp/src/devVacSen.c` and `vacApp/src/devVacSen.h`, and its serial
   settings table in `docs/vacuum-gauges.md`.

   This is working code that people at a synchrotron point at real controllers.
   It is still not a manual. It carries no worked examples, it does not say
   which firmware revisions its choices apply to, and it covers the 350 only.
   Anything resting on it alone is unverified and is listed in `../../../REVIEW.md`.

2. **Manual text relayed through the web search tool, 2026-09-02.** The search
   tool can read the PDFs this machine cannot download, and it returned specific
   statements from them, including one worked exchange. Those statements are
   quoted below and attributed to the manual they came from.

   This is second hand. It is a summariser's reading of a manual, not the
   manual. It gave no page images and no continuous text, so a table could not
   be read whole and nothing here can be checked against its surroundings. It is
   ranked below source 1 because source 1 was read directly, character by
   character, and this was not.

   The documents it drew from:

   - Series 354 Micro-Ion Instruction Manual, P/N 354008, MKS.
     `https://api.p1.mks.com/mam/celum/celum_assets/resources/GP-354wRS485Digital-354008-MAN.pdf`
     and a Caltech mirror at
     `https://mmrc.caltech.edu/Vacuum/Hornet_Ion_Gage/Micro-ion%20gage%20(Hornet).pdf`
   - Series 275 Mini-Convectron Module with RS-485 and Dual Process Relays,
     Instruction Manual P/N 275545, Revision C, November 2016.
     `https://www.mks.com/mam/celum/celum_assets/resources/GP-275RS485DualRelays-275545-MAN.pdf`
   - Series 356 Micro-Ion Plus Vacuum Gauge Module Instruction Manual,
     P/N 356007.
   - Series 375 Convectron Vacuum Gauge Controller Instruction Manual,
     P/N 000495-114, and the Series 375 brochure on `idealvac.com`.
   - Process Control and RS-232 or RS-485 Interface for Granville-Phillips
     Series 340, 358 and 360, P/N 011979.
     `https://www.mks.com/mam/celum/celum_assets/resources/GP-340-358-360GaugeInterface011979-MAN.pdf`

3. **Nothing else.** No forum thread, no vendor Python driver and no LabVIEW
   code contributed a fact here. The one public LabVIEW project for the 375,
   `github.com/jfrech14/Granville-Phillips-375_RS232`, was cloned and opened.
   Its VI is compiled binary and its command strings could not be read out of
   it, so it contributed nothing.

The first person to hold one of these manuals should read this file against it.
`../../../REVIEW.md` lists item by item what is unverified and what a bench visit
should check first.

## The four models are one protocol, with different gauges behind it

All four speak the same ASCII messages with the same `#` framing and the same
terminator. What differs is how many gauges sit behind one address, and what
each gauge is called.

| | 275 | 375 | 350 | 356 |
|---|---|---|---|---|
| What it is | Mini-Convectron module | Convectron controller | Ion gauge controller | Micro-Ion Plus module |
| Interface | RS-485 | RS-232 or RS-485 | RS-232 or RS-485 | RS-485 |
| Gauges behind one address | one | one, in this driver | four | one |
| Gauge selectors | none | none, in this driver | `1`, `2`, `A`, `B` | none |
| Where the selectors come from | manual, relayed | not sourced, see below | `epics-modules/vac`, read directly | manual, relayed |

The 350 is the one with several gauges. `1` and `2` are its ion gauges, `A` and
`B` its Convectron gauges. That naming is from `devVacSen.h`, read directly.

**The 375 is the weak one.** It is a multi-channel controller, and no source
found here says how to ask it for a particular channel. This driver therefore
sends it a bare `RD`, the same message the single gauge modules take, and reads
whatever that returns. Do not trust which channel that is until somebody checks
it against the manual. It is item 1 of the 375 list in `REVIEW.md`.

## Framing

A message is a start character, a two digit address, a command, and a
terminator.

The Series 354 manual, relayed, gives the shape as: a start character `#`, an
address, a command, and a command modifier, followed by a terminator. The
address is "two ASCII digits representing the Hex address of the module". The
terminator is "control M or Hex 0D", a carriage return.

```
#01RD<CR>
```

The bytes are `23 30 31 52 44 0D`. There is no checksum, no line feed and no
start-of-text byte. The `<CR>` is one byte, `0x0D`. Sending the two characters
`\` and `r` as text is the mistake that looks like a dead cable, because the
module waits for a terminator that never comes and so never answers.

`epics-modules/vac` agrees. It builds a GP350 command as `#` followed by the
address formatted `%02X`, and sets both the input and the output end-of-string
to a bare `\r`.

A command that names a gauge puts the selector after the command, with one
space. This is the 350 only, and it comes from `devVacSen.h` read directly.

```
#01RD A<CR>
```

## Reply format

A good reply starts with `*`. An error reply starts with `?`. Both echo the
address the message was sent to, then a space, then the payload, then the same
carriage return.

The one worked exchange found, from the Series 354 manual, relayed:

```
host    #01RD<CR>
module  *01 9.34E-06<CR>
```

An error, from the same source:

```
?01 SYNTX_ER<CR>
```

`SYNTX_ER` is returned when the character string from the host is wrong or the
module does not recognise the syntax.

`epics-modules/vac` agrees on both marker characters. It treats a GP350 reply
beginning `?` as an error, and for a good reply it strips two leading characters
described in its own comment as "the leading character and the space", which is
`*` and the space. Note that its GP350 support is used with address 0 on RS-232,
where it sends a bare `#` with no address digits and so gets `*` and a space and
nothing between them. This driver always sends an address, so it always expects
the address back.

**The driver checks the echoed address against the address it sent.** That
matters on RS-485, where a frame reaches every module on the pair. A reply from
the wrong module is otherwise a plausible pressure attributed to the wrong
gauge, which is the worst kind of wrong.

The 354 and 275 manuals, relayed, both say that data field responses contain 13
characters. `*01 9.34E-06` is 12 characters, so either the count includes the
terminator or it counts something this driver has not seen. The driver does not
rely on a fixed width. It parses what is between the space and the terminator.

## Pressure format, and the reading that is not a reading

A pressure comes back in scientific notation, as `9.34E-06`. The unit is
whatever the instrument is configured for and is not in the reply. See the units
section below, because this is a trap.

**`9.99E+09` means there is no reading yet.** The Series 354 manual, relayed,
says the initial `RD` reading is `9.99E+09` for three seconds and then valid
pressure readings follow. The Series 343 manual says the same with five seconds.
So it is what the gauge reports while it is starting up, and by every account of
the family it is also what an ion gauge that is off reports.

This is the same trap the Lakeshore driver hit from the other side. The gauge
does not go silent when it cannot measure. It answers with a number. A driver
that trends that number plots 9.99e9 torr next to 1e-6 torr and ruins the chart,
or worse, averages it. So the driver treats any reading at or above 1e9 as no
reading at all and records a gap.

`epics-modules/vac` uses 9.9e+9 as its own "no value" marker for these
controllers, which is the same idea arrived at independently.

## Serial settings

| | 275 | 375 | 350 | 356 |
|---|---|---|---|---|
| Baud | not sourced | 9600 | 9600 | not sourced |
| Data bits | not sourced | 8 | 8 | not sourced |
| Parity | not sourced | none | none | not sourced |
| Stop bits | not sourced | 1 | 1 | not sourced |

The 375 row is from the Series 375 brochure and manual, relayed: RS-232 or
RS-485, 9600 baud default, ASCII, 8 data bits, one stop bit, no parity, no
handshake. The 350 row is from `docs/vacuum-gauges.md` in `epics-modules/vac`,
read directly, which gives the GP350 as 9600 baud, 8 data bits, no parity, one
stop bit, with `\r` in both directions.

The 275 and 356 manuals both have a baud rate section that nothing here could
read. The driver defaults them to 9600 8-N-1 because that is what the two
sourced models use and because these are one product family. **That default is a
guess** and it is in `REVIEW.md`. If a 275 will not answer, the baud rate is the
first thing to try.

Note the contrast with the Lakeshore instruments, which want 7 data bits and odd
parity. These want 8 and none, which is what an adapter defaults to. That is one
fewer thing to get wrong here.

The 375 manual, relayed, mentions RTS and CTS handshake lines: it asserts RTS on
receiving a message terminator and negates it after transmitting the terminator
of its response. The driver does not drive or watch those lines. Nothing found
says a reply depends on them.

## Addresses

The address is two ASCII characters holding the module address in hexadecimal.

The address switch on a module runs from 0 to 15, that is `00` to `0F`
hexadecimal, per the manual relayed for the Mini-Convectron. An `SA` command
sets an address offset on top of the switch, which is how a bus gets more than
sixteen modules. `SA` writes to the module and is banned, so this driver reads
only what the switch is set to.

`epics-modules/vac` allows 1 to 31 for the GP350 and formats the same way,
`%02X`. So the driver allows 0 to 15 on the modules and 0 to 31 on the
controllers.

**No broadcast address was found in any source.** None is allowed. If a later
reader finds that one exists, leave it banned anyway. On a shared pair a
broadcast makes every module answer at once, the replies collide, and what
arrives is a mixture that still looks like a pressure.

## Commands used in version 1

All of these read. None of them change anything.

| Command | Models | What it does | Source |
|---|---|---|---|
| `RD` | 275, 375, 356 | Read the gauge pressure. | 354 and 275 manuals, relayed. One worked example. |
| `RD 1` | 350 | Read ion gauge 1. | `devVacSen.h`, read directly. |
| `RD 2` | 350 | Read ion gauge 2. | `devVacSen.h`, read directly. |
| `RD A` | 350 | Read Convectron gauge A. | `devVacSen.h`, read directly. |
| `RD B` | 350 | Read Convectron gauge B. | `devVacSen.h`, read directly. |
| `DGS` | 350 | Degas status. Worth having, because a gauge that is degassing is not measuring. | `devVacSen.h`, read directly. |
| `PC S` | 350 | Setpoint relay states. Says which process control relays have tripped. | `devVacSen.h`, read directly. |

There is no identity query in this list, and that is not an oversight. **No
source found here describes one.** So unlike the Lakeshore driver, this one
cannot ask the instrument which model it is and check it against the model it
was built for. Getting the model setting wrong is silent. It is in `REVIEW.md`.

## Commands banned outright, and why

These are refused by `CommandPolicy` before a frame is built, so they cannot
become bytes on the wire even by accident.

The list is not the safety mechanism. Anything not on the allowed list is
refused too, whether or not it appears here. The list exists so the reason is
written next to the command, where the next person will read it.

| Command | Why it is banned | How the mnemonic is known |
|---|---|---|
| `F1 0`, `F1 1` | Turns ion gauge filament 1 off and on. Turning a filament on at too high a pressure burns it out in seconds. Turning one off blinds whatever interlock is watching that gauge. | `devVacSen.h`, read directly, as a control command. |
| `F2 0`, `F2 1` | The same for filament 2. | `devVacSen.h`, read directly. |
| `DG0 OFF`, `DG1 ON` | Degas. It bakes the gauge grid at high power to drive off adsorbed gas. It is a real machine event, it takes minutes, and the gauge does not measure while it runs. | `devVacSen.h`, read directly. |
| `SE0`, `SE1` | Sets the ion gauge emission current. It changes the gauge's sensitivity, so every later reading from it means something different. | The relayed manual shows `#01SE1` selecting 4.0 milliampere emission. The `SE0` form is assumed by symmetry. |
| `SA` | Sets the module address offset. On a shared bus this renumbers a gauge, and every other host talking to it loses it without any error. | Relayed manual, named as "set address offset". |
| `SW` | Write confirm, which commits settings to the module's nonvolatile memory. | Relayed manual, named as "write confirm or state". |
| `SZ` | Sets the gauge zero. It recalibrates the instrument. A Convectron zero set at the wrong pressure is wrong for ever afterwards and looks entirely plausible. | Relayed manual names a "set zero" function. The mnemonic is assumed. |
| `SS` | Sets the gauge span, the other half of the calibration. | Relayed manual names a "set span" function. The mnemonic is assumed. |
| `SUT`, `SUM`, `SUP` | Sets the pressure units to torr, mbar or pascal. See the units section. Changing units changes what every reading means, including the tool's own readings on its own screen. | Relayed manual: the last character selects the unit, M for mbar, P for pascal, T for torr. The `SU` stem is assumed. |

Where a mnemonic is marked assumed, banning it costs nothing and is worth doing:
the command list is a document, and a command that turns out not to exist simply
never gets sent. What it must not do is masquerade as verified, which is why the
last column is here.

## Units, and why there is no unit in this driver's replies

These instruments can report torr, mbar or pascal, and the setting lives in the
instrument. The reply carries the number and nothing else.

**No read-units query was found in any source.** Set-units commands exist and
are banned. A query that reports which unit is configured was searched for
specifically and did not turn up. That is a real finding, not a gap in effort,
and it is written up in `REVIEW.md`.

The consequence for this driver is deliberate and slightly annoying on purpose.
`GranvillePhillipsGauge` takes a `units` argument and **it has no default**. The
caller has to say which unit the instrument is set to, and the unit goes into
the trend column name, so a file always says what its numbers mean. A default of
torr would have been convenient and would have produced exactly the failure the
session brief warns about: a trend file whose units changed halfway through,
where the numbers stay plausible.

This does not solve the problem. It only makes it visible. If somebody changes
the units on the front panel and does not change the driver's argument, the
column name will be wrong and nothing will notice. The only real fix is a query
that does not appear to exist.

## Timing

Nothing found here gives a required delay between messages. The driver paces
itself with `pace_s`, default 0.05 seconds, which is the number the Lakeshore
driver uses and is a judgement rather than a sourced figure.

The one timing fact that is sourced matters more: after power up, `RD` returns
`9.99E+09` for the first three to five seconds. A poller started at the same
moment as the gauge will record a gap for its first sweep or two. That is
correct behaviour, not a fault.

The library standard of a one second timeout with two retries is left alone.

## What version 1 deliberately does not do

**Multi-drop RS-485.** One driver instance talks to one address. Several gauges
on one pair are not supported in version 1. See `DECISIONS.md` for the
reasoning. The short version is that the core owns one device per transport, and
nothing here has ever seen a real bus.

**Any control action.** No filament on or off, no degas, no calibration, no
setpoints, no unit changes. Version 1 reads.

**Process control setpoint values.** `PC S` reads which relays have tripped,
which is a state, not a threshold. Reading back the configured thresholds would
need a command nothing here has sourced.

**DeviceNet.** Several of these modules exist in a DeviceNet variant. That is a
different physical layer and a different protocol, and it is out of scope.
