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
  those import directly, with no export step. This does not need a bundled
  library and does not break the single-file rule: an `.xlsx` is a ZIP of XML,
  and browsers provide `DecompressionStream("deflate-raw")` natively. So the
  work is a walk of the ZIP central directory, then `DOMParser` over
  `sharedStrings.xml` and the sheet XML. Scope it before starting; the estimate
  is a few hundred lines.
- **Remember column mappings.** Save the mapping per tool in the browser using
  local storage, so a repeat import needs no setup. The scaffolding is already
  there: a persistence helper near the top of the settings code takes an
  `{id, key, seed}` entry and today backs `ap_cat_rules` and `ap_module_names`.
  Key the saved mapping by the detected tool, so a dep log and an etch log each
  recall their own. The down/up phrase lists, chamber names, and filters are
  also unsaved today and could ride along.
- **More timestamp formats.** Add any date styles that real tools use but the
  current parser misses. Each new format is a small, safe addition.
- **Shared golden fixtures.** Put the sample log and its expected numbers in one
  place that both the Python tests and a browser self-test read. This proves the
  two tools agree, forever.

## Medium term

- **Mirror derived downtime in the Python tool.** The browser tool can now
  estimate downtime by pairing down and up messages per chamber. The Python tool
  should grow the same mode, sharing the phrase and chamber-name lists, so both
  tools agree. Cover it with unit tests for the state machine and the tool-level
  restricted and full-down numbers.
- **More vendor config blocks.** Add real column mappings as new tools come
  online. This is a JSON edit, not code.
- **Browser export to Excel.** Let the browser tool write a simple `.xlsx`
  summary. Note that native, clickable Excel charts still need the Python tool.
- **Reliability metrics.** Half of this shipped in 1.4.0: the Insights card
  reports mean time between failures, both tool-level and per chamber, as the
  "mean gap between events". What is left is mean time to repair, and breaking
  both numbers out per fault as well as per module.
- **Pareto knee callout.** Mark the fault where the cumulative line crosses 80
  percent, so the "vital few" are obvious at a glance.

## Longer term

- **Multi-tool comparison.** The groundwork shipped in 1.4.0: a P5000 elog is
  tagged with the tool it came from, there is a Tool column, a Tool Pareto
  level, and a Tool filter, so a dep log and an etch log can be loaded together
  and read side by side. What is left is the judgement call on top of that data,
  which is flagging the outlier automatically rather than leaving it to the eye.
- **Trend over time.** Show how a fault's rate changes week over week, not just
  a single window snapshot.
- **Packaging as a wheel.** Ship the Python tool as an installable wheel so IT
  approves one file, not a folder.

## Engineering hygiene

- Add a code formatter and a linter check to CI once the team agrees on a style.
- Add tests for the set/clear pairing path and the paired-interval path in the
  Python suite, to match the coverage the browser tool already exercises.

## Repo housekeeping

- **Stale branches, safe to delete.** Every feature branch below is fully merged
  into `main` and is kept only because nobody has swept them up yet. None is a
  base for an open pull request, and none affects CI or a release. Deleting them
  loses nothing. GitHub's "Delete merged branches" button on the Branches page
  clears the lot in one pass.
  - `claude/add-license`
  - `claude/html-elog-severity-idtext`
  - `claude/html-start-row-headerless`
  - `claude/new-session-5e2w1d`
  - `claude/p5000-etch-importer-h20brt`
  - `claude/partybarte-downtime-estimation-3vxd16`
  - `claude/reconcile-release-workflow`
  - `claude/release-v1.3.0-stamp`
  - `claude/pareto-html-recovery-i3xa1i` — this one is not merged, it is an
    abandoned pre-recovery snapshot. Its one unique commit only enables manual
    dispatch on the release workflow, which `main` already has. Treat it as
    stale, not as work in progress.
