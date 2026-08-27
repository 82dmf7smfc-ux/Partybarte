# Magnet Field Mapping Bench: course repository

Written lecture material for a 35 class self-directed course on permanent magnet
metrology, plus an accumulating source library. The end product is a working
bench that maps and images permanent magnet fields and tracks them over years.

Start with `CLAUDE.md` for the standing rules, then `PROGRESS.md` for where the
build is, then `KICKOFF.md` and `BUILD_PROMPTS.md` for the session prompts.
`syllabus/magnet-bench-syllabus.html` is the source of truth for scope.

## Why this lives in a subdirectory

This course was set up inside the `Partybarte` repository, which already held
the Alarm Log Pareto tool. The session 0 instructions assume an empty directory
and would have overwritten that project's `requirements.txt` and `.gitignore` at
the repository root. Everything for the course is therefore under
`magnet-course/`, and the two projects do not touch.

If the course should have its own repository, this whole directory moves across
intact and nothing here depends on its parent.

## Layout

```
syllabus/     the HTML syllabus and research checklist, never edited by a session
library/      sources.json, verified.log, export.bib, pdf/, notes/, queue.md
shared/       notation.md, glossary.md, reference-part.md
classes/      cNN-slug/ per class: class.md, worked.py, worked.out, artifact/
tools/        scripts that generate the files which would otherwise drift
reviews/      unit reviews and the adversarial pass
PROGRESS.md   class status table
CHANGES.md    proposed syllabus and CLAUDE.md changes, never applied silently
```

## Scripts

```
python3 tools/extract_syllabus.py syllabus/magnet-bench-syllabus.html   # syllabus as JSON
python3 tools/build_sources.py      # regenerate library/sources.json
python3 tools/verify_sources.py     # attempt every URL, append to verified.log
python3 tools/build_bib.py          # regenerate library/export.bib
python3 tools/build_progress.py     # regenerate the PROGRESS.md class table
python3 tools/conversions.py        # SI to CGS conversions used by notation.md
```

`PROGRESS.md` and `library/sources.json` restate content that lives in the
syllabus. They are generated rather than hand maintained so that 35 class titles
and 40 source keys cannot drift out of sync.
