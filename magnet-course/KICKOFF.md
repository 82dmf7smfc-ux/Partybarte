# Kickoff Prompt

Paste the block below into Claude Code, in an empty directory, with
`CLAUDE.md`, `BUILD_PROMPTS.md`, and the two HTML files present.

It runs session zero only. Everything after that comes from `BUILD_PROMPTS.md`.

---

> Read `CLAUDE.md` in full before doing anything. It carries the standing rules
> for this repository and they apply to every session, including this one. Then
> read `BUILD_PROMPTS.md`, which holds the per-session prompts we will use from
> session two onward. Do not start writing class material.
>
> This session has one job: build the spine that everything else hangs on. Work
> through the phases in order and stop at the checkpoint at the end.
>
> **Phase 1: repository and version control.**
> Initialise git. Create the directory layout from `CLAUDE.md`, including
> `/library/` and its subdirectories. Move `magnet-bench-syllabus.html` and
> `magnet-lifecycle-research.html` into `/syllabus/`. Create `PROGRESS.md` with a
> status table covering all 35 classes, columns for status, date, word count,
> sources used, and open questions, all rows empty. Create `CHANGES.md` and
> `requirements.txt`. Add a `.gitignore` that keeps `library/pdf/` out of git if
> the cache grows past a hundred megabytes, and say which way you decided and
> why. Commit as `scaffold: repository structure`.
>
> **Phase 2: the library.**
> Extract every source from the `S` object in the syllabus HTML into
> `library/sources.json`, keyed identically, with fields: key, title, url, free,
> publisher, type, year, and a verification object. Fetch every URL. Download
> every free source into `library/pdf/`. Record every attempt in
> `library/verified.log` with the date, the result, and one line on what the
> source actually contains, which is often not what its title suggests.
>
> For anything that fails to resolve, search for a replacement of equal
> credibility and log the substitution. For each of the three paid standards, run
> a fresh search for free equivalents beyond the ones already noted. I do not
> want to buy anything unless nothing free covers the point.
>
> Generate `library/export.bib`. Create `library/queue.md` with the three tiers
> described in `CLAUDE.md`, and seed it from the bibliographies of the sources
> you just fetched. I expect this to be substantial. The CAS lecture notes and
> the Jain decks cite heavily and that is where the depth of this course will
> come from. Commit as `library: initial sources verified and cached`.
>
> **Phase 3: shared conventions.**
> Write `shared/notation.md`, basing symbols and sign conventions on the CAS
> lecture notes so we match the literature rather than inventing a private
> scheme. Include the SI and CGS conversions I will actually use. Write
> `shared/glossary.md` as a stub covering the terms the syllabus already uses.
> Commit as `shared: notation and glossary`.
>
> **Phase 4: the reference part.**
> Write `shared/reference-part.md`. Propose three candidate reference magnets.
> Each must be a specific purchasable part with a datasheet URL you fetched.
> Criteria: inexpensive, dimensionally simple, published temperature
> coefficients, large enough to map at reasonable resolution, and a grade stable
> enough to serve as a control sample for years. Recommend one and make the case.
> Every worked example in all 35 classes will use this part, so a bad choice here
> propagates everywhere. Commit as `shared: reference part candidates`.
>
> **Phase 5: report and stop.**
> Update `PROGRESS.md`. Tag this commit `session-0-complete`. Then report to me:
>
> 1. Source verification summary. How many resolved, how many were replaced, and
>    which sources turned out to be weaker or narrower than their titles imply.
> 2. What you found for the three paid standards.
> 3. The size and shape of the reading queue, and which tier one items you think
>    will matter most.
> 4. Your reference part recommendation, with the reasoning.
> 5. Anything in `CLAUDE.md` or the syllabus that you think is wrong or will
>    cause trouble later. Say so now rather than working around it silently.
>
> Do not begin class material. I will answer, and then we start with class 06 per
> `BUILD_PROMPTS.md`.

---

## After session zero

Sessions follow this loop. `BUILD_PROMPTS.md` has the exact wording.

| When | Prompt to use | Ends with |
|---|---|---|
| Session 1 | Kickoff above | tag `session-0-complete` |
| Session 2 | Exemplar, class 06 | template review, then tag `exemplar-approved` |
| Per class | Per-class prompt | merge `class/NN-slug`, update `PROGRESS.md` |
| Unit done | Review pass | tag `unit-N-complete`, re-verify links, regenerate BibTeX |
| Stages 1 to 4 | Literature review | tag `lit-review-N` |
| Near the end | Adversarial pass | `reviews/adversarial.md` |

Build order is in `BUILD_PROMPTS.md` and is deliberately not numerical. Class 06
first, then unit 3, then unit 4, then the foundations.

## Literature review prompt

Use this at each of the four staged reviews. Fill in the number and scope.

> Write literature review **N**, covering **scope**, per the specification in
> `CLAUDE.md`. Before writing, work down the tier one items in
> `library/queue.md`. Fetch, cache, and take notes on each one properly. Promote
> or demote what remains as your view of it changes.
>
> This is a synthesis, not a bibliography. Argue a position. Where the
> literature disagrees, show both numbers and say which you find more credible
> and why. Where the evidence is thin, say that plainly rather than papering
> over it.
>
> Finish by stating what this review changes about the course. If it contradicts
> something already written, log it in `CHANGES.md`. Do not edit existing
> classes. Tag the commit `lit-review-N`.

## Maintenance prompt

Run this once a quarter, or whenever you return after a gap.

> Run a library maintenance pass. Re-fetch every URL in `library/sources.json`
> and update `library/verified.log`. Replace anything that has rotted, searching
> for equivalents of the same credibility. Check that every cached PDF in
> `library/pdf/` still matches its entry. Regenerate `library/export.bib`.
> Search for work published since the last pass on the three topics that matter
> most to this bench: field mapping methods, permanent magnet long term
> stability, and Hall probe calibration. Add anything worthwhile to the queue.
> Report what changed. Commit as `library: maintenance YYYY-MM`.
