# Lakeshore 218, 224 and 336 temperature monitors

The protocol notes this driver was written from. Read this before changing
`driver.py`.

## Sources, and how much each one is worth

Read this section before trusting anything below it.

1. **`lakeshorecommsresearch.md`, supplied by the project owner, 2026-09-02.**
   This is the primary source for this driver. It is a research file, not a
   manual. It was compiled from the official Lake Shore manuals, from Lake
   Shore's own Python driver, and from forum threads and working
   implementations, and it names which fact came from which. It cites:

   - Lake Shore 218 User's Manual, Rev 2.5, P/N 119-007.
     `https://www.lakeshore.com/docs/default-source/product-downloads/manuals/218_manual.pdf`
   - Lake Shore 224 User's Manual, P/N 119-062.
     `https://www.lakeshore.com/docs/default-source/product-downloads/224_manual.pdf`
   - Lake Shore 336 User's Manual.
     `https://www.lakeshore.com/docs/default-source/product-downloads/336_manual0ebc9b06cbbb456491c65cf1337983e4.pdf`

2. **Lake Shore Cryotronics' own Python driver**, read directly from
   `https://github.com/lakeshorecryotronics/python-driver` at the head of the
   default branch on 2026-09-02. Used only as a cross-check. Where it agrees
   with the research file that is said below. It carries no worked examples.

**No Lake Shore manual was read directly.** `lakeshore.com` and every mirror
found were refused by this machine's network policy. So every statement here
rests on the research file, sometimes with the vendor driver agreeing. That is
weaker than reading the manual, and `../../../REVIEW.md` lists item by item what
is unverified and what a bench visit should check first.

The first person to hold one of these manuals should read this file against it.

## The three models are one protocol

All three speak the same ASCII command set with the same terminator. What
differs is the physical interface, the port settings, and what the sensor inputs
are called. That is why this is one driver class with a model setting rather
than three classes.

| | 218 | 224 | 336 |
|---|---|---|---|
| Interface | RS-232C, DE-9 rear panel | USB virtual COM, Ethernet, IEEE-488 | USB virtual COM, Ethernet, IEEE-488 |
| True RS-232 port | yes | no | no |
| Baud | 9600 default and maximum, 300 and 1200 also selectable | 57600 | 57600 |
| Data bits | 7 | 7 | 7 |
| Parity | odd | odd | odd |
| Stop bits | 1 | 1 | 1 |
| Flow control | none, half duplex | none | none |
| Inputs | `1` to `8` | `A`, `B`, `C1` to `C5`, `D1` to `D5` | `A` to `D` |
| Read every input at once | `KRDG? 0` | not used, see below | not used, see below |

Seven data bits with odd parity is unusual, and it is the thing most likely to
be got wrong. Nearly every USB to serial adapter defaults to 8 data bits with no
parity. Wrong parity gives silence or garbage, which looks exactly like a dead
cable. Check this first when nothing answers.

The 224 and 336 have no DE-9 socket. Their USB port enumerates as a virtual COM
port, so from the driver's point of view it is an ordinary serial port and the
same `SerialTransport` works. That is why version 1 needs no socket transport.

## Framing

There is no checksum, no address prefix and no start character. A command is the
ASCII text followed by a carriage return and a line feed.

```
KRDG? A<CR><LF>
```

Replies end the same way.

```
+077.350<CR><LF>
```

The bytes are `0x0D 0x0A`. A frequent mistake is sending the two characters
`\` and `n` as text instead of a real line feed. The instrument then never
answers, because as far as it is concerned the command never ended.

A command that takes an input is the command, one space, then the input name.
The research file records one worked example on a 218 sent with no space,
`KRDG?0`, which also answered. This driver sends the space, because that is the
form the command reference uses.

## Reply format

A single reading comes back as a signed fixed width ASCII number, for example
`+077.350`. The family command reference gives the format as `+nnnnnn`.

Do not assume the decimal point sits in the same place at every temperature.
Parse it as a float after stripping the terminator.

`KRDG? 0` on the 218 returns all eight inputs on one line, comma separated.

## Commands used in version 1

All of these read. None of them change anything.

| Command | Takes an input | What it does |
|---|---|---|
| `*IDN?` | no | Identity. Returns `LSCI,MODEL218S,<serial>,<firmware>`. Used to confirm which instrument is on the end of the cable. |
| `KRDG?` | yes | Temperature in kelvin. The main reading. |
| `CRDG?` | yes | Temperature in celsius. |
| `SRDG?` | yes | The raw sensor units, volts or ohms depending on the sensor. Useful when a temperature looks wrong, because it says whether the sensor itself is reading. |
| `RDGST?` | yes | Reading status. Zero means the reading is good. |
| `INNAME?` | yes | The name a user gave that input on the front panel. Read once at start up so a trend column can say "Cold head" rather than "A". |

## Reading status, `RDGST?`

Returns an integer whose bits flag what is wrong. Zero means the reading is
valid and can be trusted.

| Bit | Value | Meaning |
|---|---|---|
| 0 | 1 | Invalid reading |
| 4 | 16 | Temperature under range |
| 5 | 32 | Temperature over range |
| 6 | 64 | Sensor units zero |
| 7 | 128 | Sensor units over range |

The bit weights come from Lake Shore's own Python driver, which agrees with the
research file that a nonzero value flags an old reading or an over or under
range condition. The research file does not print the table itself, so the exact
weights are a cross-check rather than a manual reading. They are in
`REVIEW.md` as unverified.

This matters more than it looks. A disconnected sensor does not stay silent. It
answers with a number. `RDGST?` is the only way to find out that the number
means nothing, which is why the driver reads it alongside every temperature
rather than as an afterthought.

## Timing

Working implementations leave about 50 milliseconds between queries. Do not send
them back to back, particularly on a 218 at 9600 baud. The driver paces itself
with `pace_s`, which defaults to 0.05 seconds.

A query should answer within one to two seconds. The library standard is a one
second timeout with two retries, and that is left alone here.

## Commands banned outright, and why

These are refused by `CommandPolicy` before a frame is built, so they cannot
become bytes on the wire even by accident.

| Command | Why it is banned |
|---|---|
| `*RST` | Resets the instrument to its defaults. On an instrument in service that throws away the sensor setup somebody configured, and the tool then reads nonsense from every input. One forum report suggests a 218 that would only answer `*IDN?` after an `*RST`. Do not take that route. Power cycle the instrument or fix the port settings instead. |
| `*CLS` | Clears the status registers. It is often suggested as a harmless wake up, and it is not a machine control action, but it destroys state the tool's own software may be waiting to read. Version 1 reads. It does not clear things. |
| `SETP` | Writes a control setpoint. On a 336 that changes what the heater is doing to the cryostat. |
| `RANGE` | Sets the heater range on a 336, including turning it off. Turning a heater off during a controlled warm up is a real machine event. |
| `MOUT` | Sets a manual heater output percentage. Same reason. |
| `INTYPE` | Changes what kind of sensor an input is configured for. Gets the temperature wrong on every later reading, silently. |
| `INCRV` | Assigns a calibration curve to an input. Same silent wrongness. |
| `CRVDEL` | Deletes a user calibration curve. Destroys a calibration that may exist nowhere else. |
| `DFLT` | Restores factory defaults. |
| `ALARM` | Configures alarms. The instrument may be wired to something that acts on them. |
| `RELAY` | Drives the relay outputs directly. |

The list is not the safety mechanism. Anything not on the allowed list is
refused too, whether or not it appears here. The list exists so the reason is
written next to the command, where the next person will read it.

## What version 1 deliberately does not do

**Ethernet.** The 224 and 336 both have it, on TCP port 7777, speaking the same
ASCII with the same terminator. It is out of scope. `core/transport.py` speaks
to a serial port, and adding a socket transport is a change to shared code that
all ten drivers inherit. It is not needed here, because the USB port on both
instruments enumerates as a virtual COM port and the serial path already
reaches them.

If Ethernet is wanted later, it belongs in the core as a second transport with
the same `exchange` method, not bolted into this driver. Two facts to carry
into that work: the 336 accepts a maximum of two simultaneous sockets, so a
connection left stuck can lock out reconnects, and a VISA resource string of the
form `TCPIP::<address>::7777::SOCKET` is reported to work.

**IEEE-488.** Present on the 218S, 224 and 336. It needs a GPIB adapter that
nobody has here.

**The 3062 option on a 336,** which expands input D into D1 to D5. The driver
has a `336-3062` model for it. Nothing has confirmed the naming on a real
instrument with that card fitted.
