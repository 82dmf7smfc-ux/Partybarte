# How Claude works on this project

This project carries its own working agreement for Claude Code. This file
explains what is set up, why each piece exists, and how to move the same setup
to another project.

The short version. Rules that live only in a document get followed most of the
time. Rules that live in a hook get followed every time. This setup moves the
rules that matter from prose into code.

## What is set up

    CLAUDE.md                       the rules, read at the start of every session
    .claude/settings.json           wires the hooks up
    .claude/hooks/session_start.sh  reports what this machine can verify
    .claude/hooks/guard_edit.py     blocks edits that break a hard rule
    .claude/hooks/verify_stop.py    runs the checks before the session ends
    .claude/skills/                 step by step procedures for recurring jobs
    tools/browser_core.mjs          loads the browser code so it can be tested
    tools/browser_summary.mjs       runs the browser analysis, prints JSON
    tools/check_parity.mjs          compares the browser tool to the golden files

## The four layers

### Layer 1. Context, in `CLAUDE.md`

Claude reads this at the start of every session. It holds the things that are
true about this project but invisible in the code: that the tools must run
offline, that packages need IT approval, that the browser file must stay
self-contained, that the analysis exists twice and both copies must agree.

Without this, a helpful assistant adds a charting library from a content
delivery network and breaks the one thing that makes the tool usable on a bench.

### Layer 2. Enforcement, in `.claude/hooks/`

Context can be forgotten in a long session. Hooks cannot. They run every time,
outside the model's judgment.

**`guard_edit.py`** runs before every file write. It blocks four things
outright, because each one makes the tool unusable rather than merely untidy:

1. Anything that reaches the network in shipped code. No `requests`, no
   `urllib`, no `fetch`, no remote URL.
2. Any import outside the approved package list.
3. Any outside reference in `alarm_pareto.html`. No script tag with a `src`, no
   outside stylesheet, no font from a content delivery network.
4. Any dependency in `requirements.txt` that is not pinned to one exact version.

It also notes style problems, such as an em dash, without blocking. That split
is deliberate. A hook that blocks on everything gets ignored or removed.
Comments are stripped before the code is checked, so a URL in a comment is fine
while a URL in code is not.

**`session_start.sh`** runs when a session begins. It reports whether Python,
the required packages, and Node are actually present, and says what to do in
each case. Sessions start on a fab laptop with no internet, in a cloud container
with nothing installed, and on a fully set up machine. Claude used to discover
which one it was in by failing halfway through a task.

**`verify_stop.py`** runs when Claude is about to finish. If any analysis file
changed, it runs the parity check and the test suite. If something fails, Claude
is sent back to fix it rather than leaving a broken change in the tree. It
blocks at most once, so a check that cannot pass does not loop forever. It also
notices when the analysis changed but the changelog did not.

### Layer 3. Procedures, in `.claude/skills/`

A skill is a set of steps that loads when the work matches its description.

| Skill | Loads when |
|---|---|
| `change-the-analysis` | anything that would change a reported number |
| `add-vendor` | a new log format, or a wrong column mapping |
| `offline-setup` | packages are missing or pip cannot reach an index |
| `cut-a-release` | tagging, shipping, or building the packages |

`change-the-analysis` is the important one. It carries the rule that both copies
of the math change together, that expected numbers are worked out by hand first,
and that the golden file is never edited to turn a red test green.

### Layer 4. The parity harness, in `tools/`

This is the part that is real engineering rather than configuration, and it
closes the largest hole in the project.

The analysis is written twice. Roughly a thousand lines of Python, and about
nine hundred lines of JavaScript inside `alarm_pareto.html`. They must produce
the same numbers. Until now nothing checked that. The two could drift apart for
months and the only symptom would be a wrong number on a slide.

`tools/browser_core.mjs` reads the single `<script>` block out of the HTML file,
gives it a small stand-in for a browser page, and runs it on plain Node. Nothing
is copied and nothing is rewritten, so the check cannot go stale. If someone
edits the math in the HTML, the check sees the edit.

`tools/check_parity.mjs` then runs the real browser code over the sample logs and
compares every number to the same golden files the Python tests use. That means
the group totals, and also the ranking itself: the order rows appear in, the
percent each carries, the running cumulative percent, and the "Other" bucket
that holds everything past the top N. Comparing only the totals would miss the
part of the output people actually read. Run it with:

    node tools/check_parity.mjs

It needs no packages and makes no network call.

It also checks something easy to miss. `alarm_pareto.html` carries its own copy
of the sample log in `SAMPLE_CSV`. If that copy drifts from
`tests/data/sample_alarm_log.csv`, the two tools are quietly analysing different
data. The check compares them.

## One golden file governs both tools

This is the idea that ties the setup together, and it was already on the roadmap
as "shared golden fixtures".

    tests/data/expected_summary.json    <- Python tests and the browser tool
    tests/data/expected_setclear.json   <- Python tests and the browser tool

The numbers in these files were worked out by hand. Both tools are measured
against them. Neither tool is the reference for the other, which matters,
because if one were the reference, a bug in it would become the specification.

Each golden file carries a `_by_hand` note explaining how its numbers were
derived, so the next person can check the reasoning rather than trusting it.

## What is known to differ between the two tools

These are real differences, not bugs found and left. They are written down so
nobody rediscovers them the hard way.

1. **The browser tool has no paired-interval mode.** The Python tool reads logs
   where one row carries both a set time and a clear time. The browser tool
   handles a duration column or separate set and clear rows, and nothing else.
2. **The window is applied at a different point.** The Python tool filters raw
   rows to the trailing window and then pairs set and clear rows. The browser
   tool pairs first and then filters occurrences. On the sample logs both give
   the same answer. On a log where a set falls outside the window and its clear
   falls inside, they would not. Nothing has hit this yet, and no fixture covers
   it, so the parity check would not notice.

Neither is fixed here, because fixing either one changes numbers users have
seen. That is a decision for the person who owns the tool, not for a cleanup.

## What the parity check still does not cover

Worth knowing, so the green tick is not read as more than it is.

- Only three logs are checked. A vendor format nobody has written a fixture for
  is not covered.
- The Excel and PowerPoint output is checked for structure by the end to end
  test, not compared number by number against the browser tool.
- The window difference above has no fixture, on purpose, because writing one
  would fail and the fix is a decision, not a cleanup.

## Moving this to another project

The parity harness is specific to this project. The other three layers transfer.

1. Copy `.claude/` and write a new `CLAUDE.md`.
2. In `CLAUDE.md`, write down what is true about the project that the code does
   not say. The test is whether a competent stranger would guess it. If they
   would not, it belongs in the file.
3. In `guard_edit.py`, edit the constants at the top. `APPROVED_PACKAGES`,
   `RUNTIME_PREFIXES`, and the checks themselves. Keep the split between
   blocking and warning. Block only what makes the product wrong.
4. Write a skill for anything explained more than twice.
5. Before trusting any hook, do two things. Feed it a violation and confirm it
   blocks. Then replay every existing file in the repo through it and confirm it
   blocks none of them. A guard with false positives gets deleted within a week.

## Checking the setup still works

The guard hook can be exercised by hand:

    echo '{"tool_name":"Write","tool_input":{"file_path":"alarm_pareto/x.py","content":"import requests"}}' \
      | python3 .claude/hooks/guard_edit.py; echo "exit $?"

Exit code 2 means it blocked, which is correct. Exit code 0 means the guard is
not working.
