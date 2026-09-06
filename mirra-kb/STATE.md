# State as of session 1, 2026-09-06
Schema version: 3.4   Reader version: 3.3.2

## Tool identity, from Stage 0
See SCOPE.md. Summary: three platens, four heads on a carousel, one to three
polish steps, 150 mm and 200 mm, dry-in wet-out as a base Mirra and dry-in
dry-out as a Mirra Mesa. Head zone counts are probable, not established. The
150 mm configuration is close to undocumented in public sources.

## Counts, from the reader Health tab
Terms: 29   Connections: 38   Sources: 31   Written up: 29
Uncited: 0   Orphans: 0   Broken links: 0
Contested: 0   Resting on tier 4 or 5 only: 1
Unread sources: 31   Terms resting only on unread sources: 29
Citations rows: 60, from validate.py.

Two of those numbers need reading carefully.

**Contested is 0 and that is correct.** Session 1 recorded five contested
sections. None of them was two credible sources disagreeing. They were single
weak sources with nothing against them, which is a different thing, so they were
renamed to `## Weak sourcing`. Nothing in this base has been challenged by a
second source yet, and the zero says so honestly.

**Unread sources is 31 of 31.** No page behind any citation has been opened. 26
are `snippet-only`, meaning a search summary was seen. 5 are `not-retrieved`,
meaning nothing was seen at all and the citation is an attribution by reputation:
ref-preston-1927, book-steigerwald-1997, rev-zantye-2004, thesis-lai-mit and
nccavs-feeney-2012.

The one tier 4 node is Carousel. The three platen and four head architecture
rests on trade press and a dealer page, with no tier 1 or tier 2 source behind
it. That is the single weakest load bearing claim in the base.

## Scope
mirra 6   cmp 23   general 0
polisher 25   mesa 4   both 0
Mirra terms with uncertain confidence_mirra: 0
Head nodes with no head_gen: 0          Custom configuration notes: 6 placeholders
Observation-only nodes: 0               Unrouted gaps: 0

The general count being zero is a decision now, not drift. Pure physics was
folded into cmp-tagged nodes in session 1, and splitting it out into general
nodes is objective 4 of session 2.

## Gap routing
on-tool 17    research 12    unknowable 0

Nothing is tagged unknowable yet. SCOPE.md section 5 lists the candidates. They
stay unrouted until a search has actually failed to find them.

## By domain
hardware     8 terms, 8 written, 0 uncertain confidence_mirra
consumables  5 terms, 5 written, 2 uncertain confidence_mirra
process      9 terms, 9 written, 6 uncertain confidence_mirra
controls     3 terms, 3 written, 1 uncertain confidence_mirra
clean        4 terms, 4 written, 2 uncertain confidence_mirra

Clean is at 4 against 25 polisher nodes. It is meant to reach parity, so it is
the largest structural gap in the base right now.

## Relations in use
part_of 8   governed_by 7   controlled_by 7   variant_of 5   measured_by 4
causes 3   contrasted_with 2   prerequisite_for 1   mitigates 1

## Validator
Last run: clean, 0 errors, 0 warnings
Schema 3.4 added: variant_of, a checked access vocabulary, a blocking rule on
established tool claims resting on unread sources, warnings on blank
applications and blank updated_session, and the head_gen warning now fires
regardless of domain.
Unresolved warnings: none
Custom headings appearing often: none. `## Custom configurations` on 6 nodes and
`## Weak sourcing` on 5 are both mapped headings.

## Research constraint that shaped this session
Direct page fetches were blocked by the sandbox network policy. Every source was
reached through web search summaries only. RESEARCH_NOTES.md holds that summary
text verbatim. RESEARCH_PLAYBOOK.md says how to do better next time, starting
with re-testing egress before planning anything.

## Current focus
Physics spine plus the Mirra hardware and cleaner skeleton are in. Next is
verifying the unread sources on an unrestricted network, then splitting out the
general physics nodes, then widening the clean domain toward parity.

## Known dead ends
None confirmed yet. One search came back empty: what changes between the 150 mm
and 200 mm configurations. One empty result is not a dead end. Re-run it with
different phrasing before recording it as one.
