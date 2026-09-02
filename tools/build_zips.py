"""Build the distributable zip packages.

This script makes the same zip files every time, from the current source. It uses
only the Python standard library, so it runs anywhere with no extra packages. The
GitHub release workflow calls this script, and you can run it by hand too.

    python tools/build_zips.py                  build every project
    python tools/build_zips.py alarm_pareto     build one project only
    python tools/build_zips.py fab_drivers

Output goes to the dist folder:
    dist/alarm_pareto_browser.zip   the single-file browser tool
    dist/alarm_pareto_python.zip    the Python package and tests
    dist/fab_drivers.zip            the driver library, for a bench machine

Every package leaves out caches, the virtual environment, and generated output.

Releases are per project, so the release workflow builds one project at a time,
picked from the tag name. Building everything is still the right thing to do in
CI, because that proves each package can be built.
"""

import shutil
import sys
import zipfile
from pathlib import Path

# The repository root is the folder above this script's "tools" folder. Each
# project lives in its own folder under "projects". This script packages the
# alarm_pareto project. When another project needs packaging, add a build
# function for it below and call it from main.
ROOT = Path(__file__).resolve().parents[1]
PARETO = ROOT / "projects" / "alarm_pareto"
DRIVERS = ROOT / "projects" / "fab_drivers"
DIST = ROOT / "dist"

# Folders and files we never want inside a package.
SKIP_DIR_NAMES = {"__pycache__", ".pytest_cache", ".venv", "output", ".git", "dist"}


def _add_file(zf, source, arcname):
    """Put one file into the zip under a chosen name."""
    zf.write(source, arcname)


def _add_tree(zf, source_dir, arc_prefix):
    """Put a whole folder into the zip, skipping caches and junk.

    source_dir: the folder on disk to copy in.
    arc_prefix: the path the files should have inside the zip.
    """
    for path in sorted(source_dir.rglob("*")):
        # Skip anything inside a folder we do not want.
        if any(part in SKIP_DIR_NAMES for part in path.relative_to(source_dir).parts):
            continue
        if path.is_file():
            rel = path.relative_to(source_dir)
            _add_file(zf, path, f"{arc_prefix}/{rel.as_posix()}")


def build_browser_zip():
    """Build the browser package. One HTML file plus a sample and a read me."""
    target = DIST / "alarm_pareto_browser.zip"
    top = "alarm_pareto_browser"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        _add_file(zf, PARETO / "alarm_pareto.html", f"{top}/alarm_pareto.html")
        _add_file(zf, PARETO / "tests" / "data" / "sample_alarm_log.csv", f"{top}/sample_alarm_log.csv")
        _add_file(zf, PARETO / "packaging" / "browser_READ_ME_FIRST.txt", f"{top}/READ_ME_FIRST.txt")
        _add_file(zf, ROOT / "LICENSE", f"{top}/LICENSE")
        # The screenshot is a nice-to-have. Include it only if it exists.
        shot = PARETO / "docs" / "screenshot.png"
        if shot.exists():
            _add_file(zf, shot, f"{top}/screenshot.png")
    return target


def build_python_zip():
    """Build the Python package. The code, the tests, and the setup files."""
    target = DIST / "alarm_pareto_python.zip"
    top = "alarm_pareto_python"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        _add_tree(zf, PARETO / "alarm_pareto", f"{top}/alarm_pareto")
        _add_tree(zf, PARETO / "tests", f"{top}/tests")
        # The environment setup script is shared by the whole repository, so it
        # comes from the root. Everything else belongs to this project, including
        # its package list, which names only the packages this tool imports. That
        # keeps the approval request short for whoever installs it. Inside the
        # zip they all sit together at the top level, which is the flat layout
        # the person downloading it expects.
        _add_file(zf, ROOT / "setup_venv.bat", f"{top}/setup_venv.bat")
        _add_file(zf, ROOT / "LICENSE", f"{top}/LICENSE")
        for name in ["requirements.txt", "conftest.py", "README.md"]:
            _add_file(zf, PARETO / name, f"{top}/{name}")
    return target


def build_fab_drivers_zip():
    """Build the driver library package.

    This one is not a tool a person double-clicks. It is a folder you put on a
    bench machine and leave running, so the package is the code, the tests, and
    the documents that explain how to use it safely.
    """
    target = DIST / "fab_drivers.zip"
    top = "fab_drivers"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        _add_tree(zf, DRIVERS / "fab_drivers", f"{top}/fab_drivers")
        _add_tree(zf, DRIVERS / "tests", f"{top}/tests")
        _add_file(zf, ROOT / "setup_venv.bat", f"{top}/setup_venv.bat")
        _add_file(zf, ROOT / "LICENSE", f"{top}/LICENSE")
        for name in ["requirements.txt", "conftest.py", "README.md",
                     "DECISIONS.md", "REVIEW.md", "CLAUDE.md"]:
            _add_file(zf, DRIVERS / name, f"{top}/{name}")
        _add_tree(zf, DRIVERS / "sessions", f"{top}/sessions")
    return target


# Which builders belong to which project. The release workflow reads a project
# name off the tag, so the names here are the names used in tags.
PROJECTS = {
    "alarm_pareto": [build_browser_zip, build_python_zip],
    "fab_drivers": [build_fab_drivers_zip],
}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv

    if not argv:
        wanted = list(PROJECTS)
    elif len(argv) == 1 and argv[0] in PROJECTS:
        wanted = [argv[0]]
    else:
        print("usage: python tools/build_zips.py [%s]" % " | ".join(PROJECTS))
        return 2

    if DIST.exists():
        # Start clean so old files never linger in a package.
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    built = []
    for project in wanted:
        for builder in PROJECTS[project]:
            built.append(builder())

    print("Built:")
    for path in built:
        size_kb = path.stat().st_size / 1024
        print(f"  {path.relative_to(ROOT)}  ({size_kb:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
