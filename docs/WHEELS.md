# The offline wheel list

What to ask IT for so the project installs on a machine with no PyPI access.

## How to produce the folder

Run this on any machine that *can* reach PyPI. It downloads the wheels without
installing anything, so it is safe to run anywhere:

```
python -m pip download ^
  --dest wheels ^
  --platform win_amd64 ^
  --python-version 3.12 ^
  --implementation cp ^
  --only-binary :all: ^
  -r requirements.txt -r requirements-dev.txt
```

On macOS or Linux use `\` instead of `^` for line continuation. For a 3.11
target machine, change `--python-version` to `3.11`; wheels are per Python minor
version, so a 3.12 folder will not install on 3.11.

Then copy the `wheels` folder to the target machine and:

```
setup_venv.bat C:\path\to\wheels
```

## What the folder must contain

**Direct dependencies, pinned.** These are the versions the project is fixed to,
and they must match `requirements.txt`, `requirements-dev.txt` and
`pyproject.toml` exactly. `tools/check_version.py` does not check these; keeping
the three files in step is a manual job, so change them together.

| Package | Version | Needed for |
|---|---|---|
| pandas | 2.2.2 | the whole analysis |
| numpy | 1.26.4 | pandas |
| openpyxl | 3.1.5 | writing the Excel workbook |
| python-pptx | 1.0.2 | writing the PowerPoint deck |
| matplotlib | 3.9.2 | the chart images on the slides |
| pytest | 8.3.2 | running the tests (dev only) |

**Transitive dependencies.** These come along automatically and must be in the
folder too, or the offline install fails on the first one it cannot find.

The exact list and its versions depend on the resolver and the target Python, so
**do not copy version numbers from anywhere, including this file.** Generate them
with the `pip download` command above and read the filenames it produces. As a
guide to roughly how many files to expect, the transitive set covers: the date
and timezone support pandas needs, `et-xmlfile` for openpyxl, `lxml`, `Pillow`
and `XlsxWriter` for python-pptx, matplotlib's own layout and font handling
packages, and `iniconfig` and `pluggy` for pytest. Expect somewhere around twenty
to twenty-five files in total, and around 150 MB.

If IT will only approve a fixed list, run the command, then send them the output
of:

```
dir /b wheels
```

That is the authoritative list for your exact target, which no document can be.

## Why the versions are pinned rather than ranged

`requirements.txt` says it plainly: this tool has to build the same way in
eighteen months. A range means a machine rebuilt in a year gets different code
than the one that was validated, and there is no CI on the bench machine to
catch the difference.

If IT supplies different versions, change `requirements.txt`, `pyproject.toml`
and `requirements-dev.txt` together to match the wheels you actually have, and
say so in the commit. Do not leave the files claiming versions that are not what
is installed.

## Do not commit the wheels

They are around 150 MB of binaries, they are per platform and per Python
version, and they go stale. `.gitignore` does not currently exclude a `wheels/`
folder by name because the folder is expected to live outside the repository.
Keep it there.
