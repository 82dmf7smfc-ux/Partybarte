# Setting this project up on a new machine

Written for a locked-down Windows workstation with no access to PyPI, which is
the machine this project is actually developed on. The macOS and Linux notes are
there because CI runs on Linux.

Read `docs/STATE.md` first. It says where the work stands and what is next. This
file is only about getting a machine ready.

---

## 1. Get the code

**Clone it. Do not copy a working directory from another machine.**

    git clone https://github.com/82dmf7smfc-ux/Partybarte
    cd Partybarte
    git fetch --tags

Then confirm you can see the trunk and the tags:

    git log --oneline -1 origin/main
    git tag -l

If `origin/main` does not resolve, or `git tag -l` is empty, you have a partial
fetch and every judgement you make from it will be wrong. Fix that before going
further. This has already cost this project two weeks of drift; `docs/STATE.md`
tells the story.

### If the machine cannot reach GitHub

Bring a bundle instead. On a machine that can:

    git bundle create partybarte.bundle --all

Then on the target machine:

    git clone partybarte.bundle Partybarte
    cd Partybarte
    git remote set-url origin https://github.com/82dmf7smfc-ux/Partybarte

A bundle carries the full history and all branches, so nothing is lost. Remember
it is a snapshot: re-bundle when you want newer work.

---

## 2. Find out what the network allows

Do this before fighting the installer.

    python tools/check_egress.py

It needs no packages, so it runs before the environment exists. It probes the
hosts this project needs and says which are blocked and what that costs you.
`docs/EGRESS.md` explains what to ask for if something is blocked.

The failure this prevents: with PyPI blocked, `pip install` fails with "no
matching distribution found", which reads as a bad version pin rather than a
firewall. A whole session was lost to that once.

---

## 3. Set your git identity

Do this before the first commit. A fresh machine uses whatever global config it
has, which may be a real name and address you did not mean to publish.

    git config user.name  "82dmf7smfc-ux"
    git config user.email "82dmf7smfc@privaterelay.appleid.com"

Set it per-repository, as above, not globally, so other projects on the machine
are unaffected.

Check it took before you commit anything:

    git config user.email

If you get this wrong and notice before the branch is merged, it is fixable:
rewrite the branch and force-push with `--force-with-lease`. After a merge it is
not, short of rewriting `main`.

---

## 4. Build the environment

### Windows, offline (the normal case)

Get the wheel folder from IT first. `docs/WHEELS.md` lists exactly what to ask
for. Then:

    setup_venv.bat C:\path\to\wheels

The script checks your Python version before doing anything, creates `.venv` next
to itself whatever folder you ran it from, and installs offline without touching
the network.

### Windows, with internet

    setup_venv.bat

### macOS or Linux

    ./setup_venv.sh                    # with internet
    ./setup_venv.sh /path/to/wheels    # offline

### Python version

3.11 or 3.12. Not 3.13 or newer: the pinned numpy 1.26.4 and pandas 2.2.2 have no
wheels for it. The setup scripts check and say so, because the resolver's own
error message does not mention the real cause.

---

## 5. Check it works

Four gates, cheapest first.

    python tools/check_version.py          # no packages needed
    node tests/browser/run.mjs             # needs Node and Chromium, no install
    .venv\Scripts\python.exe -m pytest -q  # needs the environment
    python tools/build_zips.py             # no packages needed

`node tests/browser/run.mjs` should report `377 passed, 0 failed`. That number is
checked by the suite against `CLAUDE.md`; if it disagrees, one of them is stale
and the run says so.

Then a real end-to-end run, including the newest features:

    .venv\Scripts\python.exe -m alarm_pareto.main ^
      --input tests\data\sample_alarm_log.csv --vendor amat ^
      --start-time 18:00 --end-time 06:00 --downtime-method in_range

It should print a night-shift report covering 360 hours with 2.50 hours of
in-range downtime, and write a workbook and a deck into `output\`. Open both.
Those exact numbers are pinned in `tests/data/cross_tool_golden.json`, so if they
differ, something is genuinely wrong rather than merely different.

Finally, open `alarm_pareto.html` by double-clicking it, press "Load built-in
sample", pick the night shift preset, and press Analyze. The browser tool must
produce the same numbers as the Python tool; that is what the cross-tool fixture
exists to enforce.

---

## 6. Where things are

| Path | What it is |
|---|---|
| `docs/STATE.md` | Where the work stands, what is next, decisions and why. **Read first.** |
| `CLAUDE.md` | Conventions, traps, and how to verify a change. |
| `ROADMAP.md` | The backlog of record. There are no GitHub issues. |
| `CHANGELOG.md` | What shipped, in plain prose. Stamping a heading here cuts a release. |
| `docs/LESSONS.md` | What went wrong before, so it does not go wrong again. |
| `docs/WHEELS.md` | The offline wheel list for IT. |
| `docs/EGRESS.md` | What the network must allow, and why. |
| `docs/CATEGORY_RULES.md` | How the fault category rules work. |
| `docs/DEBUG_CODES.md` | The debug code registry the harness checks. |

---

## 7. House rules worth knowing on day one

- **Real equipment logs never go in the repository.** They are customer data.
  They reach this project as pictures, deliberately, because the bench machine
  has no approved path out for text. `.gitignore` carries a guard rail, but the
  guard rail is not the policy; this is.
- `alarm_pareto.html` stays one self-contained file. No CDN, no bundled library,
  no build step, no network calls at runtime. It has to open from a USB stick.
- The two tools must produce the same numbers.
  `tests/data/cross_tool_golden.json` enforces it; do not regenerate that file
  from either tool's output.
- Anything changed in the browser tool earns coverage in `tests/browser/run.mjs`.
- Releases cut themselves. Landing a version heading in `CHANGELOG.md` on `main`
  publishes that release. Do not push a tag by hand: a tag pushed with the
  built-in token starts no workflows, so it fails silently and looks like it
  worked.
