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

- **Grow the category rules from real logs.** In progress, and the current arc.
  The owner sends the debug uncategorized worklist and real elog rows; those
  become category rules, so a log lands on named faults instead of labels the
  tool invented from the message text. `docs/CATEGORY_RULES.md` is the working
  guide: precedence, how to write a rule that survives a chamber tag change,
  where each piece lives, and what finishing a batch means.

  Why it is worth doing: on a real 7,324-row etch log, two built-in rules covered
  about 73% of the events and the whole tail below them read `auto: message
  shape` - a row per wording rather than a row per fault. Every rule added turns
  a scatter of near-duplicates into one bar somebody recognises.

  **Batch 1 shipped**, from a 5,158-row P5000 etch3 log that started at
  `categorized 4233 of 5158 (82%)`. Its worklist listed `top 59 of 59 distinct`,
  so the whole tail was in frame and all 59 got a rule - forty-nine new
  `BUILTIN_CAT_RULES`, four wordings folded onto labels that already existed, and
  a test per rule against the transcribed message. What is left: the same pass on
  the 7,324-row log, which is a different tool and will have its own tail, and
  whatever batch 1 got wrong - a mis-transcribed pattern shows up as a rule that
  never matched on the owner's re-run, not as a wrong label. Rules were appended
  rather than interleaved, so no already-categorized event changed name.

  **Batch 2 shipped**, from a 26,414-row k34 Endura log at
  `categorized 26014 of 26414 (98%)`, worklist `top 35 of 35 distinct`. Sixteen
  of those 35 were events batch 1 already covers, so only eighteen needed new
  rules; one batch-1 rule was widened after the second tool worded the same
  fault differently (`temperature deviation fault` against `warning`). That is
  the lesson worth keeping: the risk in a single-log batch is not only a misread
  character but a wording that looks invariant until a second tool disagrees.
  What is left: the 7,324-row log, still untouched, and confirming both batches
  against a re-run.

  Two related things to pick up while in here, both deliberately left alone until
  there is real data to judge them on:
  - The down/up phrase lists for derived downtime are Applied Materials wording.
    Real phrasings from other tools would widen the defaults so the quick report
    recognises more logs unprompted.
  - On that same etch log, 41% of events carried no chamber tag and showed as
    `(unknown)`. The full report has a "System" bucket for tag-less events, and
    the module-name list can read a subsystem out of the message text. Whether
    the quick report should apply either by itself is an open question: it
    changes what a large slice of the data is called, so it needs the owner's
    say-so and a sentence in the note if it ever happens.

- **Quick report and full report.** Shipped, and since tuned on real logs. The
  browser tool opens as a quick report - import, Analyze, results - and a switch
  opens the full tool. The three things left after the first pass are all done:
  - The results table drops the "Attributed (h)" and "Wall clock (h)" columns in
    the quick report when the log has no downtime, the same as the zero tiles
    and the empty chart. Done.
  - The print stylesheet gives the quick report a one-page hand-out: the
    summary, the ranked table, and the Pareto, with every control off the paper.
    Done.
  - The quick report can now pick "Derive from messages", but only when the
    default phrase lists genuinely pair up in the file. Done, and deliberately
    cautious: a wrong guess here invents downtime rather than omitting it, so
    the pairing is run first and derive is taken only if pairs actually close.

  What is left is wording, not machinery: the default down and up phrase lists
  are Applied Materials wording. A tool whose elog says something else still
  needs the phrases typed once in the full report, after which the saved setup
  recalls them. Worth collecting real phrasings from a few more tools and adding
  the common ones to the defaults, so the quick report recognises more logs
  without being told.

- **Read Excel files in the browser tool.** Today the browser tool reads CSV and
  delimited text. Many elogs are native `.xlsx`. Add a small offline parser so
  those import directly, with no export step. This does not need a bundled
  library and does not break the single-file rule: an `.xlsx` is a ZIP of XML,
  and browsers provide `DecompressionStream("deflate-raw")` natively. So the
  work is a walk of the ZIP central directory, then `DOMParser` over
  `sharedStrings.xml` and the sheet XML. Scope it before starting; the estimate
  is a few hundred lines.
- **Remember column mappings.** Shipped. The browser tool saves the whole setup
  per tool: the column roles, the downtime mode and its settings, the down/up
  phrase lists, the chamber names, and any filter boxes left unticked. A P5000
  elog is filed under the tool name from its preamble, so a dep log and an etch
  log each recall their own; a delimited export names no tool, so it is filed
  under its column layout instead. What is left: the category rules and the
  module names are still saved once for every tool, under `ap_cat_rules` and
  `ap_module_names`. Those are vendor wording as much as the phrase lists are,
  so they are the obvious next thing to move per tool. Doing it needs a way to
  carry the lists a user has already typed into the first tool they open, or
  they will look lost.
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

- The browser suite checks its own paperwork: the run ends by comparing the test
  count quoted in `CLAUDE.md` against the count it just reported, and fails if
  they differ. The number had gone stale twice. The same idea would suit anything
  else a session is expected to remember to update by hand.

- Add a code formatter and a linter check to CI once the team agrees on a style.
- Add tests for the set/clear pairing path and the paired-interval path in the
  Python suite, to match the coverage the browser tool already exercises.
- **Turn on "Automatically delete head branches"** in Settings -> General ->
  Pull Requests. It clears merged branches without anyone having to remember,
  which is what the housekeeping list below exists to work around. A session
  cannot do this; the permission classifier refuses branch deletion.
- **Turn on auto-merge** so a pull request lands itself once the checks pass.
  Also an owner-only setting.
- **Add a permission allowlist** at `.claude/settings.json` so routine git
  commands stop being refused mid-task. A session should not write this file
  itself, because that is a tool widening its own permissions, so it stays an
  owner job. The list wanted is `git add`, `commit`, `push`, `fetch`,
  `checkout`, `branch`, `tag`, `merge`, `rebase`, plus
  `node tests/browser/run.mjs` and `python3 tools/check_version.py`.

### Automation already in place

Recording these so nobody rebuilds them or works around them by hand:

- **The release cuts itself from the changelog.** Landing a heading like
  `## [1.4.0] - 2026-08-17` on `main` triggers `release-on-stamp.yml`, which
  publishes that version, tag and zips included. It is a no-op when the release
  already exists, so ordinary changelog edits are safe. Stamping and publishing
  used to be two steps and the second kept getting dropped.
- **The version numbers are guarded.** `tools/check_version.py` asserts that the
  newest changelog heading matches `__version__`, and runs as a `version-check`
  CI job on every push. It uses the standard library only, so it also runs in a
  container with no network. The release workflow runs it again before
  publishing, so a release cannot go out under a half-true number.
- A note on why `release-on-stamp.yml` calls the release workflow instead of
  pushing a tag: a tag pushed with the built-in `GITHUB_TOKEN` does not start
  other workflows. The obvious "push the tag and let the tag trigger it"
  approach fails silently and looks like it worked. Do not simplify it back.

## Repo housekeeping

- **Stale branches, safe to delete.** Each branch below shipped through a pull
  request that has been merged. None is a base for an open pull request, and
  none affects CI or a release.
  - `claude/add-license`
  - `claude/html-elog-severity-idtext`
  - `claude/html-start-row-headerless`
  - `claude/new-session-5e2w1d`
  - `claude/p5000-etch-importer-h20brt`
  - `claude/partybarte-downtime-estimation-3vxd16`
  - `claude/reconcile-release-workflow`
  - `claude/release-v1.3.0-stamp`

  A warning about how to check this, because plain `git` will mislead you here.
  These pull requests were squash-merged, so the commit on `main` has a
  different hash and a different parent than the branch tip it came from.
  That makes `git merge-base --is-ancestor` report four of these branches as
  "not merged", and it makes `git diff main...branch` list content that looks
  unique to the branch. Both readings are artifacts of squash-merging, not lost
  work. Compare the files directly (`git diff branch main -- <path>`) and `main`
  turns out to be strictly ahead in every case. The honest signal is the pull
  request state on GitHub, which is what the Branches page uses when it offers
  to delete a merged branch.
