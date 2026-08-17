# Working notes for Claude

This file is read automatically at the start of every session. It exists so the
same questions do not get re-asked, the same traps do not get re-discovered, and
the owner does not have to hand-hold routine steps.

## Who finishes the work

Finish the job. Do not stop at the edge of a task and hand back a decision that
the task itself implies.

- **Open the pull request.** If the work is on a branch and it is ready, open the
  PR. Do not push a branch and ask whether a PR is wanted.
- **Cut the release.** If the changelog has been stamped with a new version and
  it is on `main`, cut that release (Actions -> Release -> Run workflow, or push
  the tag). A stamped changelog with no release is an unfinished job.
- **Keep the version numbers together.** `__version__` in
  `alarm_pareto/__init__.py`, the newest heading in `CHANGELOG.md`, and the git
  tag are one fact in three places. When one moves, move all three. These drifted
  once already, with the package reading 1.0.0 while the repo had tagged 1.3.0.
- **Sweep up after yourself.** Once a PR is merged, its branch is rubbish. Delete
  it if permitted; if not, leave it and move on rather than asking about it.
- **Update the record in the same commit as the change.** Writing down what
  happened is part of the work, not a separate errand to be asked for. Every
  change to the browser tool touches some of these, and the change is not
  finished until it has:
  - `CHANGELOG.md`, under Unreleased, in plain prose about what a person can now
    do. Check the diff is purely additive.
  - `ROADMAP.md`, if the change ships or moves a backlog item. Edit the entry to
    say what shipped and what is left, rather than deleting it.
  - `docs/DEBUG_CODES.md`, for any new debug code.
  - `README.md`, if the change alters what a user does or sees.
  - this file, for the test count and for anything a future session would
    otherwise have to work out again from scratch.

  The last one is the easiest to skip and the most expensive to skip. A trap that
  cost an hour and was not written down will cost another hour.

Ask first only where the answer genuinely changes the work, or where the action
is destructive and not obviously implied by the request. Publishing a release is
a normal part of finishing, not a special escalation.

## How to verify a change

The browser harness is the fast gate and it runs anywhere:

    node tests/browser/run.mjs

It should report `259 passed, 0 failed` before any change, more after. It drives
real headless Chromium against `alarm_pareto.html` and uses only Node built-ins,
so there is nothing to install.

That number is checked by the suite itself, at the end of the run, against this
file. If it does not match, the run fails and says so. Update the line above as
part of the change that moved it, the same way a new debug code is registered as
part of the change that emits it.

**Look at the page, not only at the DOM.** The harness asserts on ids and values,
and there is a whole class of fault it cannot see. A mode switch shipped with its
active button drawn dark blue on the dark blue header, so the *inactive* button
looked selected; every assertion passed. Another change left the previous mode's
rendering on screen after a flip; every assertion passed. Both were obvious in a
screenshot and invisible to the tests.

So for any change to layout, colour, or what is shown when, drive the same
headless Chromium over CDP, call `Page.captureScreenshot` with
`captureBeyondViewport: true`, and read the image. It is about forty lines of
Node using only built-ins, the same plumbing `tests/browser/run.mjs` already
uses. Then write the test for whatever the picture caught.

**The version check does run here.** `python3 tools/check_version.py` is standard
library only, so unlike the test suite it works in the container. Run it after
any edit to `CHANGELOG.md` or `alarm_pareto/__init__.py`.

**The Python suite cannot run in the remote container.** There is no PyPI access,
so neither `pytest` nor `pandas` can be installed, and `pandas` is what the suite
actually needs. This is settled: do not spend time trying to work around it, and
do not switch test frameworks hoping to dodge it. CI runs the Python suite on
3.11 and 3.12 on every push, and the release workflow runs it again before
publishing. That is the gate. Say plainly in any summary that the Python suite
was covered by CI rather than locally.

## Rules the tools must keep

- `alarm_pareto.html` stays a single self-contained file. No CDN, no bundled
  library, no build step, no network calls at runtime. It has to open from a USB
  stick on a locked-down bench machine.
- The analysis math stays identical between the browser tool and the Python tool.
  If one grows a mode, the other owes the same mode.
- The code stays plain enough for a non-programmer to follow. Clever is worse
  than obvious here.
- Anything changed in the browser tool earns coverage in `tests/browser/run.mjs`.
- New debug codes go in `docs/DEBUG_CODES.md`. The harness asserts that every
  code the tool emits is listed, so a missing entry fails the build.
- The page has two modes, a quick report and a full report. A mode hides cards
  with a class on `<body>` and rules in the stylesheet, never by deleting them.
  Every element stays in the DOM in both modes, so the pure functions and the
  harness go on reaching everything. Keep it that way: hiding by removal would
  break dozens of tests and buy nothing.
- Anything the quick report decides on the reader's behalf, it says on the page.
  It hides the controls, so a guess it does not confess to is a guess nobody can
  catch. If a new automatic decision is added, add its sentence to the note.

## Traps that have already cost time

**Git ancestry lies about merged branches.** The pull requests here are
squash-merged, so the commit on `main` has a different hash and a different
parent than the branch tip it came from. `git merge-base --is-ancestor` will
call merged branches unmerged, and `git diff main...branch` will invent content
that looks unique to the branch. Both are artifacts. Compare the files directly
with `git diff branch main -- <path>` before concluding anything is unmerged, and
trust the pull request state on GitHub over local ancestry.

**Branch deletion is blocked.** The permission classifier refuses `git branch -d`
and `git push origin --delete`. There is no delete-branch tool in the GitHub MCP
server either. Do not keep probing at it. Note the branch as stale and carry on;
the owner clears them from the Branches page.

**Editing the changelog eats the heading below it.** Writing a new Unreleased
entry by replacing the `## [Unreleased]` block is easy to get wrong: the
replacement drops the `## [1.4.0] - ...` heading underneath, which silently folds
a released section back into Unreleased. That happened, and the only thing that
caught it was `tools/check_version.py` failing in CI, reading 1.3.0 from the
changelog against 1.4.0 in the package. Run that script locally after any
changelog edit, and check `git diff` on `CHANGELOG.md` is purely additive.

**A browser test that writes to storage must clean up after itself.** Local
storage on a `file://` page survives between runs of the harness, so a test that
saves a setup or a mode leaves the next run in a different starting state. The
storage tests clear every `ap_setup_` key and `ap_mode` at both ends for exactly
this reason, and the "page opens in the quick report" check depends on it. Run
the suite twice after touching those tests; a pass followed by a fail is the
signature.

**`style.display` lies about a mode-hidden card.** Modes hide with a stylesheet
rule, so an element's inline `style.display` can still read `""` while nothing is
on screen. Tests must ask `getComputedStyle(el).display` instead. The harness has
a `__shown(id)` helper for this.

**Two rankings of the same rows shared their working.** `rankLevel` builds
`byCount` and `byDown` from one array of group objects. `arr.slice()` copies the
array but not the objects, so `collapse` writing `rank`, `pct` and `cum` on the
second pass overwrote what the first pass wrote: the "Count %" and "Cum %"
columns and the Pareto's cumulative line were showing downtime shares, which are
all zero when a log has no downtime column. `collapse` now works on copies. The
lesson is the general one - a function that stamps fields onto rows must own
those rows - and the way it was caught is the point: every DOM assertion passed,
and it took looking at a screenshot to notice the cumulative line of a Pareto
chart lying flat along the bottom.

**Hiding a container is not hiding what it opens.** The mode rules hid
`#debugSection`, which is only the "Show debug log" button. The panel it opens,
`#debugCard`, is its *sibling*, so an opened debug log stayed on screen in the
quick report with no way to close it - its toggle had just been hidden. The test
asserted on `#debugSection` and passed throughout. Before trusting a mode rule,
list what is actually on screen rather than what the rule names: walk
`main > *` and `.card` and ask `getClientRects().length > 0` for each. That audit
is a few lines and it settles the question for every card at once.

**A red CI job is not always a red change.** `browser-actions/setup-chrome` has
failed with 429 and 503 while downloading the action, before a single test ran.
The same job passed on the same commit in the parallel run. Read the log before
diagnosing: if it died in setup, re-run the failed jobs and move on.

**Stack a follow-up rather than waiting.** When a PR is open and the next arc
builds on it, branch from that branch and open the new PR with the open branch as
its base. The diff stays honest, and GitHub retargets the follow-up to `main`
when the first one merges. Say the merge order in the PR body.

**An autonomous session needs a stop condition.** A previous session shipped
"one more feature" for three hours past the point the work was merged, driven by
a self-re-arming check-in. If a session is running unattended, state up front
what done looks like. Do not judge mergeability from GitHub's combined commit
status in this repo: it reads `pending` forever because the repo uses check runs,
which is exactly what can drive an endless re-arm loop. Use check runs.

## Where things live

- `ROADMAP.md` is the backlog of record. There are no GitHub issues in this repo.
  When an item ships, edit the entry to say what shipped and what is left rather
  than deleting it outright, so the history of a decision survives.
- `CHANGELOG.md` follows Keep a Changelog. Write entries in plain prose describing
  what a person can now do, not what the code does internally.
- `docs/DEBUG_CODES.md` is the registry the harness checks against.
