"""Build the distributable zip packages.

This script makes the same zip files every time, from the current source. It
uses only the Python standard library, so it runs anywhere with no extra
packages. The GitHub release workflow calls this script, and you can run it by
hand too.

    python tools/build_zips.py

Output goes to the dist folder:
    dist/alarm_pareto_browser.zip   the single-file Pareto browser tool
    dist/alarm_pareto_python.zip    the Python package and tests
    dist/pm_logger.zip              the PM round logger and its read me

Every package leaves out caches, the virtual environment, and generated output.
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
        # The screenshot is a nice-to-have. Include it only if it exists.
        shot = ROOT / "docs" / "screenshot.png"
        if shot.exists():
            _add_file(zf, shot, f"{top}/screenshot.png")
    return target


def build_pm_logger_zip():
    """Build the PM Round Logger package.

    Everything someone needs to walk a round on a tablet, and nothing else. The
    logger itself is self-contained, so this is really just the tool plus the
    instructions plus the one-off capability test.
    """
    target = DIST / "pm_logger.zip"
    top = "pm_logger"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        _add_file(zf, ROOT / "pm_logger.html", f"{top}/pm_logger.html")
        _add_file(zf, ROOT / "packaging" / "pm_logger_READ_ME_FIRST.txt", f"{top}/READ_ME_FIRST.txt")
        # Run once per tablet to find out whether this browser can write into a
        # folder you choose, and whether it remembers that folder afterwards.
        _add_file(zf, ROOT / "pm_logger_capability_test.html", f"{top}/pm_logger_capability_test.html")
        # The screenshot is a nice-to-have. Include it only if it exists.
        shot = ROOT / "docs" / "pm_logger_screenshot.png"
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
        for name in ["requirements.txt", "setup_venv.bat", "conftest.py", "README.md"]:
            _add_file(zf, ROOT / name, f"{top}/{name}")
    return target


def main():
    if DIST.exists():
        # Start clean so old files never linger in a package.
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    browser = build_browser_zip()
    python = build_python_zip()
    pm_logger = build_pm_logger_zip()

    print("Built:")
    for path in (browser, python, pm_logger):
        size_kb = path.stat().st_size / 1024
        print(f"  {path.relative_to(ROOT)}  ({size_kb:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
