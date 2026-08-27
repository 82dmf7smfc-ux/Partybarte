# Proposed changes

Problems found in `CLAUDE.md` or the syllabus. Nothing here is applied. The
syllabus HTML is not edited by any session. Raise, record, and let the user
decide.

---

## 1. `CLAUDE.md` defines the source library twice, in two places

**Status: resolved provisionally, needs a decision.**

The "Repository layout" section specifies:

```
/sources/
   sources.json
   verified.log
```

The "The library" section specifies:

```
/library/
   sources.json
   verified.log
   export.bib
   pdf/  notes/  queue.md  reviews/
```

Same two filenames, two different directories, no statement of which wins.
`KICKOFF.md` phase 2 and `START_HERE.md` phase 2 both say `library/`.
`BUILD_PROMPTS.md` session 1 step 2 says `sources/`.

Provisional resolution: **`library/` is canonical.** It is the richer
specification, it is what the session 0 prompts use, and `sources/` has no room
for the PDF cache or the notes. `sources/` now holds only a README pointing at
`library/`.

Two files claiming to be the single source of truth for every reference is the
exact drift failure `CLAUDE.md` warns about, so this is worth settling
explicitly rather than by convention.

Suggested edit: change the layout block to `/library/`, and change
`BUILD_PROMPTS.md` session 1 step 2 to match. Note that session 1 in
`BUILD_PROMPTS.md` also duplicates the session 0 work described in `KICKOFF.md`,
with slightly different wording, which is a second place the two can drift.

---

## 2. The stated contact time does not match the classes

The masthead lists `Contact time: approx 55 h`. Summing the `len` field over all
35 classes gives 3630 minutes, which is 60.5 hours.

This is cosmetic in the browser, because the page overwrites the value on load
(`updateHead` sets `#mHours` to `"approx " + Math.round(totalHrs) + " h"`, which
renders 61 h). But the literal 55 in the HTML is what a reader sees if scripting
is off, and what anyone reading the file sees.

Suggested edit: change the hardcoded `approx 55 h` to `approx 61 h`, or drop the
static value since the script replaces it anyway.

---

## 3. Three sources are in the library appendix but cited by no class

`casprog`, `a773`, and `uspas` appear in the `LIB` groups at the bottom of the
syllabus but no class lists them in its `src` array.

This is not necessarily wrong. `casprog` and `uspas` are archives to mine rather
than documents to read, and `a773` is explicitly marked as rarely needed. But
they are the three sources most likely to be forgotten, because nothing pulls
them into a session.

Suggested handling: leave the syllabus alone and carry them in
`library/queue.md` instead, which is what has been done. Revisit at the unit 2
review, when the instrument choice is being settled.

---

## 4. "The three paid standards" undercounts the paid items by one

`KICKOFF.md` and `START_HERE.md` both ask for free equivalents for "the three
paid standards". There are four sources with `f:0`:

| key | what it is |
|---|---|
| `a977` | ASTM standard |
| `a773` | ASTM standard |
| `iec` | IEC standard |
| `magcamieee` | paywalled IEEE journal paper, not a standard |

The wording is defensible, since `magcamieee` is a paper rather than a standard
and the syllabus already names `amamag` as the open version by the same authors.
Recorded so that a later session does not read "three" as "all paid items are
handled" and skip checking whether the open version really matches.

---

## 5. `tools/` is not in the specified layout

Added anyway, for scripts that keep generated files honest:
`extract_syllabus.py`, `build_sources.py`, `build_progress.py`,
`verify_sources.py`.

The reasoning: `PROGRESS.md` and `library/sources.json` both restate content
that lives in the syllabus HTML. Hand transcription of 35 class titles and 40
source keys will drift. Generating them makes drift impossible rather than
merely discouraged.

Suggested edit: add `/tools/` to the layout block in `CLAUDE.md`.

---

## 6. The source policy and this environment are in direct conflict

Not a defect in `CLAUDE.md`, but the reason session 0 is incomplete.

`CLAUDE.md` source policy rule 1: "Every source must be fetched and read before
it is cited." This environment has no outbound network access. All 40 URLs were
attempted and all 40 failed. The rule is correct and was followed, which is why
no source is marked verified and no citation appears anywhere in this
repository.

No edit suggested. The rule is the right one. The environment has to change.
