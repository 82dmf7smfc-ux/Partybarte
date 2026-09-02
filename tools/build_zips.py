"""Build the two distributable zip packages.

This script makes the same two zip files every time, from the current source. It
uses only the Python standard library, so it runs anywhere with no extra
packages. The GitHub release workflow calls this script, and you can run it by
hand too.

    python tools/build_zips.py

Output goes to the dist folder:
    dist/alarm_pareto_browser.zip   the single-file browser tool
    dist/alarm_pareto_python.zip    the Python package and tests

Both packages leave out caches, the virtual environment, and generated output.
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
        for name in ["requirements.txt", "conftest.py", "README.md"]:
            _add_file(zf, PARETO / name, f"{top}/{name}")
    return target


def main():
    if DIST.exists():
        # Start clean so old files never linger in a package.
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    browser = build_browser_zip()
    python = build_python_zip()

    print("Built:")
    for path in (browser, python):
        size_kb = path.stat().st_size / 1024
        print(f"  {path.relative_to(ROOT)}  ({size_kb:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
