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

# The project root is the folder above this script's "tools" folder.
ROOT = Path(__file__).resolve().parents[1]
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
        _add_file(zf, ROOT / "alarm_pareto.html", f"{top}/alarm_pareto.html")
        _add_file(zf, ROOT / "tests" / "data" / "sample_alarm_log.csv", f"{top}/sample_alarm_log.csv")
        _add_file(zf, ROOT / "packaging" / "browser_READ_ME_FIRST.txt", f"{top}/READ_ME_FIRST.txt")
        _add_file(zf, ROOT / "LICENSE", f"{top}/LICENSE")
        # The screenshot is a nice-to-have. Include it only if it exists.
        shot = ROOT / "docs" / "screenshot.png"
        if shot.exists():
            _add_file(zf, shot, f"{top}/screenshot.png")
    return target


def build_python_zip():
    """Build the Python package. The code, the tests, and the setup files."""
    target = DIST / "alarm_pareto_python.zip"
    top = "alarm_pareto_python"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        _add_tree(zf, ROOT / "alarm_pareto", f"{top}/alarm_pareto")
        _add_tree(zf, ROOT / "tests", f"{top}/tests")
        for name in ["requirements.txt", "setup_venv.bat", "conftest.py", "README.md", "LICENSE"]:
            _add_file(zf, ROOT / name, f"{top}/{name}")
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
