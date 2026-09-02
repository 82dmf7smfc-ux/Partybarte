# Partybarte

This repository holds more than one tool. Each tool is a separate project. Each
project lives in its own folder under `projects` and has its own read me.

## Projects

| Project | What it does |
|---|---|
| [`projects/alarm_pareto`](projects/alarm_pareto/README.md) | Ranks the faults in a semiconductor tool alarm log, by how often each one happens and by how much downtime it causes. Comes as a zero-install browser page and as a Python command line tool. |

## How this repository is laid out

Everything a single project owns lives inside that project's folder. That means
its code, its tests, its sample data, and its read me. Everything shared by the
whole repository stays at the root.

| Path | What it is |
|---|---|
| `projects/` | One folder per project. This is where the code lives. |
| `requirements.txt` | The pinned Python packages, shared by every project. |
| `setup_venv.bat` | Builds the one shared `.venv` environment on Windows. |
| `pytest.ini` | Points pytest at every project, so one command runs all tests. |
| `tools/build_zips.py` | Builds the download packages for release. |
| `CONTRIBUTING.md` | How to set up, test, branch, and cut a release. |
| `ROADMAP.md` | Ideas and future improvements, so they are not lost. |
| `CHANGELOG.md` | A dated record of what changed in each version. |
| `.github/workflows/` | The continuous integration and release automation. |

## Rules that apply to every project here

These are not style preferences. They come from where these tools have to run.

1. **Fully offline.** No project makes a network call at runtime. The machines
   these tools run on have no internet, and the data must not leave them.
2. **Ask before adding a package.** Every Python package is an IT approval
   request. Use what is already in `requirements.txt` where you can.
3. **A browser tool stays one file.** No outside scripts, no content delivery
   networks, no fonts fetched from the web.
4. **Plain code and plain writing.** Short sentences. Common words. Comments
   that a smart reader who is not a full-time programmer can follow.

`CONTRIBUTING.md` explains all of this in more detail.

## First time setup

You need Python and the packages in `requirements.txt`. On a machine with
internet:

```
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

On an offline machine, get the wheel files from IT, put them in one folder, and
run `setup_venv.bat C:\path\to\wheel_folder`. A wheel is a pre-built package
file. There is one environment for the whole repository, so you only do this
once, not once per project.

## Running the tests

From the repository root, this runs the tests for every project:

```
.venv\Scripts\python.exe -m pytest -q
```

To run one project's tests only, name its folder:

```
.venv\Scripts\python.exe -m pytest -q projects\alarm_pareto
```

## Downloads

Packaged versions are published on the GitHub Releases page. To build them
yourself, run `python tools/build_zips.py` from the repository root. The
packages land in `dist`.
