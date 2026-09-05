---
id: motor-current-endpoint
term: Motor Current Endpoint
---

## Definition
Endpoint taken from the current drawn by a drive motor. Motor current tracks the
power needed to turn the platen against the coefficient of friction of the
surface being polished [rev-zantye-2004].

## Physics
Polishing a low friction metal draws low current. As the metal clears and the
pad begins to work on the underlying dielectric, friction rises and current rises
with it [rev-zantye-2004]. The transition is the endpoint marker.

Inferred, no source: the signal is whole wafer and whole platen. It reports that
clearing has happened somewhere, not where. A wafer that clears at the edge first
gives the same shape of trace as one that clears in the centre first.

## On the Mirra
Not established from sources reached here. Whether the tool exposes a usable
motor current trace, and on which motor, is answerable on the machine.

## Typical values
None published for this platform. Record the shape of the trace for a known good
lot before trying to threshold it.

## Open questions
- Does the tool log platen motor current at a usable sample rate?
- Is head motor current available separately from platen motor current?
