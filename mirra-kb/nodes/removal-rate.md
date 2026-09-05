---
id: removal-rate
term: Removal Rate
---

## Definition
Film thickness removed per unit time, normally quoted in angstroms per minute
[rev-zantye-2004]. It is the headline output of a polish step and the number a
recipe is timed against when there is no endpoint signal.

## Physics
To first order the rate follows the Preston relation, so it rises with pressure
and with relative velocity [ref-preston-1927]. Everything else enters through
the Preston coefficient [thesis-lai-mit].

Three levers move rate without touching pressure or speed. Slurry chemistry sets
the rate constant for a given film [rev-zantye-2004]. Slurry supply sets how much
fresh reagent reaches the gap [sd-groove-width-mrt]. Pad condition sets how many
asperities are carrying the load [sd-diamond-disc-conditioning].

## On the Mirra
Rate is a per platen property, not a tool property. A one to three step recipe
runs different pads and often different slurries on each platen
[sst-new-cmp-architecture].

Inferred, no source: rate on platen 1 and rate on platen 3 should be tracked
separately, since they wear on different clocks.

## Typical values
Not established here from public sources. Log your own by platen and by pad age.

## Open questions
- What rate does each platen give on the film sets run here?
- How much does rate fall across one pad life?
