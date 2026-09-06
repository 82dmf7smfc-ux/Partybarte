# Lessons from session 1

Two parts. What was found and already fixed, and what needs your decision.

---

## Part 1. Findings already acted on

### The citation regex did not match the citation format the contract requires

`PROMPT.md` section 2 requires patent citations to name the part:
`[pat-us6537133 spec]` or `[pat-us6537133 claims]`. The regex in `validate.py`
and the matching one in the reader allowed no space inside the bracket. So a
qualified patent citation matched nothing at all.

The consequences were quiet, which is what made it worth fixing:

- `validate.py` never saw those citations, so it could not warn that one pointed
  at a source id that was never logged.
- A node whose only citations were qualified patent citations counted as prose
  with no inline citations, so it would have been flagged wrongly, or worse,
  a typo in a patent id would have gone unreported.
- The reader rendered `[pat-us6537133 spec]` as literal text instead of a chip,
  so the missing-source colouring never applied to it either.

The line below the regex in `validate.py`, `sid = sid.split()[0]` with the
comment "strip 'spec' / 'claims' qualifier", shows the check was written on the
assumption that the qualifier would match. It never reached that line.

Fixed in three places, all in this package: `validate.py`, the reader (now
v3.3.1), and the embedded copy of `validate.py` in `PROMPT.md` section 7.

### The contract carried a stale copy of its own validator

`PROMPT.md` section 7 contains the full source of `validate.py`. That is a good
idea, since it makes the contract self-contained. It also means the file on disk
and the file in the contract can drift, and after the fix above they had.

Anyone starting cold, pasting `PROMPT.md`, and regenerating `validate.py` from
section 7 would have reintroduced the bug without noticing.

The embedded block now matches the shipped file character for character. A check
worth running at the start of any session that edits either one:

```bash
python3 - <<'PY'
import re
block = re.findall(r"```python\n(.*?)```", open('PROMPT.md').read(), re.S)[0]
print("in sync:", block == open('validate.py').read())
PY
```

---

## Part 2. Proposals, all since decided and applied in schema 3.4

Each was a friction that showed up while writing real nodes. All six were put to
the owner and all six were accepted, so the descriptions below now read as the
rationale for what the schema does, not as open questions. `SESSION_LOG.md`
carries the change list.

### 1. There is no "is a kind of" relation

This is the one that actually bent the data.

`titan-head` is a kind of `carrier-head`. `sti-ceria-slurry` is a kind of
`slurry`. `tungsten-slurry-oxidizer` is a component of a slurry, which is
different again. The relation list offers `part_of`, `alias_of` and
`contrasted_with`, and none of them means "is a kind of".

What was written instead: `titan-head contrasted_with titan-profiler-head`, which
is true but sidesteps the link to the parent concept, and
`tungsten-slurry-oxidizer part_of slurry`, which is right. The `titan-head` to
`carrier-head` link was left out rather than written wrongly, because the reader
renders `part_of` in reverse as "contains", and "Carrier Head contains Titan
Head" reads backwards.

**Applied.** `variant_of` is in the relation list with the reader reverse label
"variants". Then `titan-head variant_of carrier-head` reads correctly in
both directions, and every head generation hangs off the general concept.

This will matter more, not less. Every consumable with an application-specific
version has the same shape.

### 2. `access` is the most important field in `sources.csv` and nothing checks it

Everything in this batch is `snippet-only`. That single word is what stops the
base from being over-claimed. But `access` is free text, so a typo silently turns
a caveat into nothing, and there is no rule connecting it to confidence.

**Applied, in two steps:**

- Controlled vocabulary: `read`, `snippet-only`, `paywalled`, `not-retrieved`,
  validated the same way `tier` is.
- A new check: if every source cited for a node's `mirra_application` field is
  `snippet-only` or `not-retrieved`, then `confidence_mirra=established` is an
  error. This is the machine-checkable version of the rule you already wrote in
  prose, that wanting it to be Mirra specific is not evidence.

### 3. `searches.csv` records the session but not the date

An empty result is only worth re-running after enough time has passed for the web
to change. Session number does not carry that. **Applied:** the column order is
now `session,date,query,where_run,outcome,note`, and the 21 existing rows are
dated 2026-09-05.

### 4. The `head_gen` warning has a hole

The check fires only when `domain` is `hardware`:

```python
if not hg and n.get("domain") == "hardware" and HEAD_WORDS.search(n["term"]):
```

A node about zone recipes in `controls`, or about edge profile in `process`,
matches `HEAD_WORDS` but escapes the warning. `zone-pressure-control` happens to
be tagged `hardware`, so it was caught. The next one may not be.

**Applied.** The domain condition is gone from both the validator and the reader.
The rule in section 2 is about the claim, not about the domain: "Never write a
head claim without head_gen."

### 5. Two fields are never checked at all, now they are

**Applied as warnings.** `applications` was not checked for being empty, and
`updated_session` was not checked at all. Both are easy to forget in a hand-edited row, and an empty
`applications` value silently drops the node out of every application filter in
the reader.

### 6. Batch size

**Applied to the contract as a cap.** 29 nodes in one batch was too many. The last few node files are noticeably
thinner than the first few, and that is a quality difference a future reader
cannot see from the CSV. Your own instruction of about 20 was right. The clean
domain being under-represented is not a good enough reason to stretch a batch,
because a thin clean node is not parity either.

### 7. Two structural observations, offered without a proposal

- **The empty `general` bucket.** Decided: split the pure physics out into
  general nodes in session 2, objective 4. Every node in this batch is `cmp` or `mirra`.
  Pure physics such as contact mechanics, fluid films and friction was folded into
  `cmp` nodes rather than given its own `general` nodes. That is defensible, but it
  means the specificity split currently understates how much of the base is
  ordinary engineering. Worth a deliberate decision rather than drift.

- **Contested was doing more work than its name suggests.** Resolved: all five
  sections were renamed and `## Weak sourcing` is now a mapped heading, so the
  contested count is 0 and means what section 2 says it means. Section 2 defines it as
  two credible sources disagreeing. Four of the five `## Contested` sections in
  this batch are not disagreements between sources. They are single-source claims
  where the source is weak or where a summary may have merged documents. That is a
  useful thing to record, but it is a different category, and counting it as
  contested hid the fact that nothing in this base has been challenged by a
  second source at all.

---

## Working notes, for whoever runs the next session

- Write the CSVs first, run `validate.py`, then write the prose. Errors in the
  structure are cheap to fix before 29 files reference it.
- Every node needs at least one edge and at least one citation or the validator
  warns. Plan the edges as you plan the nodes, not afterwards.
- Source ids must contain a hyphen or a dot, or the inline citation regex will not
  see them. `stg1997` is invisible. `stg-1997` works.
- The reader's Health tab earned its place: "resting on tier 4 or 5 only" found
  the weakest claim in the base immediately, which no amount of re-reading the
  prose would have surfaced.
- Serve the folder and load the reader before wrapping up. The Health numbers are
  the honest count and they belong in `STATE.md`.
