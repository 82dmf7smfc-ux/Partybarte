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
- No column changed. Schema stays 3.3.
Research constraint: the session network policy blocked direct fetches of
appliedmaterials.com, patents.google.com, uspto.gov, freepatentsonline.com and
every other site tried. Only web search worked, so all sources are recorded with
access=snippet-only or as free PDFs that were also not opened. This is the main
thing to fix in session 2.
Commit: see git log for this branch
