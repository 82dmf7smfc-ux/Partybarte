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
