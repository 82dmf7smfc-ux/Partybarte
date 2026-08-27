# Roadmap and future improvements

This file captures ideas for later work. It is a living list. Add to it as you
learn what the bench actually needs. Nothing here is a promise. It is a place to
keep good ideas so they are not lost between sessions.

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
- **Shared golden fixtures.** Put the sample log and its expected numbers in one
  place that both the Python tests and a browser self-test read. This proves the
  two tools agree, forever.

## Medium term

- **More vendor config blocks.** Add real column mappings as new tools come
  online. This is a JSON edit, not code.
- **Browser export to Excel.** Let the browser tool write a simple `.xlsx`
  summary. Note that native, clickable Excel charts still need the Python tool.
- **Reliability metrics.** Add mean time between failures and mean time to
  repair per fault and per module. These are common asks in tool health reviews.
- **Pareto knee callout.** Mark the fault where the cumulative line crosses 80
  percent, so the "vital few" are obvious at a glance.

## Longer term

- **Multi-tool comparison.** Compare the same fault across several tools of the
  same type to spot an outlier chamber.
- **Trend over time.** Show how a fault's rate changes week over week, not just
  a single window snapshot.
- **Packaging as a wheel.** Ship the Python tool as an installable wheel so IT
  approves one file, not a folder.

## Engineering hygiene

- Add a code formatter and a linter check to CI once the team agrees on a style.
- Add tests for the set/clear pairing path in the Python suite, to match the
  coverage the browser tool already exercises. The paired-interval path is now
  covered by the Picosun tests.
- Choose and add a license file. The project has none yet.
