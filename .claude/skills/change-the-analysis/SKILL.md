---
name: change-the-analysis
description: Change how faults are counted, how downtime is measured, how the window is applied, or how results are ranked. Use whenever a change would alter the numbers either tool reports, including bug fixes to the overlap merge, new downtime modes, timestamp parsing changes, and new metrics like mean time between failures. Also use when a reported number looks wrong.
---

# Changing the analysis

The analysis is written twice. Once in Python, once in JavaScript. A change to
one without the other makes the two tools disagree, and nobody notices until a
number is wrong in a tool health review.

This is the procedure. Follow it in order.

## 1. Find both copies

The same idea lives in two places. Common pairs:

| Idea | Python | JavaScript in `alarm_pareto.html` |
|---|---|---|
| Overlap merge | `aggregate.merged_seconds` | `mergedSeconds` |
| Ranking and top N | `aggregate.rank_level` | `rankLevel`, `collapse` |
| Window filter | `window.py` | `applyWindow` |
| Occurrence building | `normalize.py` | `buildOccurrences`, `makeOcc` |
| Timestamp parsing | `parse.py` | `parseDate` |
| Delimited parsing | `parse.py` | `parseDelimited`, `splitLine` |

Read both before editing either. They are written in different styles but they
must mean the same thing.

## 2. Decide what the right answer is, by hand

Work out the expected numbers for the sample log yourself, on paper, before
writing code. `tests/data/expected_summary.json` exists because the numbers were
derived by hand once. Keep that true.

If the change affects the sample log's numbers, write down the new expected
values and why they changed. You will need this in step 5.

## 3. Change both copies in the same commit

Never leave the tree with one side changed. If you cannot finish the second
side, revert the first.

Remember the two downtime numbers are different and must never be mixed:

- **Attributed.** Every alarm gets its own full duration. Ranks which fault
  costs the most.
- **Wall clock.** Overlapping alarms merge first, so shared time counts once.
  Answers how long the tool was really down.

## 4. Add a test that fails without the change

For a bug fix, the test must fail on the old code and pass on the new. Check
that. A test that passes either way proves nothing.

Put analysis tests in `tests/test_aggregate.py` or `tests/test_window.py`.

## 5. Run both checks

    node tools/check_parity.mjs      # the browser tool against the golden file
    python -m pytest -q              # the Python tool against the same file

Both must pass. If the parity check fails, the two copies disagree. Read its
output. It names the exact value and both numbers.

If Python packages are missing here, see the `offline-setup` skill. Do not skip
the Python side silently. Say that you could not run it.

## 6. Update the golden file only if you meant to

If the numbers changed on purpose, update `tests/data/expected_summary.json`
with the values you worked out in step 2, and say in the commit message why they
changed.

Never edit the golden file to make a red test go green. That is the one move
that destroys the value of this whole setup.

## 7. Record it

Add a line under "Unreleased" in `CHANGELOG.md`. If the change alters numbers
users have seen before, say so plainly, because someone has an old report on a
slide.
