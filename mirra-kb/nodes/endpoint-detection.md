---
id: endpoint-detection
term: Endpoint Detection
---

## Definition
Deciding in real time when a polish step has removed enough material, rather than
polishing for a fixed time [rev-zantye-2004]. Endpoint turns a timed step into a
closed loop step.

## Physics
Two signal families are in common use. Optical methods watch reflected light from
the wafer and count interference fringes as thickness changes
[amat-pr-optical-endpoint]. Friction methods watch drive motor current, which
shifts when the material at the surface changes [rev-zantye-2004].

Inferred, no source: the choice follows the film stack. Optical suits a
transparent dielectric over a reflecting layer. Friction suits a metal clearing
to a dielectric, where the coefficient of friction changes at the transition.

## On the Mirra
Applied Materials states that its optical endpoint technology is available on
Mirra, Mirra Mesa and Reflexion systems [amat-pr-optical-endpoint]. The Mirra
product page lists precise endpoint detection as part of the architecture
[amat-mirra-200mm].

## Open questions
- Which platens on this tool carry an endpoint sensor, and which run timed?
- Is endpoint used to stop the step, or only to log a rate?
