---
id: preston-equation
term: Preston Equation
---

## Definition
The first order model of material removal in polishing. Removal rate is
proportional to the product of the applied pressure and the relative velocity
between wafer and pad [jmr-2020-wafer-interface]. Preston found the relation
empirically in plate glass polishing [ref-preston-1927].

MRR = k_p × P × v

MRR = material removal rate, nm/min or A/min
k_p = Preston coefficient, fitted from data rather than derived, nm/min per kPa per m/s
P = pressure applied to the wafer against the pad, kPa
v = relative velocity between wafer and pad, m/s

## Physics
The relation is empirical and has no derivation from first principles
[jmr-2020-wafer-interface]. Everything the model does not name is buried in k_p.
That includes slurry chemistry, abrasive size and count, pad condition, and
temperature [thesis-lai-mit].

Inferred, no source: this is why k_p is not transferable. A coefficient fitted
on one pad and slurry set is a number about that consumable set, not about the
material.

## On the Mirra
Pressure comes from the head zone chambers and velocity comes from platen and
head rotation, so both terms in the equation are recipe parameters you set
directly [amat-mirra-200mm].

Inferred, no source: on a multi-zone head the equation applies per zone, since
P is a local pressure. A single tool wide k_p hides the zone structure.

## Typical values
None published for this tool in the sources reached so far. Fit k_p from your
own rate monitors rather than importing a literature value.

## Open questions
- What is the measured k_p for the pad and slurry set actually running here?
- Does k_p drift measurably across pad life on this tool?
