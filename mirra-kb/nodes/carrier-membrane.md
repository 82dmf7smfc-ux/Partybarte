---
id: carrier-membrane
term: Carrier Membrane
---

## Definition
The flexible sheet behind the wafer that turns chamber pressure into load on the
wafer back [pat-us6244942]. Several chambers can sit behind one membrane, each
independently pressurized, so different zones of the wafer see different loads
[pat-us6450868 spec].

## Physics
Pressure applied to a fluid behind a compliant sheet is transmitted to the wafer
with little of the stiffness a rigid backing plate would add. That is what lets
the head follow wafer bow and pad thickness variation.

Pressure distribution is not perfectly uniform at a zone boundary, and a pressure
spike there can create unintended profile nonuniformity [pat-us6450868 spec].

Inferred, no source: this is the physical reason a zone recipe cannot produce an
arbitrary profile. The achievable profile is a smoothed version of the zone
pressure set.

## On the Mirra
The Mirra heads named in public sources are membrane heads with multiple zones
[ieee-profiler-contour-heads]. The specific membrane construction on this
platform is not documented in any source reached here.

## Custom configurations
Nothing recorded yet. Membrane part number and thickness are the usual
non-OEM substitution point, so record what is fitted.

## Open questions
- What is the membrane part number in use, and its replacement interval here?
- Does membrane age show up as a rate change, a profile change, or both?
