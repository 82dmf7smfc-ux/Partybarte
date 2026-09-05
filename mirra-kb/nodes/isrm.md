---
id: isrm
term: In-Situ Rate Monitor
---

## Definition
Applied Materials' in-situ optical endpoint and rate monitor. It determines
endpoint from periodic optical interference changes, with the signal from a
patterned wafer processed by digital filtering so that intensity varies
periodically as material is removed [pat-us6537133].

## On the Mirra
Applied Materials describes the optical endpoint methodology as available on
Mirra, Mirra Mesa and Reflexion [amat-pr-optical-endpoint]. The technique puts a
laser interferometer in the platen, directs the beam through a transparent window
in the polishing pad, and reads the light reflected from the wafer
[amat-pr-optical-endpoint]. The Mirra product page lists precise endpoint
detection technology alongside the multi-platen architecture and Titan Head
carriers [amat-mirra-200mm].

Inferred, no source: a window in the pad is a consumable constraint. A pad
ordered without the window makes the sensor useless on that platen, and the
failure looks like a dead sensor rather than a wrong part.

## Physics
Interference between light reflected from the top and bottom of a transparent
film gives an intensity that cycles as the film thins [amat-pr-optical-endpoint].
Counting cycles gives thickness removed, and the cycle rate gives removal rate.

## Contested
Not contested between sources, but the naming is loose. Public text uses in-situ
rate monitor and in-situ removal monitor for the same abbreviation
[amat-mirra-200mm]. No source reached here fixes the expansion, so treat the
long form as unconfirmed.

## Open questions
- Which platen or platens carry the ISRM optics on this tool?
- Is the pad on that platen a windowed part number?
- The underlying patent US6537133 was named in a press release but not read in
  this session, so no claim here rests on the patent text itself.
