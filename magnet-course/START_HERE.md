# Start Here

## Setup, two minutes

Download these five files into one empty directory:

```
CLAUDE.md                        standing rules, read every session
BUILD_PROMPTS.md                 per-session prompts, used from session 2 on
KICKOFF.md                       session map and the review prompts
magnet-bench-syllabus.html       the 35 class syllabus, source of truth
magnet-lifecycle-research.html   the research checklist
```

Open Claude Code in that directory. Paste the block below. That is the whole
setup.

---

## The prompt

> You are building a comprehensive course repository. Read this whole prompt
> before acting.
>
> **What we are building.** Written lecture material for a 35 class self-directed
> course on permanent magnet metrology, plus an accumulating source library. The
> end product is a working bench that maps and images permanent magnet fields and
> tracks them over years. The reader is one person: an electronics engineer,
> comfortable with circuits, instrumentation, and Python, with no prior magnetics
> background.
>
> **Read first, in this order.** `CLAUDE.md` carries the standing rules and
> governs every session including this one. `BUILD_PROMPTS.md` holds the prompts
> we use from session two onward. `KICKOFF.md` has the session map and the review
> prompts. `magnet-bench-syllabus.html` is the source of truth for scope: the
> units, the classes, the beat structure, the sources, and the artifacts. Do not
> redesign the syllabus. If any of these files is missing, stop and tell me
> rather than improvising a replacement.
>
> **Non-negotiables, restated here so they cannot be lost.** No em dashes
> anywhere. Short sentences. Never invent a citation: if you did not fetch the
> URL in this session, do not cite it. Free sources first, and search for a free
> equivalent before citing anything paywalled. Never write hard gates,
> prerequisites, or blocking steps, because I work in whatever order suits me.
> Warnings and recommendations are welcome and should be phrased as consequences,
> not permissions. Every number in the prose must come from runnable code or a
> cited source.
>
> **This session builds the spine. No class material.** Work the phases in order,
> committing at each one.
>
> Phase 1. Initialise git. Build the directory layout from `CLAUDE.md`, including
> `/library/` and its subdirectories. Move the two HTML files into `/syllabus/`.
> Create `PROGRESS.md` with a status table covering all 35 classes, columns for
> status, date, word count, sources used, and open questions, rows empty. Create
> `CHANGES.md` and `requirements.txt`. Add a `.gitignore`, and tell me whether
> you chose to track `library/pdf/` or not, and why. Commit as
> `scaffold: repository structure`.
>
> Phase 2. Extract every source from the `S` object in the syllabus HTML into
> `library/sources.json`, keyed identically, with fields for key, title, url,
> free, publisher, type, year, and verification. Fetch every URL. Cache every
> free source into `library/pdf/`. Log every attempt in `library/verified.log`
> with date, result, and one line on what the source actually contains, which is
> often narrower than its title suggests. Replace anything that fails to resolve
> with something of equal credibility and log the swap. For each paid standard,
> run a fresh search for free equivalents beyond those already noted. Generate
> `library/export.bib`. Build `library/queue.md` with the three tiers from
> `CLAUDE.md`, seeded from the bibliographies of what you just fetched. Expect
> this to be substantial. Commit as
> `library: initial sources verified and cached`.
>
> Phase 3. Write `shared/notation.md`, taking symbols and sign conventions from
> the CAS lecture notes so we match the literature. Include the SI and CGS
> conversions actually needed. Write `shared/glossary.md` as a stub covering the
> terms the syllabus already uses. Commit as `shared: notation and glossary`.
>
> Phase 4. Write `shared/reference-part.md`. Propose three candidate reference
> magnets, each a specific purchasable part with a datasheet URL you fetched.
> Criteria: inexpensive, dimensionally simple, published temperature
> coefficients, large enough to map at reasonable resolution, stable enough to
> serve as a control sample for years. Recommend one and argue for it. Every
> worked example in all 35 classes uses this part, so a poor choice propagates
> everywhere. Commit as `shared: reference part candidates`.
>
> Phase 5. Update `PROGRESS.md`. Tag `session-0-complete`. Then stop and report:
> the source verification summary, including which sources turned out weaker than
> their titles imply; what you found for the paid standards; the size and shape
> of the reading queue and which tier one items look most valuable; your
> reference part recommendation with reasoning; and anything in `CLAUDE.md` or
> the syllabus you think is wrong or will cause trouble later. Raise it now
> rather than working around it silently.
>
> Do not begin class material. I will answer your report, and then we start with
> class 06 using the exemplar prompt in `BUILD_PROMPTS.md`.

---

## What happens next

| Session | Prompt | Ends at |
|---|---|---|
| 0 | the block above | tag `session-0-complete` |
| 1 | exemplar, class 06, in `BUILD_PROMPTS.md` | template review, tag `exemplar-approved` |
| 2 onward | per-class prompt | merge `class/NN-slug` |
| unit done | review pass | tag `unit-N-complete` |
| 4 stages | literature review prompt in `KICKOFF.md` | tag `lit-review-N` |
| near end | adversarial pass | `reviews/adversarial.md` |
| quarterly | maintenance prompt in `KICKOFF.md` | `library: maintenance YYYY-MM` |

Build order is in `BUILD_PROMPTS.md` and is deliberately not numerical. Class 06
first because it is the hardest and will stress the template, then unit 3, then
unit 4, then the foundations, and the bench build class last.
