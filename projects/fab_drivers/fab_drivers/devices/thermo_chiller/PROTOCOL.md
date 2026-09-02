# Thermo NESLAB and ThermoFlex chillers, NC serial protocol

The protocol notes this driver was written from. Read this before changing
`driver.py`.

Covered here: the Thermo NESLAB bath and recirculator line running the NC
protocol, and the Thermo Scientific ThermoFlex recirculating chillers. They
supply process cooling water. This driver reads bath temperature, setpoint,
pump pressures, flow, and fault state.

**This is the first binary protocol in this library.** Everything before it was
ASCII with a carriage return on the end. This one sends raw bytes with a
checksum and no terminator at all, which is why it needed a change to the shared
transport. See `../../../DECISIONS.md`, the entry for 2026-09-02.

## Sources, and how much each one is worth

Read this section before trusting anything below it.

**Two Thermo NESLAB manuals were read directly on this machine, in full.** That
is a first for this project. The two Granville-Phillips and Lakeshore drivers
were both written without a manual. This one was not.

What was read, strongest first.

1. **`NESLAB_RTE110-112_man.pdf`, read directly, 2026-09-02.** Thermo NESLAB RTE
   Series Refrigerated Bath/Circulators, Instruction and Operation Manual.
   Appendix A, "Serial Communications Protocol", pages 27 to 31 of the PDF.

   Read from the file, character by character, after extracting its text. It
   gives the frame layout, the checksum rule in words, four fully worked
   examples with their byte values, the complete Table 1 of commands with the
   exact bytes for each, the error responses, and the qualifier byte table.

   **This is a manual, opened and read.** It is the strongest kind of source
   this project has.

2. **`ThermoNESLAB_RTE9-12_man.pdf`, read directly, 2026-09-02.** Thermo NESLAB
   RTE 7, RTE 10, RTE 17 and RTE 25 series, Digital Plus controller. Appendix B,
   "NC Serial Communications Protocol", pages 47 to 51 of the PDF.

   The newer of the two. Same protocol, and it adds RS-485, the second lead
   character, the address range, the Read Status command with its bit table, and
   the cool-side PID commands. Four more worked examples, two of them on RS-485.

   Both PDFs came from the `manuals/` folder of the public repository
   `github.com/octopode/bathtime`, which was cloned and read on disk. They are
   Thermo NESLAB's own documents, not somebody's notes about them. What is
   second hand is only how they arrived here, not what they say.

3. **`Dennis-van-Gils/MHT_Tunnel`, read directly, 2026-09-02.** Cloned from
   `https://github.com/Dennis-van-Gils/MHT_Tunnel` and read on disk. The file
   `Python/DvG_dev_ThermoFlex_chiller__fun_RS232.py` is a working RS-232 library
   for a ThermoFlex chiller, written in 2018 against a real one.

   **This is the only source here for anything ThermoFlex specific.** It is
   working code and it is not a manual. It carries no worked examples, it does
   not say which ThermoFlex model or firmware it was written against, and where
   it disagrees with the NESLAB manuals it is the manual that wins. Everything
   resting on it alone is listed in `../../../REVIEW.md`.

4. **`octopode/bathtime`, read directly, 2026-09-02.** The file `neslabrte.py`,
   a working library for the RTE line. Used here only as a cross-check, and it
   agreed with the manual on every point checked.

5. **Manual text relayed through the web search tool, 2026-09-02.** Used only
   for the ThermoFlex manual, which could not be downloaded. It confirmed that
   the ThermoFlex manual's Appendix C is titled "NC Serial Communications
   Protocol", that it is a master-slave half-duplex binary protocol, and that
   the default port settings are 9600 baud, 8 data bits, 1 stop bit, no parity,
   with an RS-485 slave address defaulting to 1. It could not return the
   ThermoFlex command table or its status bit table. That is a real gap and it
   is written up in `../../../REVIEW.md`.

**What the network refused.** Every manufacturer and distributor site was
blocked at the proxy with a refused CONNECT: `thermofisher.com`,
`documents.thermofisher.com`, `manualslib.com`, `idealvac.com`,
`marshallscientific.com`, `chillercity.com`, `artisantg.com`, and the university
mirrors at `neurophysics.ucsd.edu`, `csun.edu` and `nanofab.utah.edu`. The
WebFetch tool was refused by the same policy. `github.com` was reachable, which
is the only reason this session has manuals at all.
`../../../manuals/FETCH_PROMPT_THERMO_CHILLER.md` asks for the one document
still missing, which is the ThermoFlex serial appendix.

## Are Neslab and ThermoFlex one protocol?

Yes for the framing, and not entirely for what is behind it. This mattered
enough to be checked rather than assumed. The finding, item by item:

| | NESLAB RTE | ThermoFlex |
|---|---|---|
| Lead character | `CA` on RS-232, `CC` on RS-485 | `CA` on RS-232 |
| Frame layout | lead, address, command, count, data, checksum | the same |
| Checksum | inverted one byte sum | the same |
| Error reply | command `0F` | the same |
| Read temperature, setpoint, limits | `20`, `70`, `40`, `60` | the same |
| Qualifier byte | high nibble precision, low nibble unit | the same layout |
| Units the qualifier can name | none and °C only | eleven, including bar, PSI, LPM |
| Read Status `09` | five bytes, bath bit layout | four bytes, chiller bit layout |
| Flow and pressure commands | none, a bath has no pump pressure | `10`, `28`, `29` |
| Where this is known from | manual, read directly | source 3 only, except the framing |

The framing evidence is strong. The ThermoFlex library at source 3 builds every
frame as `[0xCA, 0x00, 0x01]` followed by the command, the count and the
checksum, computes the checksum as `(sum(bytes[1:]) % 0x100) ^ 0xFF`, and reads
the error reply at command `0F`. That is the NESLAB manual's protocol exactly.
The ThermoFlex manual's appendix carries the same title as the NESLAB one.

So this driver is **one class with a model profile**, the same shape the
Granville-Phillips driver uses. The protocol is one protocol. What differs is
which registers exist behind it and what the status bits mean, which is a
capability list, not a second protocol. `DECISIONS.md` says what would force
that decision to be reversed.

## Framing

Every frame, in both directions, is:

```
Lead char | Addr-MSB | Addr-LSB | Command | n d-bytes | d-byte 1 ... n | Checksum
```

Quoting the RTE Digital Plus manual, Appendix B, read directly:

- **Lead char.** `RS-232 = CA (hex)`, `RS-485 = CC (hex)`.
- **Addr-msb.** `Most significant byte of device address is 00 hex.`
- **Addr-lsb.** `01 - 64 hex (1 - 100 decimal) for RS-485, 01 for RS-232.`
- **Command.** One byte. The tables below.
- **n d-bytes.** `Number of data bytes to follow (00 to 08 hex).`
- **Checksum.** One byte. Next section.

There is no terminator, no start-of-text byte and no escaping. **A frame is
found by its length, and the length is inside the frame.** Byte 4, counting from
zero, is the number of data bytes to follow, so the whole frame is `6 + n` bytes
long. That is how the driver knows when a reply has finished, and it is why the
shared transport grew a `reply_size` hook.

The older RTE manual gives the count range as `00 to 03 hex`, the newer one as
`00 to 08 hex`. The driver does not enforce either. It reads the count the frame
gives it.

## The checksum, and the worked examples it was tested against

Quoting the manual, both of them, in the same words:

> Bitwise inversion of the 1 byte sum of bytes beginning with the most
> significant address byte and ending with the byte preceding the checksum. (To
> perform a bitwise inversion, "exclusive OR" the one byte sum with FF hex.)

So: add up every byte except the lead character and the checksum itself, keep
the low byte of that sum, and exclusive-or it with `FF`.

```python
checksum = (sum(frame[1:]) & 0xFF) ^ 0xFF
```

**Nineteen frames with their checksums were taken out of the two manuals, and
every one of them is a test.** They are in `tests/test_thermo_chiller.py` as
`MANUAL_EXAMPLES`, and the test checks the byte the manual prints against the
byte this code computes. Twelve are the complete request frames printed in the
two Table 1s, and seven are the fully worked exchanges in the body text.

Eighteen agree. One does not, and that one is dealt with below.

The four worked exchanges, quoted:

```
Read internal temperature, request
    CA 00 01 20 00 DE
    sum = 00+01+20+00 = 21, checksum = 21 XOR FF = DE

Reply, -10.5 degrees C, from the RTE 110 manual
    CA 00 01 20 03 11 FF 97 34
    qualifier 11 = one decimal place, degrees C
    FF97 = -105 decimal = -10.5 C
    sum = 00+01+20+03+11+FF+97 = 1CB, low byte CB, checksum = CB XOR FF = 34

Reply, 62.5 degrees C, from the Digital Plus manual
    CA 00 01 20 03 11 02 71 57
    0271 = 625 decimal = 62.5 C
    sum low byte = A8, checksum = A8 XOR FF = 57

Set setpoint reply on RS-485, address 3, from the Digital Plus manual
    CC 00 03 F0 03 11 01 2C CB
    sum = 134, low byte 34, checksum = 34 XOR FF = CB
```

**One printed checksum in the manual does not agree with the manual's own
rule.** The Digital Plus Table 1 prints Read Cool Proportional Band as
`CA 00 01 74 00 84`. The rule gives `8A`, not `84`. The independent ThermoFlex
library at source 3 also sends `8A` for that command. `8A` and `84` differ by
one character and it is almost certainly a misprint, or an artefact of pulling
text out of a PDF. This driver computes every checksum and never copies one, so
it sends `8A`. It is written up in `REVIEW.md` because a bench visit can settle
it in one command.

## Reply layout

Quoting the manual:

> The bath will respond to a Read Function by echoing the lead character,
> address, and command byte, followed by the requested data and checksum. When
> the bath sends data, a qualifier byte is sent first, followed by a two byte
> signed integer (16 bit, MSB sent first).

So a read of a measured value comes back as three data bytes: the qualifier,
then a signed 16 bit big-endian integer.

**The integer is signed.** The manual says so and its own worked example proves
it: `FF 97` is `-105`, which is `-10.5` degrees. This matters on a chiller,
because a chiller running below zero is an ordinary thing. The ThermoFlex
library at source 3 decodes the same field as unsigned. That is a bug in it that
its author would not have hit, because a ThermoFlex 900 does not go below about
five degrees. The manual wins. It is in `REVIEW.md` as a disagreement resolved
in the manual's favour.

### The qualifier byte

The manual's own table, from the Digital Plus manual:

| Qualifier | Meaning |
|---|---|
| `10` hex | 0.1 precision, no units of measure |
| `20` hex | 0.01 precision, no units of measure |
| `11` hex | 0.1 precision, °C units |
| `21` hex | 0.01 precision, °C units |

> Example: The temperature of 45.6 °C would be represented by the qualifier 11
> hex, followed by the 2 bytes 01 C8 hex (456 decimal).

Read as two nibbles, that table is: **the high nibble is the number of decimal
places, the low nibble is a unit index.** `11` is one decimal place and unit 1.
`20` is two decimal places and unit 0. The ThermoFlex library at source 3 splits
it exactly that way, and extends the unit index to eleven values.

The driver uses the nibble reading, because it covers the manual's four values
and the ThermoFlex ones with one rule. The unit names beyond "none" and "°C"
come from source 3 only:

| Index | Unit | Source |
|---|---|---|
| 0 | no unit | manual, read directly |
| 1 | °C | manual, read directly |
| 2 | °F | source 3 only |
| 3 | litres per minute | source 3 only |
| 4 | gallons per minute | source 3 only |
| 5 | seconds | source 3 only |
| 6 | PSI | source 3 only |
| 7 | bar | source 3 only |
| 8 | megaohm cm | source 3 only |
| 9 | percent | source 3 only |
| 10 | volts | source 3 only |
| 11 | kilopascals | source 3 only |

**This is the good news about this protocol.** Unlike the Granville-Phillips
gauges, which report a pressure with no unit and no way to ask which unit is
set, this instrument states the unit in every single reply. The driver records
the unit it was told alongside the value, and refuses a reading whose unit is
not the one the caller said to expect. Nobody has to remember what the front
panel is set to.

### Error replies

Quoting Table 1, both manuals:

```
Bad Command     CA 00 01 0F 02 01 ed cs
Bad Checksum    CA 00 01 0F 02 03 ed cs
```

`ed` is the echo back of the command byte as received. Command `0F` is the error
reply and is never something the host sends.

The ThermoFlex library at source 3 also handles a first data byte of `02`,
calling it "bad data received by chiller". **That third code is not in either
manual.** The driver reports it with a plainer message and says where it came
from.

## Serial settings

| | RTE 110/112 | RTE Digital Plus | ThermoFlex |
|---|---|---|---|
| Baud | 9600 | 19200 | 9600 |
| Data bits | 8 | 8 | 8 |
| Parity | none | none | none |
| Stop bits | 1 | 1 | 1 |
| Interfaces | RS-232 | RS-232 and RS-485 | RS-232 and RS-485 |
| Source | manual, read directly | manual, read directly | relayed, and source 3 |

**The baud rate is the one thing that differs between the two manuals**, and it
is the first thing to try when a chiller will not answer. 9600 on the older RTE
line, 19200 on the Digital Plus. Both manuals say "1 start bit, 8 data bits, 1
stop bit and no parity".

Two things stop a chiller answering that are not the cable.

- **Serial communication has to be switched on at the front panel.** Both
  manuals say so. The RTE 110 wants `r232` selected in the Setup Loop. The
  Digital Plus has a Computer button. A chiller with it switched off is silent,
  and looks exactly like a dead cable.
- **On RS-485 the bath waits at least 5 milliseconds** after receiving the
  checksum byte before it asserts its transmitter, and the host must release the
  line in less than 5 milliseconds. Quoting the Digital Plus manual directly.
  Version 1 does not drive a transmit enable line, so RS-485 needs an adapter
  that switches direction itself.

Pin-out, from the Digital Plus manual, 9-pin female on the chiller:

```
RS-232                    RS-485
1 No Connection           1-7 No Connection
2 TX                      8 T+
3 RX                      9 T-
4 No Connection
5 Signal Ground
6 - 9 No Connection
```

The RTE 110 manual says it the other way round, which is worth reading twice:
"Data read of the serial port connects to the data transmit (pin 2) of the bath.
Data transmit of the serial port connects to data read (pin 3) of the bath."
That is a crossover, so a null modem cable, not a straight extension. The
Digital Plus manual asks for a male to female 9 pin extension instead. **The two
manuals disagree about the cable.** Try one, then the other.

## Commands used in version 1

All of these read. None of them change anything. Every one is refused by
`CommandPolicy` unless it is on this list.

| Name in the driver | Byte | Models | What it reads | Source |
|---|---|---|---|---|
| `read_acknowledge` | `00` | all | Protocol version. Used to check something is there. | manual, read directly |
| `read_status` | `09` | all | The fault and alarm bits. | manual, read directly |
| `read_internal_temperature` | `20` | all | Bath or process fluid temperature. | manual, read directly |
| `read_external_sensor` | `21` | RTE | The external probe, if one is fitted. | manual, read directly |
| `read_setpoint` | `70` | all | The temperature setpoint. Reads it. Does not set it. | manual, read directly |
| `read_low_temperature_limit` | `40` | all | The low alarm limit. | manual, read directly |
| `read_high_temperature_limit` | `60` | all | The high alarm limit. | manual, read directly |
| `read_flow` | `10` | ThermoFlex | Process flow rate. | source 3 only |
| `read_supply_pressure` | `28` | ThermoFlex | Pump supply pressure. | source 3 only |
| `read_suction_pressure` | `29` | ThermoFlex | Pump suction pressure. | source 3 only |
| `read_low_flow_limit` | `30` | ThermoFlex | Low flow alarm limit. | source 3 only |
| `read_high_flow_limit` | `50` | ThermoFlex | High flow alarm limit. | source 3 only |
| `read_low_pressure_limit` | `48` | ThermoFlex | Low pressure alarm limit. | source 3 only |
| `read_high_pressure_limit` | `68` | ThermoFlex | High pressure alarm limit. | source 3 only |

The PID reads, `71` to `76`, exist and are documented, and are deliberately not
on the list. They are tuning constants, not measurements, and nothing trends
them. Adding them later costs one line.

### Reading a setpoint is not writing one

This is the closest thing in this library so far to a command where misreading
the manual becomes a machine action. It is worth setting out.

The manual's Table 1 has a READ block and a SET block, and they are separate
tables with separate command bytes. Read Setpoint is `70`. Set Setpoint is `F0`.
The pattern holds for every pair the manual lists:

| Reads | Writes |
|---|---|
| `70` setpoint | `F0` setpoint |
| `40` low temperature limit | `C0` low temperature limit |
| `60` high temperature limit | `E0` high temperature limit |
| `71` `72` `73` heat PID | `F1` `F2` `F3` heat PID |
| `74` `75` `76` cool PID | `F4` `F5` `F6` cool PID |

**Every write command in both manuals has bit 7 set. Every read command does
not.** That is an observed regularity across the whole of both tables, not a
rule either manual states, so it is not the safety mechanism. It is a second one.
`build_frame` refuses any command byte at or above `0x80` outright, with a
message saying why, so a driver change that put a write on the allowed list by
mistake would still not put those bytes on the wire. The allowed list remains
the thing that decides.

The one write the manuals list that does not fit the read and write pairing is
Set On/Off Array, `81`. It has bit 7 set, so the structural guard catches it too.

## Commands banned outright, and why

Refused by `CommandPolicy` before a frame is built. The list is not the safety
mechanism, because anything missing from the allowed list is refused anyway. The
list exists so the reason sits next to the command.

| Name | Byte | Why it is banned |
|---|---|---|
| `set_setpoint` | `F0` | Changes the temperature of the water feeding live equipment. A chiller setpoint moved by twenty degrees while a tool is processing is a scrapped lot at best. This is the one that matters most. |
| `set_low_temperature_limit` | `C0` | Moves the low alarm limit. Widening an alarm limit does not change the water, it stops anyone being told the water is wrong, which is worse because it is silent. |
| `set_high_temperature_limit` | `E0` | Moves the high alarm limit. Same reason. |
| `set_heat_proportional_band` | `F1` | Retunes the heat side of the control loop. A badly tuned loop oscillates, and the temperature swings for hours before anybody connects it to a command sent last week. |
| `set_heat_integral` | `F2` | The same. |
| `set_heat_derivative` | `F3` | The same. |
| `set_cool_proportional_band` | `F4` | Retunes the cool side. Same reason. |
| `set_cool_integral` | `F5` | The same. |
| `set_cool_derivative` | `F6` | The same. |
| `set_on_off_array` | `81` | Turns the chiller on and off, and switches its faults, its alarm mute, its auto restart and its serial communications. Turning off the cooling water to a running tool is the worst single command in this library so far. Its own manual notes that a unit shut down over the serial link has to be restarted over the serial link. |

Every one of these is named and given a byte in the manuals, read directly. None
of them is a guess.

## Read Status, and the two different bit layouts

`09` returns the fault and alarm bits. **The two families do not agree on what
the bits mean, and this is the one place where a mistake reads as a working
driver.** A bit that means "pump on" on one family and "high pressure fault" on
the other will produce a trend that is confidently wrong.

The RTE Digital Plus layout is the manual's Table 2, read directly, five bytes.
The ThermoFlex layout is from source 3 only, four bytes. The driver keeps them
apart as two named tables and picks by model, and it uses the byte count the
frame actually declares rather than a fixed one.

RTE Digital Plus, from the manual:

| Bit | d1 | d2 | d3 | d4 | d5 |
|---|---|---|---|---|---|
| 7 | RTD1 open fault | RTD2 open fault | high fixed temp fault | buzzer on | RTD2 controlling |
| 6 | RTD1 shorted fault | RTD2 shorted fault | low fixed temp fault | alarm muted | heat LED flashing |
| 5 | RTD1 open | RTD2 open warn | high temp fault | unit faulted | heat LED on |
| 4 | RTD1 shorted | RTD2 shorted warn | low temp fault | unit stopping | cool LED flashing |
| 3 | RTD3 open fault | RTD2 open | low level fault | unit on | cool LED on |
| 2 | RTD3 shorted fault | RTD2 shorted | high temp warn | pump on | unused |
| 1 | RTD3 open | refrig high temp | low temp warn | compressor on | unused |
| 0 | RTD3 shorted | HTC fault | low level warn | heater on | unused |

ThermoFlex, from source 3 only, and unverified:

| Bit | d1 | d2 | d3 | d4 |
|---|---|---|---|---|
| 7 | low temp fault | HPC fault | high pressure fault, factory | unused |
| 6 | high temp fault | LPC fault | low fixed flow warning | unused |
| 5 | low fixed temp fault | motor overload fault | invalid level fault | unused |
| 4 | high fixed temp fault | phase monitor fault | 5V sense fault | unused |
| 3 | RTD3 open | high level fault | low level fault | unused |
| 2 | RTD2 open | drip pan fault | low flow fault | powering down |
| 1 | RTD1 open | low pressure fault | local EMO fault | powering up |
| 0 | running | high pressure fault | external EMO fault | low pressure fault, factory |

The bit that a trend most wants is "is anything wrong at all", and the driver
answers that by counting every bit named a fault in whichever table applies. It
does not need the individual names to be right to get that answer right, which
is the one comfort available while the ThermoFlex table is unverified.

## The first bench session, for somebody standing at the chiller

Hardware access exists for this device, which is why it is third in the build
order. This is the short version to follow at the machine. It should take ten
minutes.

**1. Set the port up.**

- Service or spare port only. Never the port the tool controller is using.
- Use a USB to serial isolator. This is powered equipment.
- 8 data bits, no parity, 1 stop bit, no handshake.
- Baud: **9600** for a ThermoFlex or an RTE 110 or 112. **19200** for an RTE
  Digital Plus, which is the RTE 7, 10, 17 and 25 family.
- Cable: try a null modem first for an RTE 110 or 112, and a straight through
  9 pin male to female extension for a Digital Plus. The two manuals disagree,
  so if one gives silence, try the other before suspecting anything else.

**2. Switch serial communication on at the front panel.** RTE 110 or 112: select
`r232` in the Setup Loop. Digital Plus: press the Computer button. ThermoFlex:
the serial option in the menus. **The chiller is silent until this is done**,
and silent is exactly what a bad cable looks like. Do this before anything else.

**3. Send one command. Send this one:**

```
CA 00 01 00 00 FE
```

That is Read Acknowledge. It is the safest command on the instrument. It asks
the protocol version and touches nothing. If the address is not 1, put it in the
third byte and recompute the checksum, or use `python -m` and the driver's own
`build_frame`.

**4. A good reply is 8 bytes and looks like this:**

```
CA 00 01 00 02 v1 v2 cs
```

The first four bytes are echoed back exactly as sent. `02` is the number of data
bytes. `v1` and `v2` are the protocol version. `cs` is the checksum. The
ThermoFlex library at source 3 expects the version to be `00 00` or `00 01`,
which would make the whole reply `CA 00 01 00 02 00 00 FC` or
`CA 00 01 00 02 00 01 FB`. **Write down the exact bytes you get.** The version
this instrument reports is a fact nobody in this project has, and it is item 1
of the bench list in `REVIEW.md`.

**5. Then send Read Internal Temperature:**

```
CA 00 01 20 00 DE
```

A good reply is 9 bytes: `CA 00 01 20 03 qb d1 d2 cs`. Check the qualifier byte
`qb` against the front panel. `11` means one decimal place in °C, so `11 01 2C`
is 30.0 °C. If the front panel says 30.0 and the bytes say `11 01 2C`, the
protocol is confirmed end to end and everything else in this file is likely to
be right.

**6. If it stays silent**, in this order: serial communication switched on at
the panel, then the baud rate, then the cable, then the address.

Send nothing else. Every other command worth sending is in the driver, and the
driver refuses the ones that are not.

## Timing

The manuals give the one number that matters, in both: **"If the controller
fails to respond within 1 second, the host should resend the command."** That is
the library standard already, one second and two retries, so nothing changed.

Nothing found gives a required gap between commands. The driver paces itself
with `pace_s`, default 0.05 seconds, which is a judgement copied from the two
earlier drivers and not a sourced figure. The manual does say the controller
response must be received before the host sends the next command, which the
transport enforces anyway by doing one exchange at a time.

The 5 millisecond RS-485 turnaround is quoted in the serial settings section
above. Version 1 does not manage a transmit enable line.

## What version 1 deliberately does not do

**Any control action.** No setpoint, no limits, no PID, no on and off. Version 1
reads. The reasons are in the banned table and in `DECISIONS.md`.

**RS-485 multi-drop.** One driver instance talks to one address. The lead
character and the address range are implemented and tested, so a Digital Plus or
a ThermoFlex on RS-485 can be read, but several chillers on one pair are not
supported. The core owns one device per transport. Same reasoning as the
Granville-Phillips driver.

**The display text command.** Source 3 reads the front panel text with command
`07`, returning ASCII in the data bytes. It is genuinely useful and it is in no
manual read here, so it is not on the allowed list. It is in `REVIEW.md` as
something to add once somebody confirms it.

**Fahrenheit.** The driver reads whatever unit the qualifier byte names and
refuses a reading in a unit the caller did not expect. It does not convert.
Converting silently is how a trend ends up with two units in one column.
