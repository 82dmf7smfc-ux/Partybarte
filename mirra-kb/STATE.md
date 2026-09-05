# State as of session 1, 2026-09-05
Schema version: 3.3   Reader version: 3.3.1

## Tool identity, from Stage 0
See SCOPE.md. Summary: three platens, four heads on a carousel, one to three
polish steps, 150 mm and 200 mm, dry-in wet-out as a base Mirra and dry-in
dry-out as a Mirra Mesa. Head zone counts are probable, not established. The
150 mm configuration is close to undocumented in public sources.

## Counts, from the reader Health tab
Terms: 29   Connections: 33   Sources: 31   Written up: 29
Uncited: 0   Orphans: 0   Broken links: 0
Contested: 5   Resting on tier 4 or 5 only: 1
Citations rows: 60, from validate.py.

The one tier 4 node is Carousel. The three platen and four head architecture
rests on trade press and a dealer page, with no tier 1 or tier 2 source behind
it yet. That is the single weakest load bearing claim in the base.

## Scope
mirra 6   cmp 23   general 0
polisher 25   mesa 4   both 0
Mirra terms with uncertain confidence_mirra: 0
Head nodes with no head_gen: 0          Custom configuration notes: 6 placeholders
Observation-only nodes: 0               Unrouted gaps: 0

The general count being zero is a gap in the node set, not a claim. Pure
physics nodes such as contact mechanics and fluid film behaviour have been
folded into cmp tagged nodes so far.

## Gap routing
on-tool 17    research 12    unknowable 0

Nothing is tagged unknowable yet. SCOPE.md section 5 lists the candidates. They
stay unrouted until a search has actually failed to find them.

## By domain
hardware     8 terms, 8 written, 0 uncertain confidence
consumables  5 terms, 5 written, 2 uncertain confidence_mirra
process      9 terms, 9 written, 6 uncertain confidence_mirra
controls     3 terms, 3 written, 1 uncertain confidence_mirra
clean        4 terms, 4 written, 2 uncertain confidence_mirra

Clean is at 4 against 25 polisher nodes. It is meant to reach parity, so it is
the largest structural gap in the base right now.

## Validator
Last run: clean, 0 errors, 0 warnings
Unresolved warnings: none
Custom headings appearing often: "Custom configurations" is used on 6 head and
consumable nodes as an empty placeholder. It is a mapped heading, so it does not
show in the custom heading report.

## Research constraint that shaped this session
Direct page fetches were blocked by the sandbox network policy. Every source was
reached through web search summaries only. sources.csv records this per source
as access=snippet-only. Nothing resting only on a snippet is tagged established
for the tool.

## Contested sections in place
isrm, titan-head, titan-profiler-head, carousel, mesa-cleaner. Each records what
the disagreement or the weak sourcing actually is. None of them is a defect.

## Current focus
Physics spine plus the Mirra hardware and cleaner skeleton are in. Next is
verifying the snippet-only sources on an unrestricted network, then widening the
clean domain toward parity.

## Known dead ends
None confirmed yet. One search came back empty: what changes between the 150 mm
and 200 mm configurations. One empty result is not a dead end. Re-run it with
different phrasing before recording it as one.
