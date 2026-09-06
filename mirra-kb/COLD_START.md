# Cold start, Mirra CMP knowledge base

Paste this whole file into a fresh session. It is enough to resume usefully on
its own. Everything it refers to is in the same package.

---

## The project

Build a linked knowledge base of the terms an expert engineer must know,
understand and apply on Applied Materials Mirra CMP systems, standalone 150 mm
and 200 mm. Expert means able to diagnose a fault from tool behaviour, set and
defend a recipe parameter, and predict how a change affects removal rate,
uniformity and defectivity.

Target size is roughly 400 to 550 nodes across five domains, with the clean
domain at parity with the polisher. Say so rather than continuing if any domain
heads past 140.

Public sources only. No OEM manuals. Applied Materials patents are the primary
machine-specific source. **Never invent a specification. Unknown is a valid and
expected answer.**

The full contract is `PROMPT.md`. Read it before writing anything. This file is
the summary, not a replacement.

## Where it stands

29 nodes, 33 edges, 31 sources, 60 citations, 21 searches logged. Validator
clean, 0 errors and 0 warnings. Reader Health: 0 uncited, 0 orphans, 0 broken
links, 5 contested, 1 node resting on tier 4 sources only.

Scope split 6 `mirra` and 23 `cmp`. Domains: hardware 8, process 9, consumables 5,
clean 4, controls 3.

Stage 0 is done and written up in `SCOPE.md`.

## The one thing to know before trusting any of it

No page behind any citation has been read. Session 1 ran in a sandbox whose
network policy blocked every direct fetch, so all 31 sources were reached through
web search summaries. Each is marked `access=snippet-only` in `sources.csv`, and
`RESEARCH_NOTES.md` holds the verbatim summary text keyed to source id and node.

Verifying those is objective 1. Confirm or correct, update `access`, log the
correction in `SESSION_LOG.md`.

## Schema in brief

Files: `nodes.csv`, `edges.csv`, `sources.csv`, `citations.csv`, `searches.csv`,
and `nodes/<id>.md` for prose. Column order never changes. Keep commas, quotes
and line breaks out of CSV fields; prose belongs in the `.md` file.

`nodes.csv` columns:

```
id,term,aliases,type,domain,specificity,applies_to,head_gen,applications,verify,
gloss,value_status,confidence,confidence_mirra,wafer_note,updated_session
```

- `domain`: hardware, consumables, process, controls, clean
- `specificity`: `general`, `cmp`, `mirra`. Do not tag `mirra` unless a source
  ties the claim to the tool. Wanting it to be Mirra specific is not evidence.
- `applies_to`: `polisher`, `mesa`, `both`. Default polisher.
- `head_gen`: `titan`, `titan-profiler`, `either`, `custom`, `unknown`. Required
  on any head, membrane, ring or zone node. If you cannot tell which head a claim
  describes it is `unknown`, not `either`. Those mean different things and only
  one is honest.
- `applications`: from `oxide-sti`, `tungsten`, `copper`, `silicon-poly`, `all`.
  Use `all` only when the term is genuinely application independent.
- `verify`: `on-tool`, `research`, `unknowable`. Route every gap. A question you
  can answer by walking to the machine should never consume a search budget.
- `confidence` is about the general concept. `confidence_mirra` is about whether
  it applies to this tool. They routinely differ and a strong general confidence
  never carries a weak tool claim.

`edges.csv` is `from_id,to_id,relation,source_id,note` and direction matters.
`from_id` is the subject. A `causes` or `mitigates` edge asserts a mechanism and
needs a `source_id`.

## Rules that matter most

- **Claim-level citations.** Put the source id in square brackets at the end of
  the sentence it supports. A paragraph with one marker at the end is one cited
  sentence and several uncited ones. An unsourced sentence is allowed only as your
  own synthesis and must say so: `Inferred, no source: ...`
- **Patents have three parts and they are not equally trustworthy.** Background
  describes prior art, often a competitor. Specification describes an embodiment
  that may never have shipped. Claims describe what was protected. Always say
  which: `[pat-us6537133 spec]` or `[pat-us6537133 claims]`. Never cite a patent
  as if it documents the shipped machine.
- **Contested claims are a result, not a failure.** When two credible sources
  disagree, add a `## Contested` section with both positions and their ids.
- **Log every search**, including the ones that found nothing. Empty results are
  the expensive thing to rediscover.
- **Observation is tier 0.** Authoritative for the tool observed and nothing else.
  It may raise `confidence_mirra`, never `confidence`. It never deletes a
  contested section, it annotates it.
- **Keep the OEM baseline separate from custom configurations.** The baseline is
  what lets a future reader recognise that the tool in front of them is not
  standard. Losing it costs more than losing the modification.
- No em dashes. Short sentences. Batches of about 20 nodes. Never renumber or
  reuse an id. Ask before adding a node type or a relation type.

## Excluded products, they will pollute your searches

Mirra Trak or MirraTrak, Mirra DNS, Desica, Mirra Durum, Reflexion and
Reflexion LK. Different products. Reject results about them and say so. Where a
finding does transfer because of shared architecture, name the product the source
described and cap `confidence_mirra` at probable.

## First action

Read `HANDOFF.md`, then `LESSONS.md` part 2, then decide the six open schema
questions. The most pressing is that the relation list has no way to say "is a
kind of", which is why `titan-head` is not linked to `carrier-head` at all.

Then work `NEXT_SESSION.md` in order, starting with
https://ieeexplore.ieee.org/document/7919822/ and what it actually says about
Titan, Profiler and Contour zone counts.
