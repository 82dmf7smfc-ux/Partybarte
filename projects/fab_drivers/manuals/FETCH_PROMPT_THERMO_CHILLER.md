# Fetch request: the ThermoFlex serial communications appendix

This goes to a machine that can reach manufacturer websites. The machine that
wrote it cannot. Every Thermo Fisher, distributor and university mirror was
refused by its network egress policy with a 403 on the CONNECT.

**This is a much smaller request than the two before it.** The Thermo NESLAB
side of this driver was written with two manuals open, read directly, so most of
the protocol is not in doubt. One document is missing and it closes the two
remaining holes.

## What this is for

`projects/fab_drivers/fab_drivers/devices/thermo_chiller/` is a read-only driver
for Thermo NESLAB and ThermoFlex chillers on the NC serial protocol. It reads
temperature, setpoint, pump pressures, flow and fault state, and trends them.

The NESLAB RTE parts of it came from two manuals read in full. The ThermoFlex
parts came from one open source library and no manual, and those parts are
listed as unverified in `projects/fab_drivers/REVIEW.md`.

## The one rule

**Hand back the original documents.** Do not retype them, summarise them, or
rewrite them into notes. A paraphrase loses exactly the detail the code depends
on, and it reads just as confidently when it is wrong. A PDF is what is wanted.

If a document genuinely cannot be obtained, say so plainly. That is a useful
answer. A confident-sounding reconstruction is not.

## What is wanted, in priority order

### 1. The ThermoFlex manual, complete, with its serial appendix

The serial section is **Appendix C, "NC Serial Communications Protocol"**. It is
the whole point of this request. A manual whose Appendix C is missing or
truncated does not help.

Known copies, any one of which would do:

- `https://www.marshallscientific.com/v/vspfiles/specs/Thermo%20Scientific%20ThermoFlex%20Chillers%20Manual%20-%20Marshall%20Scientific.pdf`
- `https://documents.thermofisher.com/TFS-Assets/LED/manuals/thermoFlex-recirculating-chillers-manual-multilingual.pdf`
- `https://www.idealvac.com/files/manuals/Chiller_Neslab_ThermoFlex-900-2500_Manual.pdf`
- `https://www.nanofab.utah.edu/wp-content/uploads/2022/10/ThermoFlex-Manual.pdf`
- `https://www.csun.edu/~vfgeo008/CH5415A/Chiller_manual.pdf`
- `https://www.slac.stanford.edu/grp/lcls/controls/global/sw/epics/app/Temperature/R7.7.1/documentation/thermoFlex-recirculating-chillers-manual-multilingual.pdf`
- `https://www.chillercity.com/OPMANUAL/ThermoFlex%20Basic%20User%20Manual.pdf`
- The manual for the Deluxe Controller specifically, which is the one with the
  serial option, is a separate document from the Basic Controller one. Prefer
  the Deluxe.

If a separate "DCOM" or "Serial Communications Option" document exists as its
own part number, that is better than the manual and is worth asking Thermo
Fisher technical support for.

### 2. The Thermo NESLAB EX series manual

Its Appendix B is the same NC protocol and would confirm the ThermoFlex reading
from a second direction.

- `https://www.manualslib.com/manual/1401911/Thermo-Scientific-Neslab-Ex-Series.html`

### 3. Anything for the Merlin series

- `https://neurophysics.ucsd.edu/Manuals/Thermo/NESLAB%20Merlin%20Recirculating%20Chillers.pdf`

## The questions the documents have to answer

This is the part that matters. If a document is found, check it against these
before handing it back, and say which ones it answers.

1. **What are the ThermoFlex command bytes for flow and pressure?** The driver
   currently uses `10` for flow, `28` for supply pressure, `29` for suction
   pressure, and `30`, `50`, `48`, `68` for the four flow and pressure alarm
   limits. All seven come from one open source library and no manual. Are they
   right?

2. **What does the Read Status reply, command `09`, actually mean on a
   ThermoFlex?** How many data bytes, and what is in each bit of each one? The
   driver has a table with names like "low flow fault", "phase monitor fault"
   and "external EMO fault" that came from the same library. **This is the item
   where being wrong looks most like working**, so the exact bit table is the
   single most valuable thing in this request.

3. **What is the full qualifier byte table?** The NESLAB manual gives four
   values: `10`, `20`, `11`, `21`. The driver reads the byte as a precision
   nibble and a unit nibble, and uses unit indexes up to 11 including bar, PSI,
   LPM and kPa. Is that the right reading, and is that the right list?

4. **Is there an error code `02`?** The NESLAB manuals list `01` for a bad
   command and `03` for a bad checksum. The library also handles `02` as bad
   data. Does the ThermoFlex manual list a third code?

5. **What does Read Acknowledge, command `00`, return?** Two protocol version
   bytes. What are they on a real chiller?

6. **Is there a command to read the front panel display text?** The library uses
   `07` and decodes ASCII out of the data bytes. It is not implemented here
   because no manual describes it.

7. **What is the default baud rate, and is it selectable?** The driver uses 9600
   for a ThermoFlex, from relayed search results. The RTE Digital Plus uses
   19200 and the RTE 110 uses 9600, both from manuals read directly.

8. **How is RS-485 addressed, and what is the address range?** The NESLAB
   Digital Plus manual gives 1 to 100 decimal with lead character `CC`. Does the
   ThermoFlex agree?

9. **Does the ThermoFlex use lead character `CA` on RS-232 like the NESLAB
   units?** The library says yes. A manual saying so would settle it.

10. **Are there worked examples in the appendix?** Complete frames with their
    byte values. If there are, they are the most valuable thing in the document
    after question 2, because they can be turned straight into tests. The
    NESLAB manuals gave nineteen and they are all tests now.

11. **Is there any command that changes machine state that this driver has not
    banned?** The banned list covers `C0`, `E0`, `F0` to `F6` and `81`. Anything
    else that writes needs to be on it.

12. **Does the ThermoFlex serial appendix disagree with the NESLAB one
    anywhere?** If it does, that disagreement is the finding, and it decides
    whether this stays one driver class or becomes two.

## Where to put what comes back

`projects/fab_drivers/manuals/thermo/`, with a `MANIFEST.md` saying for each
file: what it is, its part number, where it was downloaded from, and the date.

Then whoever holds it reads it against
`projects/fab_drivers/fab_drivers/devices/thermo_chiller/PROTOCOL.md`, which
says exactly which claims are from a manual and which are from the library, and
updates `projects/fab_drivers/REVIEW.md` item by item.

## What already exists and does not need fetching

Two Thermo NESLAB manuals were read in full and are not needed again. They came
with the public repository `github.com/octopode/bathtime`, in its `manuals/`
folder:

- `NESLAB_RTE110-112_man.pdf`, Appendix A, the serial protocol.
- `ThermoNESLAB_RTE9-12_man.pdf`, Appendix B, the same protocol with RS-485,
  the Read Status bit table and the cool-side PID commands.

Both are ordinary public files in that repository and can be fetched again from
there by anyone who needs them.
