# Handoff, end of session 1

Written for a session that has none of this session's context: no sandbox, no
repo checkout, no transcript. Everything needed is in this package.

## What exists

A knowledge base of Applied Materials Mirra CMP terms, built to the Option B
contract in `PROMPT.md`. Flat CSV index files, one Markdown file per node for
prose, a single-file browser reader, and `validate.py` for bulk integrity checks.

Schema version 3.3. Reader version 3.3.1.

## State in numbers

From the reader Health tab, confirmed by loading the reader against these files:

| | |
|---|---|
| Terms | 29 |
| Connections | 33 |
| Sources | 31 |
| Written up | 29 |
| Uncited | 0 |
| Orphans | 0 |
| Broken links | 0 |
| Contested | 5 |
| Resting on tier 4 or 5 only | 1 |

`validate.py` exits 0 with 0 errors and 0 warnings.

Scope split: 6 tagged `mirra`, 23 tagged `cmp`, 0 tagged `general`.
Config split: 25 `polisher`, 4 `mesa`, 0 `both`.
Gap routing: 17 `on-tool`, 12 `research`, 0 `unknowable`.
By domain: hardware 8, process 9, consumables 5, clean 4, controls 3.

## What Stage 0 settled

Full answers in `SCOPE.md`. In short:

**Settled.** Three polishing platens. Four wafer carriers on a rotating carousel.
One to three polish steps. 150 mm and 200 mm. Base Mirra is dry-in and wet-out.
Mirra Mesa is the same polisher made dry-in and dry-out by the integrated Mesa
cleaner.

**Probable, not established.** Head zone counts, Titan 3 and Profiler 4 and
Contour 6. The Mesa module list, an immersion megasonic plus two double-sided
brush stations plus a spin rinse dryer, configurable up to four modules.

**Not found.** Which head generation shipped when. What differs between the
150 mm and 200 mm configurations, which was searched and came back empty. Which
platens carried the endpoint optics. Whether a 200 mm Titan Profiler existed.
Which stations the 150 mm Mesa cleaner has.

## The constraint that shaped everything

Every source was reached through web search summaries. The session's network
policy blocked direct fetches to appliedmaterials.com, patents.google.com,
uspto.gov, freepatentsonline.com and every other site tried, all 403 at the proxy.

So no page behind any citation in this base has been read. That is recorded per
source in `sources.csv` as `access=snippet-only`, and nothing resting on a
snippet is tagged `established` for the tool.

`RESEARCH_NOTES.md` holds the actual summary text, verbatim, keyed to the source
ids and to the nodes that use them. Without it those citations cannot be checked
at all. Read it before trusting anything, and replace each block with what the
real page says as you verify it.

## The five claims to be sceptical of

1. **Titan has three zones and Profiler has four.** From a search summary of a
   paywalled conference paper that was never opened. Recorded under `## Contested`
   on both nodes.
2. **Profiler is a 150 mm head.** One study says so. That is a fact about the
   study's scope, not evidence that no 200 mm Profiler existed. A dealer listing
   in the same search mentioned a "Titan II Profiler 200mm" head, uncited.
3. **Three platens and four heads on a carousel.** True as far as anything can
   tell, but sourced only to trade press and a dealer page. The reader flags
   `carousel` for exactly this. It is the weakest load-bearing claim in the base.
4. **Brush rpm figures**, 1500 rpm wafer and 400 rpm brush, come from a patent
   whose assignee was never confirmed. Recorded as an embodiment, not a Mesa
   specification.
5. **"ISRM"** appears expanded two different ways in public text, in-situ rate
   monitor and in-situ removal monitor. Recorded as contested naming.

Every carrier head patent cited is an Applied Materials patent from the right era
that never mentions the Mirra. Those claims are written as general carrier head
behaviour for that reason. The `spec` and `claims` qualifiers on those citations
were assigned from summary wording, not from reading the patent parts, so verify
the qualifier along with the claim.

## What was changed in the tooling

Two bugs found and fixed, both logged in `SESSION_LOG.md` and explained in
`LESSONS.md`. In short: the inline citation regex in `validate.py` and in the
reader could not match the qualified patent citation form that `PROMPT.md`
section 2 requires, and `PROMPT.md` section 7 carried a stale copy of
`validate.py` that would have reintroduced the bug on a cold restart. All three
now agree. No column changed and the schema is still 3.3.

## What to do next

`NEXT_SESSION.md` carries the ordered objectives. The first three matter most:

1. Open every `snippet-only` source and either confirm the claims that cite it or
   correct the node. Start with `ieee-profiler-contour-heads`,
   `amat-mirra-mesa-200mm` and `pat-us6537133`, because the head zone counts, the
   Mesa module list and the ISRM description all rest on them. Update the `access`
   field as each one is read.
2. Log every correction in `SESSION_LOG.md`. It is append only.
3. Find a tier 1 or tier 2 source for the three platen and four head architecture.

Then widen the clean domain, which sits at 4 nodes against 25 polisher nodes and
is meant to reach parity.

`LESSONS.md` part 2 holds six schema proposals that need a decision before the
next batch, the most pressing being that there is no relation meaning "is a kind
of", which is why `titan-head` is not linked to `carrier-head` at all.

## Running it

```bash
python3 -m http.server 8000     # then open mirra-kb-reader.html
python3 validate.py             # exit 0 means no errors
```

The reader makes no network calls in CSV mode. Excel will corrupt these files if
you let it guess types, so import as text or stay out of Excel.
