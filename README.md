# Partybarte

This repository holds more than one tool. Each tool is a separate project. Each
project lives in its own folder under `projects` and has its own read me.

## Projects

| Project | What it does |
|---|---|
| [`projects/alarm_pareto`](projects/alarm_pareto/README.md) | Ranks the faults in a semiconductor tool alarm log, by how often each one happens and by how much downtime it causes. Comes as a zero-install browser page and as a Python command line tool. |
| [`projects/fab_drivers`](projects/fab_drivers/README.md) | A library of small, read-only monitoring drivers for fab equipment. Reads values over serial, logs every raw frame, and trends the readings into daily CSV files. Read its safety section before connecting anything. |

## How this repository is laid out

Everything a single project owns lives inside that project's folder. That means
its code, its tests, its sample data, and its read me. Everything shared by the
whole repository stays at the root.

| Path | What it is |
|---|---|
| `projects/` | One folder per project. This is where the code lives. |
| `requirements.txt` | Gathers each project's pinned packages into one install. |
| `setup_venv.bat` | Builds the one shared `.venv` environment on Windows. |
| `pytest.ini` | Points pytest at every project, so one command runs all tests. |
| `tools/build_zips.py` | Builds the download packages for release. |
| `CONTRIBUTING.md` | How to set up, test, branch, and cut a release. |
| `ROADMAP.md` | Ideas and future improvements, so they are not lost. |
| `CHANGELOG.md` | A dated record of what changed in each version. |
| `.github/workflows/` | The continuous integration and release automation. |

## Rules that apply to every project here

These are not style preferences. They come from where these tools have to run.

1. **Nothing leaves the building.** No project reaches the internet, at any
   point, for any reason. No telemetry. No content delivery networks. No fonts
   fetched from the web. The machines these tools run on have no internet, and
   the data on them must not leave.

   Talking to a piece of equipment is not the same thing. A driver that reads a
   gauge over RS-232, or over a socket to a tool on the fab network, is doing
   exactly what it is for. The rule is about the internet, not about local
   links.
2. **Ask before adding a package.** Every Python package is an IT approval
   request. Use what a project already pins where you can.
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

Each project pins its own packages, in its own folder. The file at the root just
gathers them. That way a download package only asks a person to approve the
packages that tool really imports.

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

Packaged versions are published on the GitHub Releases page. Releases are per
project, and the tag says which one, for example `alarm-pareto-v1.5.0` or
`fab-drivers-v0.1.0`.

To build them yourself, run `python tools/build_zips.py` from the repository
root, or name one project to build only that. The packages land in `dist`.
