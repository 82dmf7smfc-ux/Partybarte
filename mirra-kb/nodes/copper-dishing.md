---
id: copper-dishing
term: Copper Dishing
---

## Definition
The recess left in a copper line when the metal in the feature polishes faster
than the dielectric beside it [mit-boning-cu-damascene]. Measured as the depth
from the dielectric surface to the lowest point of the metal.

## Physics
Dishing is strongly feature size dependent and largely insensitive to pattern
density [mit-boning-cu-damascene]. That is the clean separation from erosion,
which behaves the other way round [mit-boning-cu-damascene].

The pad bridges a distance set by its stiffness, so a wide feature lets the pad
sag into it while a narrow one does not [ieee-dishing-model]. Both dishing and
step height reduction depend on pad stiffness and bending, on slurry, on
polishing conditions, and on the surface geometry [ieee-dishing-model].

Overpolish is the main driver of the whole family of these effects, so
controlling overpolish time controls the variation [mit-boning-cu-damascene].
A multi step polish gives an appreciable improvement in dishing and erosion over
a single step [mit-boning-cu-damascene].

## On the Mirra
Inferred, no source: the three platen architecture is well matched to the multi
step approach above, since bulk copper, barrier clear and a touch step can each
have their own pad and slurry [sst-new-cmp-architecture].

## Typical values
None taken as established here. Dishing numbers are quoted per feature width, so
a single number without a width is not usable.

## Open questions
- Is copper actually run on this tool, and with what step split?
