# Lessons learned

Things that went wrong, what they cost, and what to do instead. Written down
because every one of these is cheap to avoid once you know and expensive to
rediscover.

Add to this file when something costs you a day. Do not add things that merely
sound wise.

---

## Version control

### A long-lived session branch silently forks the project

Three commits, 1,977 insertions, written two weeks after `main` had moved on,
from a base that predated four releases. No pull request was ever opened. The
browser tool those commits were written against was 120 KB behind the real one
and knew nothing about category rules, the quick report, saved setups or any
vendor importer.

Packaging that checkout as "the project" would have shipped a fork and lost most
of the browser tool.

**Instead:** branch from `main`, open the pull request immediately even as a
draft, and rebase before every session. A branch nobody has proposed merging is
not work in progress, it is work in limbo.

### A partial fetch hides the trunk, and every local check then agrees with you

The checkout had only ever fetched two branches. There was no `origin/main` and
no tags, so `git log`, `git branch -a` and `alarm_pareto/__init__.py` all agreed
the project was at v1.0.0. It was at v1.4.0. Nothing was lying; the evidence was
simply absent, which is much harder to notice than evidence that is wrong.

**Instead:** on any unfamiliar checkout, run `git fetch --tags` and confirm
`git log --oneline -1 origin/main` resolves before believing anything local.
`docs/HANDOFF.md` makes this step one.

### Squash-merges make git report merged branches as unmerged

`git merge-base --is-ancestor` says no. `git diff main...branch` lists content
that looks unique to the branch. Both readings are artifacts of the squash, not
lost work.

**Instead:** compare files directly, `git diff branch main -- <path>`, and trust
the pull request state on GitHub. `ROADMAP.md` documents this under "Repo
housekeeping", which is where it was found after being rediscovered.

---

## Verifying

### Verify where you can, and say plainly where you cannot

PyPI was blocked for an entire stretch of work, so pandas could not be installed
and `pytest` never ran locally. CI on real pandas was the only honest gate. The
temptation was to write a pandas stand-in good enough to run the tests; that
would have tested the stand-in.

**Instead:** find the gate that runs real code, use it, and say in the commit and
the summary which checks did not run. An unrun test reported as passing is worse
than no test.

### Distinguish measured from estimated, in the document itself

The browser tool's memory and time limits in `README.md` were measured by running
the real parsing and aggregation code against generated logs of 100k to 4M rows.
The Python tool's were reasoned from the shape of the code. Both appear in the
same section, so the section says which is which.

**Instead:** when you cannot measure, label the number as an estimate where the
reader will see it, not in a commit message they will never read.

### Assert invariants, not coincidences

An `attributed >= in_range` assertion held on the sample and was written as a
test. It is not an invariant: a long fault starting before a quiet shift breaks
it. The sample later produced exactly that counterexample on second shift, where
in-range is larger than both other numbers.

**Instead:** prefer exact golden values to inequalities. An inequality can pass
for the wrong reason for a long time. When you do assert a bound, be able to say
why it must hold, not merely that it does today. The counterexample is now pinned
in both suites so nobody re-adds the assertion.

### A new test is not trustworthy until you have seen it fail

The cross-tool check passed the first time it ran, which proves nothing on its
own. Perturbing one golden value confirmed it goes red and names the exact case
and field.

**Instead:** mutate something and watch the test catch it. It takes a minute.

---

## Design

### Logic duplicated in two languages drifts, and discipline does not stop it

The browser tool and the Python tool implement the same analysis twice, with
fourteen near-literal translations between them. Agreement was enforced by one
sentence in `CONTRIBUTING.md`. They had already drifted twice: a backwards window
raises in Python and returns empty in JavaScript, and unreadable time input
raises in Python but silently disables the filter in the browser.

**Instead:** make agreement mechanical. `tests/data/cross_tool_golden.json` is
now read by both suites, so a change that moves one tool and not the other goes
red. A rule that relies on someone remembering is not a rule, it is a hope.

### A golden file generated from the code it checks proves nothing

It agrees with that code's bugs by construction.

**Instead:** derive golden values independently. The cross-tool numbers came from
a standalone script sharing no code with either tool, and the file says so in its
own header so nobody later "regenerates" it for convenience.

### Zero TODO markers make unfinished code look finished

There is not one `TODO`, `FIXME` or `XXX` anywhere in the tree. Everything
deferred lives in `ROADMAP.md`, so a developer grepping the source concludes,
wrongly, that nothing is pending.

**Instead:** this is a deliberate house style and it works, but only because
`ROADMAP.md` and now `docs/STATE.md` are kept genuinely current. If those go
stale the code becomes actively misleading. Keeping them current is the cost of
the style.

### The test that failed was right

Two new tiles were added to the results page. A test expecting four tiles on a
log with no downtime column went red. The easy fix was to change the number to
six; the correct fix was to notice that "0.0% of covered time down" implies the
tool was up, which is not known when no downtime was measured at all. The tiles
are now gated on there being real downtime data, and the test passes unchanged.

**Instead:** when an existing test fails on a new change, first ask what it knew
that you did not.

---

## Working with the tools

### Read the code before writing the integration, not after

A test harness helper was written against `parseDelimited`, `#durCol` and a
`data-col` attribute. None of the three exist in the current browser tool; all
were remembered from an older version of the file. Three failed runs to find out
what five minutes of reading would have said.

**Instead:** grep for the real identifiers first. This applies doubly to a file
that has grown a lot since you last saw it.

### Guessing at fixture numbers wastes more time than computing them

Six shift cases were drafted with plausible row counts. Three were wrong. A short
script computed all of them correctly in one pass, and turned up the second-shift
counterexample that became the most valuable case in the fixture.

**Instead:** compute expected values with a throwaway script rather than
reasoning them out, especially when the whole point of the fixture is to be
independently correct.
