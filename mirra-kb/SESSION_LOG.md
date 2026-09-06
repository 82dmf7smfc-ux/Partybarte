# Session log

Append only. One entry per session. Never edit an old entry.

## Session 1, 2026-09-05, focus: scaffold plus physics spine and Mirra skeleton
Added: 29 nodes, 33 edges, 31 sources, 21 searches logged, 60 citations
Key finds:
- Head zone counts from one conference paper: Titan three zones, Profiler four,
  Contour six, with Profiler named for 150 mm and Contour for 200 mm.
- Mesa cleaner is configurable with up to four modules, an immersion megasonic,
  two double sided brush stations and a spin rinse dryer, with wafers gripped at
  the edge and immersed vertically.
- Applied Materials states its optical endpoint is available on Mirra, Mirra
  Mesa and Reflexion, using a laser through a window in the pad.
Corrections: none, this is the first session.
Contested found:
- ISRM expansion is loose in public text, in-situ rate monitor against in-situ
  removal monitor. Recorded on the isrm node.
- Titan zone count rests on a search summary of a paywalled paper, not on the
  paper. Recorded on the titan-head node.
- Profiler tied to 150 mm by one study only. That is a fact about the study, not
  proof no 200 mm Profiler existed. Recorded on titan-profiler-head.
Validator issues: none outstanding. Clean run, 0 errors and 0 warnings.
Tooling changes:
- validate.py CITE_RE now accepts the patent part qualifier, so
  [pat-us6537133 spec] is matched and checked. Previously the regex allowed no
  space inside the bracket, which meant every qualified patent citation was
  invisible to both the unknown-source check and the prose-without-citations
  check, even though the code below it strips the qualifier. The stripping line
  shows the check was meant to work this way.
- mirra-kb-reader.html got the same regex change so a qualified citation renders
  as a chip instead of literal text, and the chip resolves on the id with the
  qualifier shown after it. Reader marked v3.3.1.
- PROMPT.md section 7 carried the pre-fix regex in its embedded copy of
  validate.py, so a cold restart from the contract would have regenerated the
  bug. The embedded block now matches the shipped validate.py character for
  character, and the two lines that still said reader v3.3 now say v3.3.1.
- No column changed. Schema stays 3.3.
Research constraint: the session network policy blocked direct fetches of
appliedmaterials.com, patents.google.com, uspto.gov, freepatentsonline.com and
every other site tried. Only web search worked, so all sources are recorded with
access=snippet-only or as free PDFs that were also not opened. This is the main
thing to fix in session 2.
Commit: see git log for this branch

## Session 1 addendum, 2026-09-06, focus: handoff package and schema 3.4
Added: 5 edges, 0 nodes, 0 sources, 0 searches logged
Key changes:
- Schema bumped 3.3 to 3.4. Reader to v3.3.2. Contract, validator and reader all
  updated together and verified in sync.
- New relation `variant_of`, meaning "is a kind of". Five links that previously
  had nowhere to go are now written: titan-head and titan-profiler-head to
  carrier-head, sti-ceria-slurry to slurry, isrm and motor-current-endpoint to
  endpoint-detection. Before this, part_of was the only near fit and the reader
  renders it in reverse as "contains", so "Carrier Head contains Titan Head"
  would have read backwards on the page.
- `access` in sources.csv is now a checked vocabulary: read, snippet-only,
  paywalled, not-retrieved, unrecorded. New blocking rule: a node cannot carry
  confidence_mirra=established when every source behind its tool claims is
  unread. Error, not warning.
- searches.csv gains a date column. All 21 existing rows dated 2026-09-05.
- New `## Weak sourcing` heading, mapped in both the validator and the contract.
- validate.py also now warns on a blank applications field, a blank
  updated_session, and drops the domain==hardware condition from the head_gen
  check, since the contract rule is about the claim and not about the domain.
  The reader head_gen check was changed to match.
Corrections:
- All five `## Contested` sections were renamed to `## Weak sourcing`. None of
  them was two credible sources disagreeing. They were single-source claims with
  nothing against them, which is a different thing, and counting them as
  contested hid the fact that nothing in this base has been challenged yet.
  Contested count is now 0 and that is the honest number.
- Five sources were re-marked from free-pdf or paywalled to not-retrieved:
  ref-preston-1927, book-steigerwald-1997, rev-zantye-2004, thesis-lai-mit and
  nccavs-feeney-2012. The old values described availability. The new field
  describes what was actually consumed, and for these five that was nothing.
  Claims citing them are standard CMP knowledge attributed to a standard source
  that was never opened. They need confirming or replacing.
  Affected nodes: carrier-head, retaining-ring, motor-current-endpoint,
  tungsten-slurry-oxidizer, removal-rate, polishing-pad, slurry,
  endpoint-detection, preston-equation, within-wafer-nonuniformity.
- The remaining 26 sources are snippet-only, which is what they always were.
Contested found: none. See the correction above.
Validator issues: the new access check found the five rows above immediately,
which is the check earning its place on the first run.
Tooling changes: as listed above. Four new documents shipped with the base:
HANDOFF.md, COLD_START.md, LESSONS.md, RESEARCH_NOTES.md, plus
RESEARCH_PLAYBOOK.md for finding better sources next time.
Commit: see git log for this branch
