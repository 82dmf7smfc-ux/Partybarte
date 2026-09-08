# Where the project actually stands

`CHANGELOG.md` records what shipped. `ROADMAP.md` records what is wanted. Neither
records what is half-done, what was decided and why, or what is waiting on
somebody. That gap is what this file fills, and it is the file to read first when
picking the project back up.

Keep it current the way `CHANGELOG.md` is kept current: as part of the change,
not afterwards.

Last updated: 2026-09-08, at the end of the reconciliation described below.

---

## The one thing to know before touching anything

**Work from `main`. Verify that with `git log --oneline -1 origin/main` before
you believe any local state.**

This project lost two weeks of trunk drift to a stale branch. A session working
in a checkout that had only ever fetched two branches could not see `main` or any
tag, so every local signal agreed the project was at v1.0.0 while `main` was at
v1.4.0. Three commits were written on that base, and the browser tool they were
written against was 120 KB behind. Packaging that checkout would have shipped a
fork and quietly lost most of the browser tool.

The clone on the new machine must be a full one:

    git clone https://github.com/82dmf7smfc-ux/Partybarte
    git fetch --tags

Never copy a working directory from one machine to another to move this project.

---

## Current state

`main` is at v1.4.0. Branch `claude/pareto-final-wave` carries the work below and
is not yet merged.

### What landed on `claude/pareto-final-wave`

1. **The time-of-day filter, both tools.** `--start-time` and `--end-time` on the
   Python tool; two time boxes and a shift preset in the browser tool. Half open,
   and a start later than an end wraps past midnight, which is what makes 18:00
   to 06:00 the night shift.

2. **A third downtime number, "in range", both tools.** New module
   `alarm_pareto/reporting_range.py`. It merges overlaps like wall clock, then
   cuts every fault down to the parts that land inside the hours the report
   covers. It is the only one of the three bounded by the clock, and the only one
   that splits correctly across shifts.

3. **Shared golden fixtures.** `tests/data/cross_tool_golden.json` is now the
   referee between the two tools. See "Decisions" below.

4. **Hygiene.** `pyproject.toml`, a dev/runtime requirements split,
   `.editorconfig`, `setup_venv.sh`, fixes to `setup_venv.bat`, CI concurrency
   and pip caching, a release-target fix, `.claude/settings.json`, and a
   `.gitignore` guard against committing real logs.

5. **These handoff documents.**

### Verified how

- `node tests/browser/run.mjs` — 377 passed, 0 failed. Runs anywhere Node and
  Chromium exist, including this locked-down environment.
- `python3 tools/check_version.py` — passes; now also covers `pyproject.toml`.
- CI on GitHub, Python 3.11 and 3.12, real pinned pandas — green on the Python
  port commit.
- The cross-tool check was mutation-tested: perturbing one golden value turns it
  red and names the case and field.

**`pytest` was never run locally.** PyPI is blocked from the environment this
work was done in, so pandas could not be installed at all. CI was the only gate
on the Python suite. On the new machine, run `python -m pytest -q` and treat the
first run as genuinely new information.

---

## Tasks still needed

In the order they should be done.

### 1. Open the pull request and merge `claude/pareto-final-wave`
Nothing else should be built on top of it until it lands. It has never been
reviewed.

### 2. Mirror derived downtime in the Python tool — **not started**
The browser tool can estimate downtime by pairing "down" and "up" messages per
chamber. The Python tool cannot. This is the largest remaining behavioural gap
between the two tools, and the cross-tool fixture cannot cover the derive mode
until it exists.

What it needs: port the pairing state machine, share the phrase and chamber-name
lists, and cover the tool-level "restricted" (any chamber down) and "full down"
(all chambers down) numbers with unit tests. Then extend
`tests/data/cross_tool_golden.json` with derive-mode cases.

### 3. Excel import in the browser tool — **not started**
Many elogs are native `.xlsx` and today need exporting to CSV first. No library
and no build step is required, which is what keeps the single-file rule: an
`.xlsx` is a ZIP of XML, and browsers provide `DecompressionStream("deflate-raw")`
natively. Walk the ZIP central directory, then `DOMParser` over
`sharedStrings.xml` and the sheet XML. `ROADMAP.md` estimates a few hundred
lines. Scope it before starting.

### 4. Category rules batch 3 — **blocked on the owner**
The 7,324-row etch log is still untouched. It is a third tool and will bring its
own tail. Expect some of the existing 67 rules to need widening, the way
`temperature deviation` did once a second tool worded the same fault differently.

**This needs you to send the debug uncategorized worklist and the real elog rows,
as pictures.** Nothing can start without them. See `docs/CATEGORY_RULES.md`.

### 5. Smaller things, none blocking
- Add tests for the set/clear pairing path and the paired-interval path in the
  Python suite. `ROADMAP.md` has wanted these for a while; the browser tool
  already exercises them.
- Turn on a ruff job in CI. `pyproject.toml` now carries the configuration, but
  no workflow runs it, deliberately: turning it on will surface findings across
  files this change did not touch, and that belongs in its own commit.
- Two owner-only GitHub settings that a session cannot change: "Automatically
  delete head branches" and auto-merge, both under Settings, General, Pull
  Requests. Twenty-six branches have accumulated, most already merged.

---

## Decisions, and why

Recorded so they are not re-litigated or quietly reversed.

**The three downtime numbers are never mixed, and there are exactly three.**
Attributed credits each fault its whole duration. Wall clock merges overlaps but
still counts a fault against the hours it started in. In range merges overlaps
and also cuts each fault to the covered hours. If a fourth is ever added, say on
the page and in the docs what question it answers that the others do not.

**In-range downtime is measured from the rows before the window and the shift,
but after the severity and category filters.** It follows the clock rather than
the fault onset: a fault that began before a shift started still had the tool
down during that shift. The filters are the reader's intent rather than the
reporting range, so a report filtered to one chamber stays filtered in every
column. Do not "simplify" this to use the windowed rows; it silently loses every
fault that straddles a boundary.

**In-range is not bounded by the other two numbers.** On second shift in the
sample it is larger than both, because a fault that started at 12:00 was still
running at 14:00. Both suites pin that case so nobody adds an
`in_range <= wallclock` assertion, which would pass on most of the sample and be
wrong. It is bounded by the clock and by nothing else.

**The time-of-day range is half open, and wraps.** The start minute is kept and
the end minute is not, which is what makes two shifts add up to one day with
nothing counted twice and nothing lost. A start later than an end wraps past
midnight. Fab shifts cross midnight, so this is the normal case, not an edge one.

**The golden fixture is never regenerated from either tool.** Its numbers came
from a standalone script sharing no code with either implementation. A golden
file produced by the code it checks agrees with that code's bugs by construction.
When a number genuinely must change, change it by hand and say in the commit why
the old one was wrong.

**`.claude/settings.json` was written by a session, against `ROADMAP.md`'s rule.**
That rule says the permission allowlist is an owner job, because a session
writing it is a tool widening its own permissions. The owner was shown the rule
and chose to overrule it for this change. Recorded here so the exception is
visible rather than looking like the rule was missed.

---

## Open questions

None of these block the work above.

1. Which git identity should commits use? This machine's local git config
   attaches a real name and address; `main`'s history is authored under an Apple
   private relay. Set it deliberately before the first commit on a new machine.
2. Should `claude/pareto-debugging-ajyqf1` be deleted now that its work is on
   `claude/pareto-final-wave`, or kept as a record of the fork?
3. Is "Applied Materials" in `alarm_pareto/config/vendor_columns.json`
   acceptable, or should vendor names be genericised? It is a tool vendor, not a
   customer or fab, so the current reading is that it is fine.
4. Both vendor blocks in that config are self-declared placeholders. Is there a
   real column mapping to add? First real use on a new machine will need one.
5. Should Python 3.13 be added to the CI matrix? It cannot be until numpy and
   pandas are unpinned, and the pins are deliberate.
6. Should PR #32, the Mirra CMP knowledge base, land before or after this wave?
   It targets a stale base and will need rebasing onto `main` either way.

---

## Things that are not what they look like

- **Squash-merges make `git` lie about mergedness.** `git merge-base
  --is-ancestor` reports merged branches as unmerged, and `git diff main...branch`
  lists content that looks unique but is not. Compare files directly
  (`git diff branch main -- <path>`) and trust the pull request state on GitHub.
  `ROADMAP.md` documents this too, under "Repo housekeeping".
- **Other projects live on other branches.** `magnet-course`, `mirra-kb`,
  `projects/`, and an offline PM logger all exist on side branches of this same
  repository. `main` is Pareto-only. Do not be alarmed by unrelated files in a
  branch listing.
- **The repository has no GitHub issues.** `ROADMAP.md` is the backlog of record.
