---
id: planarization-length
term: Planarization Length
---

## Definition
The distance over which the pad averages surface topography instead of following
it. In the effective density model it is the characteristic length of an elliptic
weighting function applied to the layout, set by long range pad deformation
[mrs-density-stepheight].

One working definition is the radius of a circle within which film thickness
stays within 10 percent of the value at that point, so a 5 mm planarization
length means features within 5 mm of a location planarize to within 10 percent
[mrs-density-stepheight].

## Physics
The pad is modelled as a plate on an elastic foundation whose stiffness follows
the local pattern density [ieee-dishing-model]. A stiffer pad bridges further
and gives better within-die uniformity [ieee-dishing-model].

Inferred, no source: planarization length is therefore a consumable property
first. Changing the stacked pad changes it, and no recipe parameter recovers it.

## On the Mirra
Not established. Planarization length depends on the pad stack rather than on
the polisher, so it should transfer between platforms running the same pad.

## Open questions
- What is the planarization length of the pad stack in use here?
- Is a hard pad on one platen and a soft pad on another being used to split
  planarization from rate?
