# Next session prompt, session 2

## Paste this at the start
I am continuing the Mirra CMP knowledge base build.
Attached: PROMPT.md, SCOPE.md, STATE.md, nodes.csv, sources.csv, edges.csv.
Read all of them before responding.

Last session covered: scaffold, Stage 0, and 29 nodes across the physics spine,
the Mirra hardware skeleton, and the Mesa cleaner.
This session focus: verify the snippet-only sources, then widen the clean domain.

## Objectives, in order
1. Open every source in sources.csv with access=snippet-only and either confirm
   the claims that cite it or correct the node. Start with
   ieee-profiler-contour-heads, amat-mirra-mesa-200mm and pat-us6537133, because
   the head zone counts, the Mesa module list and the ISRM description all rest
   on them. Change access to a real value as each one is read.
2. Fix or downgrade every claim that the reading contradicts, and log each
   correction in SESSION_LOG.md.
3. Find a tier 1 or tier 2 source for the three platen and four head carousel
   architecture. It currently rests on trade press only and the reader flags it.
4. Add 15 to 20 clean domain nodes, applies_to=mesa, to move the clean domain
   toward parity: brush chemistry, brush conditioning, particle re-adhesion,
   watermarks, back side defects, wafer transfer wet handoff, dryer defects.

## Open questions carried forward
- Which head generation shipped when, blocked on any Applied Materials document
  with a date on it.
- Whether a 200 mm Titan Profiler existed, blocked on the same.
- Which stations the 150 mm Mesa cleaner has, blocked on any 150 mm source at
  all.
- What differs between the 150 mm and 200 mm polisher, blocked on the same.
- The assignee of US6886387, which is cited for brush rpm figures.

## Searches to run
- Applied Materials Titan head Titan II Titan Profiler introduction year, on web
  and on patent assignee search
- Mirra CMP system datasheet filetype pdf, on web
- Mirra 150mm CMP cleaner stations, on web
- AMAT Mirra facilities requirements footprint utilities, on used-tool dealers
- assignee Applied Materials post-CMP brush cleaning patent, on patent search
- Mirra ISRM platen window pad part, on web

## Searches already run and empty
- Mirra CMP 150mm configuration difference 200mm platen size retrofit polisher,
  on web. Returned dealer pages and nothing on configuration differences.

## First action
Fetch https://ieeexplore.ieee.org/document/7919822/ and read what it actually
says about Titan, Profiler and Contour zone counts. Then correct or confirm
nodes/titan-head.md and nodes/titan-profiler-head.md and set the access field
for that source.
