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

Ask first only where the answer genuinely changes the work, or where the action
is destructive and not obviously implied by the request. Publishing a release is
a normal part of finishing, not a special escalation.

## How to verify a change

The browser harness is the fast gate and it runs anywhere:

    node tests/browser/run.mjs

It should report `138 passed, 0 failed` before any change, more after. It drives
real headless Chromium against `alarm_pareto.html` and uses only Node built-ins,
so there is nothing to install.

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
