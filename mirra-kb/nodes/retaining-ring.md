---
id: retaining-ring
term: Retaining Ring
---

## Definition
A ring surrounding the wafer inside the head. It stops the wafer sliding out
during polish, and it presses the pad down just outside the wafer edge
[book-steigerwald-1997].

## Physics
In a head that loads the ring separately, the ring load is set by the difference
between two chamber pressures rather than by the wafer pressure
[pat-us6540594 spec]. That decouples edge pad compression from wafer down force.

The ring compresses the pad ahead of the wafer edge, so the pad arrives at the
wafer already deflected instead of rebounding under it
[book-steigerwald-1997].

Inferred, no source: the ring is a consumable and wears in use. Wear changes the
pad compression geometry at the edge, so an edge profile that drifts slowly over
weeks is a ring wear candidate before it is a recipe problem.

## On the Mirra
Not established in detail. Public sources confirm Applied Materials heads with
independently loaded rings [pat-us6540594 spec], but none reached here ties a
ring load range to the Mirra.

## Custom configurations
Nothing recorded yet. Non-OEM ring profiles and materials are a common
substitution, so record the profile and the material seen on the tool.

## Open questions
- What is the wear limit and the measured thickness of the rings in use?
- Is ring load a separate recipe parameter on this tool, or fixed?
