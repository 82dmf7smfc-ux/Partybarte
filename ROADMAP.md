# Roadmap and future improvements

This file captures ideas for later work. It is a living list. Add to it as you
learn what the bench actually needs. Nothing here is a promise. It is a place to
keep good ideas so they are not lost between sessions.

## Done

These were on the list and are now in place. They are kept here so the history
of the list makes sense.

- **Shared golden fixtures.** `tests/data/expected_summary.json` and
  `tests/data/expected_setclear.json` now govern both tools.
  `tools/check_parity.mjs` runs the real browser code and compares it to the
  same numbers the Python tests use. See `docs/claude-system.md`.
- **Tests for the set/clear pairing path and the paired-interval path.** See
  `tests/test_pairing.py`.
- **The ranking itself is checked, not just the totals.** Order, percent,
  cumulative percent and the "Other" bucket are compared between the two tools.
  See `tests/test_ranking.py`.

## Guiding goals

- Keep both tools fully offline. No network calls at runtime.
- Keep the browser tool a single file with no install.
- Keep the analysis math identical between the browser tool and the Python tool.
- Keep the code plain enough for a non-programmer to follow.

## Near term

- **Read Excel files in the browser tool.** Today the browser tool reads CSV and
  delimited text. Many elogs are native `.xlsx`. Add a small offline parser so
  those import directly, with no export step.
- **Remember column mappings.** Save the mapping per tool in the browser using
  local storage, so a repeat import needs no setup.
- **More timestamp formats.** Add any date styles that real tools use but the
  current parser misses. Each new format is a small, safe addition.

## Medium term

- **More vendor config blocks.** Add real column mappings as new tools come
  online. This is a JSON edit, not code.
- **Browser export to Excel.** Let the browser tool write a simple `.xlsx`
  summary. Note that native, clickable Excel charts still need the Python tool.
- **Reliability metrics.** Add mean time between failures and mean time to
  repair per fault and per module. These are common asks in tool health reviews.
- **Pareto knee callout.** Mark the fault where the cumulative line crosses 80
  percent, so the "vital few" are obvious at a glance.

## Known differences between the two tools

Written down so nobody rediscovers them the hard way. Neither is fixed, because
fixing either changes numbers users have already seen.

- The browser tool has no paired-interval mode. It handles a duration column or
  separate set and clear rows, and nothing else.
- The window is applied at a different point. Python filters raw rows and then
  pairs set and clear rows. The browser tool pairs first and then filters. On a
  log where a set falls outside the window and its clear falls inside, the two
  would disagree. Nothing has hit this yet, and no fixture covers it.

## Longer term

- **Multi-tool comparison.** Compare the same fault across several tools of the
  same type to spot an outlier chamber.
- **Trend over time.** Show how a fault's rate changes week over week, not just
  a single window snapshot.
- **Packaging as a wheel.** Ship the Python tool as an installable wheel so IT
  approves one file, not a folder.

## Engineering hygiene

- Add a code formatter and a linter check to CI once the team agrees on a style.
- Choose and add a license file. The project has none yet.
