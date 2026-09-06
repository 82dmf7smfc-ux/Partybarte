# Next session prompt, session 2

## Paste this at the start
I am continuing the Mirra CMP knowledge base build.
Attached: PROMPT.md, SCOPE.md, STATE.md, nodes.csv, sources.csv, edges.csv.
Read all of them before responding.

Last session covered: scaffold, Stage 0, and 29 nodes across the physics spine,
the Mirra hardware skeleton, and the Mesa cleaner.
This session focus: verify the snippet-only sources, then widen the clean domain.

## Objectives, in order
0. Re-test outbound network access before planning anything. Session 1 was
   blocked from every direct fetch and this session may not be. Run the probe
   block at the top of RESEARCH_PLAYBOOK.md, log the result in searches.csv, and
   let the answer decide how much of the rest is achievable.
1. Open every source in sources.csv with access=snippet-only and either confirm
   the claims that cite it or correct the node. Start with
   ieee-profiler-contour-heads, amat-mirra-mesa-200mm and pat-us6537133, because
   the head zone counts, the Mesa module list and the ISRM description all rest
   on them. Change access to a real value as each one is read.
2. Fix or downgrade every claim that the reading contradicts, and log each
   correction in SESSION_LOG.md.
3. Find a tier 1 or tier 2 source for the three platen and four head carousel
   architecture. It currently rests on trade press only and the reader flags it.
4. Split the pure physics out into general-tagged nodes. Hertzian contact,
   boundary layer behaviour and asperity statistics are currently folded into
   cmp-tagged nodes, which makes the scope split overstate CMP specificity.
   Point the cmp nodes at them with governed_by.
5. Add clean domain nodes, applies_to=mesa, to move the clean domain
   toward parity: brush chemistry, brush conditioning, particle re-adhesion,
   watermarks, back side defects, wafer transfer wet handoff, dryer defects.

## Read first
RESEARCH_PLAYBOOK.md, sections 2 and 4. The Wayback Machine may hold the Applied
Materials product pages that would settle Stage 0, and searching the literature
for papers that ran on a Mirra is the cheapest way to get a real tier 2 or 3
source about this tool rather than about CMP in general.

## Open questions carried forward
- Which head generation shipped when, blocked on any Applied Materials document
  with a date on it.
- Whether a 200 mm Titan Profiler existed, blocked on the same.
- Which stations the 150 mm Mesa cleaner has, blocked on any 150 mm source at
  all.
- What differs between the 150 mm and 200 mm polisher, blocked on the same.
- The assignee of US6886387, which is cited for brush rpm figures.
- Whether Titan I and Titan II are distinct generations. Two dealer part numbers
  found in session 1 imply they are, and imply a 200 mm Profiler existed.

## Searches to run
- web.archive.org CDX for appliedmaterials.com Mirra pages circa 1998 to 2004
- "Applied Materials Mirra" polish experimental, on Google Scholar and OpenAlex
- "Titan head" OR "Titan Profiler" CMP uniformity, on Semantic Scholar
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
