# Session Prompts

Copy the relevant block into Claude Code. `CLAUDE.md` carries the standing rules, so these stay short.

---

## Session 1: scaffold and foundations

Paste this once, at the start.

> Set up this repository per `CLAUDE.md`. Do not write any class material yet.
>
> 1. Create the directory structure and empty `PROGRESS.md` and `CHANGES.md`.
> 2. Extract every source from the `S` object in `syllabus/magnet-bench-syllabus.html` into `sources/sources.json`, keyed the same way, with fields: key, title, url, free, publisher, type, and a `verified` object. Fetch every URL. Record the result in `sources/verified.log`. For anything that fails to resolve, search for a working replacement of equal credibility and note the swap.
> 3. For each of the three paid standards, run a fresh search for free equivalents and add any you find. I do not want to buy anything unless there is no alternative.
> 4. Write `shared/notation.md`. Symbols, units, sign conventions, and the SI to CGS conversions I will actually use. Base it on the CAS lecture notes so we match the literature rather than inventing our own scheme.
> 5. Write `shared/glossary.md` as a stub with the twenty terms the syllabus already uses.
> 6. Write `shared/reference-part.md`. Propose three candidate reference magnets, each a specific purchasable part with a datasheet URL, and recommend one. Criteria: cheap, stable, well characterized on the datasheet, simple geometry, large enough to map at reasonable resolution, and a grade whose temperature coefficients are published. Every worked example in the course will use this part, so make the case properly.
> 7. Report back with the source verification summary and your reference part recommendation. Do not proceed past this without my answer.

---

## Session 2: build the exemplar class

Do class 06 first, not class 01. It is the densest and most source heavy class in the course. If the template survives it, it survives anything.

> Write class 06, Hall sensors: physics, planar effect, active area, offset. The syllabus entry in `syllabus/magnet-bench-syllabus.html` gives the objective, the beat structure, the sources, and the artifact. Follow `CLAUDE.md` exactly.
>
> Specific requirements for this one:
> - Read Sanfilippo end to end before writing a word. It is the primary source and most of the class comes from it.
> - `worked.py` must compute the active area averaging error for our reference magnet at three lift-off distances, using magpylib for the true field, and show how much of the reported reading is an artifact of the probe geometry.
> - The "where this goes wrong" section should have at least five entries for this class.
> - The artifact is a probe error checklist I can fill in for any candidate probe.
>
> When you are done, tell me what you would change about the class template before we scale it to the other 34.

---

## Per-class prompt

Use this for every class after the exemplar. Fill in the two blanks.

> Write class **NN**, **title**. Follow `CLAUDE.md`. The syllabus entry gives the objective, beats, sources, and artifact.
>
> Before writing: read `shared/notation.md`, `shared/reference-part.md`, and the class files immediately before and after this one if they exist. Fetch and read every listed source. Add sources if the listed ones do not cover the material, and log them in `sources.json`.
>
> After writing: run the definition of done checklist from `CLAUDE.md` and report which items passed. Update `PROGRESS.md`. Tell me anything you could not source properly.

---

## Batch prompt, for the cheap classes

Some classes are short and mostly synthesis. Batching two saves setup time.

> Write classes **NN** and **NN**. They are closely related, so build them together and make the handoff between them explicit. Everything else per `CLAUDE.md` and the per-class prompt.

---

## Review pass, run after each unit is complete

> Review unit **N** as a whole, classes NN through NN. Do not rewrite. Produce a report at `reviews/unit-N.md` covering:
>
> 1. Notation drift. Any symbol used inconsistently across the unit.
> 2. Repetition. Anything explained twice that should be explained once and linked.
> 3. Gaps. Anything a class assumes the reader knows that no earlier class taught and no source was given for.
> 4. Source quality. Any claim resting on a weak source, and what would strengthen it.
> 5. Numbers. Spot check five calculations against the code and say whether they reproduce.
> 6. Voice. Any em dashes, any long sentences, any passive constructions that obscure who does what.
>
> List fixes in priority order. I will decide which to apply.

---

## Integration pass, run when several classes are done

> Update `syllabus/magnet-bench-syllabus.html` so that any class with material written links to its `class.md`, and shows a "material ready" marker. Do not change the class content, the checkpoint text, or the stored progress format. Keep the existing storage key so my progress survives.

---

## Adversarial pass, run near the end

Worth one full session. This is where the value is.

> You are reviewing this course as a skeptical metrologist who thinks a home bench cannot produce trustworthy multi-year magnet data. Read the whole course. Write `reviews/adversarial.md`.
>
> Find every place where the course is optimistic. Name the specific claim, the reason it is shaky, and what evidence or experiment would settle it. Pay particular attention to whether the claimed repeatability is achievable with the hardware the BOM actually specifies. If the answer is no, say so plainly and tell me what has to change.

---

## Suggested build order

Not numerical. Build the load bearing parts first, so a rethink is cheap.

1. Class 06, Hall sensors. Exemplar and hardest.
2. Classes 11 to 14, unit 3. Metrology discipline decides whether the data is worth anything.
3. Classes 15 to 19, unit 4. Mapping, the core capability.
4. Classes 02 to 05, unit 1. Foundations, written after you know what the later classes actually lean on.
5. Classes 21 to 23, unit 5. Modeling.
6. Classes 07 to 10, rest of unit 2.
7. Classes 24 to 27, unit 6. Aging.
8. Class 01 and unit 7, the build. Written last, with real knowledge of what the bench needs.
9. Unit 8, running the program.
10. Review passes, then the adversarial pass.
