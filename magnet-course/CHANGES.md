# Proposed changes

Changes to `CLAUDE.md`, `KICKOFF.md`, `BUILD_PROMPTS.md` and the syllabus HTML.
Nothing here has been applied. Per `CLAUDE.md` session hygiene, the syllabus and
the standing rules are yours to edit, not mine.

Each item says what is wrong, what was done in the meantime, and what the fix
would be.

Raised 2026-08-25, session zero.

---

## 1. The source directory has two names

`CLAUDE.md`, repository layout, puts the source index at `/sources/`, with
`sources.json` and `verified.log`.

`KICKOFF.md` phase 2, and the maintenance prompt at the bottom of the same file,
both address `/library/`, and add `pdf/`, `queue.md` and `export.bib`. Phase 1
says to "create the directory layout from `CLAUDE.md`, including `/library/` and
its subdirectories", which cannot be done, because `CLAUDE.md` has no
`/library/`.

**Done:** `/library/` is used. It is the superset, and it is what two of the
three prompts address.

**Fix:** in `CLAUDE.md`, replace the `/sources/` block with:

```
/library/
   sources.json       single source of truth for every reference
   verified.log       date and result of every link check
   queue.md           reading queue, three tiers
   export.bib         BibTeX, generated from verified entries
   pdf/               cached copies of every source
```

---

## 2. The three tiers are never defined

`KICKOFF.md` phase 2 says to create `library/queue.md` "with the three tiers
described in `CLAUDE.md`". `CLAUDE.md` describes no tiers, and does not mention
a reading queue at all.

**Done:** a working definition is written into `library/queue.md`. Tier 1 blocks
a named class. Tier 2 is for depth and the literature reviews. Tier 3 is parked
until the next maintenance pass.

**Fix:** confirm or replace that definition, then add it to `CLAUDE.md` so the
kickoff's reference resolves.

---

## 3. The literature review specification does not exist

The literature review prompt in `KICKOFF.md` says to write review N "per the
specification in `CLAUDE.md`". There is no such specification. `CLAUDE.md` never
mentions literature reviews, their scope, length, or where they are filed.

The after-session-zero table also refers to "Stages 1 to 4" of literature review
without saying what the four stages cover.

**Fix:** add a section to `CLAUDE.md` covering the four review scopes, the
output path, and what a review must contain. Until then the prompt cannot be
followed as written.

---

## 4. `reviews/` is missing from the layout

`BUILD_PROMPTS.md` writes `reviews/unit-N.md` in the review pass and
`reviews/adversarial.md` in the adversarial pass. The `CLAUDE.md` layout has no
`reviews/` directory.

**Done:** `reviews/` created.

**Fix:** add it to the `CLAUDE.md` layout block.

---

## 5. There are four paid sources, not three

`KICKOFF.md` phase 2 says "each of the three paid standards". The `S` object has
four entries with `f:0`: `a977`, `a773`, `iec`, and `magcamieee`.

`magcamieee` is not a standard. It is a paywalled IEEE paper, and its own `sub`
note says the same authors and content are in the open AMA Science proceedings,
which the syllabus already carries as `amamag`. It is listed in class 20 as
"Optional. Same authors, paywalled journal version."

**Proposed:** drop `magcamieee` from `S` and from the class 20 source list. A
paywalled twin of a document already held free adds nothing, and it makes the
paid count ambiguous in every prompt that refers to "the three paid standards".

---

## 6. No class can meet the definition of done without PyPI

`CLAUDE.md`, numerical rigor, requires that every number in the prose comes from
`worked.py`, that `worked.py` runs standalone using magpylib, numpy and scipy,
and that `worked.out` is committed. The definition of done repeats it.

Session zero ran with PyPI refused by the same egress policy that blocked the
sources, so magpylib cannot be installed. No class can be completed until that
clears. This is environmental, not a flaw in `CLAUDE.md`, but it is worth
recording as a hard blocker.

**Fix:** none needed in the file. Open egress to PyPI, then pin exact versions in
`magnet-course/requirements.txt` on the first session that can install them.

---

## 7. Commit and branch policy for classes conflicts

`CLAUDE.md` session hygiene item 4 says commit once per class, message format
`class NN: title`.

The after-session-zero table in `KICKOFF.md` says each class ends by merging a
branch `class/NN-slug`.

My working instructions for this repository pin all development to the branch
`claude/kickoff-md-aowok2` and forbid pushing to any other branch without your
explicit permission.

**Proposed:** commit per class directly on the designated branch, keeping the
`class NN: title` message format. If you want a branch per class, say so and
name the branch, and I will use it.

---

## 8. The class directory example does not match any rule

`CLAUDE.md` shows `classes/c01-bench-spec/` in the layout. Nothing states how
that name was derived, and it is not the first words of the class 01 title,
which is "What the bench must do, and what good means".

For 35 directories that need to be consistent for years, a rule beats an
example.

**Done:** one mechanical rule, written into `PROGRESS.md`, and the resulting 35
directory names are listed there. Class 01 comes out as `c01-bench-must-do`.

**Fix:** update the `CLAUDE.md` example to `c01-bench-must-do`, or give a
different rule and I will regenerate.

---

## 9. The syllabus states 55 contact hours, its own data says 61

`magnet-bench-syllabus.html` has a static meta value of "approx 55 h". The class
durations in `UNITS` total 3630 minutes, which is 60.5 hours, and the page's own
JavaScript computes and displays 61 h on load.

The static text is a fallback, so it only shows with JavaScript off, and when
printing from a browser that has not run the script. Small, but it is the number
someone would quote from a printout.

**Proposed:** change the static value to "approx 61 h".

---

## 10. Session zero deviated from the phase 2 commit message

`KICKOFF.md` phase 2 says to commit as `library: initial sources verified and
cached`. Nothing was verified and nothing was cached, so that message would be
false in the permanent record.

**Done:** committed as `library: source index extracted, verification blocked by
network policy`.

---

## 11. `sources.json` carries a field the kickoff does not list

`KICKOFF.md` phase 2 lists the fields for `library/sources.json` as key, title,
url, free, publisher, type, year and a verification object. The `S` object also
carries a `sub` field on the paid entries, holding the "covered free by X, buy
only if a customer cites the standard" reasoning.

Dropping it would lose the only record of why each paid source is listed but not
bought.

**Done:** kept as `free_alternative_note`. Two further fields were added:
`host`, and `year_basis`, which records where a derived year came from so that a
guess cannot pass as a fact.
