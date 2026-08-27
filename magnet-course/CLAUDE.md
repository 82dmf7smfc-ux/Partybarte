# Magnet Metrology Course: Project Instructions

Persistent rules for every session in this repo. Read this file first, then `PROGRESS.md`, then the class brief you were given.

## What we are building

Written lecture material for a 35 class self-directed course on permanent magnet metrology. The syllabus already exists and is fixed. Your job is to write the material behind each class, at a standard high enough that a competent engineer could run the bench from these files alone.

The reader is one person: an electronics engineer, comfortable with circuits, instrumentation, and Python, with no prior magnetics background. Not a student. Not a physicist. Someone building a real bench who needs to make decisions and defend them.

End state: a working bench that maps and images permanent magnet fields and tracks them over years.

## Repository layout

```
/syllabus/            the existing HTML syllabus and checklist pages
/sources/
   sources.json       single source of truth for every reference
   verified.log       date and result of every link check
/classes/
   c01-bench-spec/
      class.md        the lecture text
      worked.py       every calculation in the class, runnable
      worked.out      captured output of worked.py
      artifact/       the template or file the class produces
      sources.md      what was read, which sections, what was taken
/shared/
   notation.md        symbols, units, sign conventions
   glossary.md        terms, defined once, linked from classes
   reference-part.md  the specific magnet used in all worked examples
/PROGRESS.md          class status table, updated at the end of every session
/CHANGES.md           proposed syllabus changes, never applied silently
```

## Source policy

This is the rule that matters most. Bad sourcing makes the whole thing worthless.

1. Every source must be fetched and read before it is cited. Do not cite from memory. Do not cite a paper you only saw referenced in another paper's bibliography.
2. Record in `sources/verified.log`: URL, date fetched, whether it resolved, and one line on what it actually contains. Links rot. We want to know when.
3. Cite to the section, page, or figure. "Sanfilippo section 4.2" not "Sanfilippo".
4. Free sources only, unless nothing free covers the point. If you reach a paywall, search for a free equivalent before giving up: preprint servers, national lab reports, vendor white papers, standards summaries, university course notes. Record the search you did.
5. If a claim has no source and no derivation, either derive it in the text or delete it. Never split the difference with vague attribution.
6. Prefer primary and open: arXiv, national labs, NIST, NPL, vendor technical documents, peer reviewed open access. Avoid content farms, magnet retailer blog posts, and anything that reads as SEO.
7. When sources disagree, say so in the text and show both numbers. Do not average them silently.

## Numerical rigor

1. Every number in the prose must come from `worked.py` or from a cited source. No estimated figures typed straight into text.
2. `worked.py` runs standalone, prints its results, and is captured to `worked.out`. Use magpylib, numpy, scipy. Pin versions in `requirements.txt`.
3. Units on every quantity. SI as default, with the CGS equivalent in parentheses the first time a quantity appears in a class.
4. Show the derivation or the substitution. A result with no visible path to it is not usable by the reader.
5. Where a result depends on an assumption, name the assumption inline and state how sensitive the result is to it.

## Writing rules

1. Never use em dashes. Use a period or a comma.
2. Short sentences. Avoid stacking clauses with multiple commas.
3. Plain language first, technical term second, in parentheses, on first use.
4. Lead with the point. No throat-clearing openings, no summaries of what the class will cover beyond one line.
5. Second person. "You will measure", not "the student measures" and not "one measures".
6. No motivational filler. No "exciting", no "powerful", no "in today's fast paced world".
7. Do not write hard prerequisites, gates, or blocking steps. Recommendations and explicit warnings are welcome. The reader moves in any order they want. Phrase it as "this is easier after class 12" or "skipping this usually costs you X", never as "you must complete".

## Class file structure

Every `class.md` follows this order. Do not add sections. Do not reorder.

```
# Class NN: Title

Objective: one sentence, what you can do afterward.
Time: NN minutes. Prerequisites: none. Easier after: class NN.

## Why this matters for the bench
Three to five sentences. Concrete, tied to a decision the reader will make.

## The idea
The core explanation. This is the bulk. Build from something the reader
already knows about circuits or instrumentation where an analogy is honest.

## Worked example
Real numbers, the reference part from /shared/reference-part.md, output
from worked.py shown inline.

## Where this goes wrong
Failure modes, with the symptom the reader would actually see on the bench.
This section is not optional and is often the most valuable one.

## Do this now
The hands-on or written step. Produces the artifact.

## Sources used
Each with section reference and one line on what was taken from it.

## Open questions
Anything you could not resolve. Be honest. Leave it for the reader.
```

## Definition of done for a class

Do not mark a class complete in `PROGRESS.md` until all of these are true.

- Every source fetched, logged, and cited to a section
- `worked.py` runs clean and `worked.out` is committed
- Every number traceable to code or a citation
- The artifact template exists in `artifact/`
- No em dashes anywhere in the file
- Notation matches `/shared/notation.md`, with new symbols added there
- New terms added to `/shared/glossary.md`
- "Where this goes wrong" has at least three entries with observable symptoms
- `PROGRESS.md` updated with date, word count, and any open questions

## Session hygiene

1. One class per session. Two only if the second is short and closely related.
2. Do not edit classes other than the one you were assigned. If you find an error elsewhere, log it in `CHANGES.md`.
3. Do not modify the syllabus HTML. Propose changes in `CHANGES.md` and let the user apply them.
4. Commit once per class, message format: `class NN: title`.
5. End every session by updating `PROGRESS.md` and stating in one paragraph what the next session should pick up.

## Consistency guards

The failure mode of a 35 part build is drift. Guard against it:

- Same reference magnet in every worked example, from `/shared/reference-part.md`
- Same symbols, from `/shared/notation.md`
- Same file naming, same section order
- Before writing, read the two adjacent classes if they exist, so the handoff is clean
- If you need a symbol or convention that is not in `notation.md`, add it there first

## Version control

The repo is the record. Treat history as something you will read in two years.

1. `main` holds completed work only. Build each class on a branch named
   `class/NN-slug`. Merge with `--no-ff` so the class shows as a unit in the log.
2. Commit in stages inside a class branch, in this order, so a failed session
   leaves usable partial work:
   - `class NN: sources verified` after fetching and logging, before writing
   - `class NN: reading notes` after the notes exist
   - `class NN: draft` after the prose
   - `class NN: worked code` after `worked.py` runs clean
   - `class NN: artifact` after the template exists
   - `class NN: complete` with `PROGRESS.md` updated in the same commit
3. Tag every completed unit as `unit-N-complete`. Tag every literature review as
   `lit-review-N`. These are the points worth returning to.
4. Never rewrite published history. No force push, no rebase of merged work.
5. `PROGRESS.md` is updated in the completing commit, never in a separate one.
   The status table and the history must not disagree.
6. If a session ends mid-class, commit whatever stage is finished and write the
   handoff into `PROGRESS.md` before stopping. Do not leave uncommitted work.

## The library

Sources accumulate across the whole build. The library is a deliverable in its
own right, not a byproduct. It should outlive this repo.

```
/library/
   sources.json        canonical record, one entry per source
   verified.log        every fetch attempt, dated
   export.bib          BibTeX, regenerated whenever sources.json changes
   pdf/                local cache, filename is the source key
   notes/KEY.md        reading notes, one file per source
   queue.md            tiered backlog of unread sources
   reviews/            staged literature reviews
```

Rules:

1. **Cache locally.** Download every free source to `library/pdf/` on first use.
   Vendor white papers and lab reports disappear without warning. arXiv and NIST
   are stable, everything else is not. Record the download date.
2. **Notes before prose.** `library/notes/KEY.md` exists before any class cites
   that source. Notes record what the source actually says, with section
   numbers, in your own words. They are not summaries for the reader. They are
   working notes for the writer.
3. **Feed the queue.** Every source you read cites others. When a reference
   looks relevant, add it to `library/queue.md` under one of three tiers: read
   next, read eventually, noted only. Do not chase citations mid-class. The
   queue is what makes the literature reviews possible later.
4. **BibTeX stays current.** Regenerate `export.bib` at every unit tag. This is
   the artifact that survives if the repo does not.
5. **Re-verify at unit tags.** Re-fetch every URL in `sources.json`. Update
   `verified.log`. Replace anything that has rotted. Link rot is the slow
   failure mode of a multi-year project.

## Literature reviews

Four staged reviews, at the points where enough material exists to synthesize
something. Each produces `library/reviews/lit-N.md`. These are syntheses, not
annotated bibliographies. Argue a position and support it.

- **lit-1, after units 1 and 2.** Measurement principles. What the field agrees
  on about sensing magnetic quantities, where the methods disagree, and which
  principle suits this bench. Should settle the instrument choice with evidence.
- **lit-2, after unit 4.** Field mapping practice. How working laboratories
  actually map fields, what spatial resolutions and repeatabilities are
  reported, and how those numbers were established. Should produce a realistic
  target for what this bench can achieve.
- **lit-3, after unit 6.** Aging and stability. What is known about long term
  loss in each material family, what the reported magnitudes are, over what
  timescales, and what measurement precision was needed to see them. Should
  answer whether the planned experiment can detect anything real.
- **lit-4, at the end.** Full synthesis. What this course rests on, where the
  evidence is thin, and what the open questions are for the program going
  forward.

Each review works the queue down. Read the tier one backlog before writing it,
and log every new source properly. A review that cites only what was already
cited in the classes has failed its purpose.
