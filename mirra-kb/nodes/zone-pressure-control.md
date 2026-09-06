---
id: zone-pressure-control
term: Zone Pressure Control
---

## Definition
Setting the radial removal profile by pressurizing several chambers behind the
carrier membrane independently, so each annular zone of the wafer sees its own
load [pat-us6244942].

## On the Mirra
Zone control is the main uniformity lever on this platform. The head generations
found in public sources differ mainly in zone count, with three zones described
for Titan, four for Profiler and six for Contour
[ieee-profiler-contour-heads].

Inferred, no source: zone pressures are not independent of total load. Raising
one zone to fix an edge signature raises the average pressure and therefore the
rate, so recipe time has to be re-checked after a profile tune.

## Physics
Each chamber applies a load to a band of the wafer through the membrane
[pat-us6244942]. Boundaries between zones do not produce a clean pressure step,
and a spike at a boundary can put an unintended feature into the profile
[pat-us6450868 spec].

## Custom configurations
Nothing recorded yet.

## Open questions
- What zone pressure set is in use for each product recipe here?
- Does the tool report actual zone pressures during polish, or only setpoints?
