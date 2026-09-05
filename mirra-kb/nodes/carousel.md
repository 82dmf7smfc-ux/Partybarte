---
id: carousel
term: Carousel
---

## Definition
The rotating structure that carries the polishing heads and indexes them from
platen to platen between steps.

## On the Mirra
The system uses a rotating four-head carousel, which lets the wafer handling
robot load and unload at a transfer station while the three platens keep
polishing [sst-new-cmp-architecture]. The four wafer carriers are supported by
the carousel and move wafers through a one, two or three step polish
[sst-new-cmp-architecture].

The base polisher is dry-in and wet-out [sst-new-cmp-architecture]. With the
Mesa cleaner attached the same polisher becomes dry-in and dry-out
[amat-mirra-mesa-200mm].

Inferred, no source: four heads against three platens means one head is always
at load or unload. Throughput is therefore set by the slowest platen step plus
the index time, not by the sum of the steps.

## Contested
No source reached in this session disagrees on the three platen and four head
count, but the strongest statements found are trade press and used tool listings
rather than an Applied Materials specification [sst-new-cmp-architecture;
entrepix-mirra]. Confidence is probable rather than established for that reason.

## Open questions
- What is the index time between platens on this tool?
- Does the carousel lift the heads clear of the pad before indexing, and by how
  much?
