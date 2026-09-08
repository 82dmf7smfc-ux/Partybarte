#!/usr/bin/env bash
# Build the project-local virtual environment on macOS or Linux.
#
# The Windows twin of this script, setup_venv.bat, is the one a bench machine
# uses. This exists because CI runs on Linux and every command in the README was
# a Windows path, so there was no scripted setup for the platform the project is
# actually tested on.
#
# Usage:
#   ./setup_venv.sh                     install from the default index
#   ./setup_venv.sh /path/to/wheels     install offline from a wheel folder
set -euo pipefail

# Work from the folder this script lives in, whatever folder it was called from.
cd "$(dirname "$0")"

WHEEL_DIR="${1:-}"

# numpy 1.26.4 and pandas 2.2.2 have no wheels for 3.13 or newer. Say so here
# rather than letting the resolver fail with a message about nothing in
# particular.
if ! python3 -c 'import sys; sys.exit(0 if (3,11) <= sys.version_info[:2] <= (3,12) else 1)'; then
  echo
  echo "This project needs Python 3.11 or 3.12."
  python3 --version
  echo
  echo "The pinned numpy and pandas versions have no wheels for anything newer."
  echo "Use 3.12, or change the pins in requirements.txt and pyproject.toml"
  echo "together if you have different wheels."
  exit 1
fi

echo "Creating virtual environment in .venv ..."
python3 -m venv .venv

if [ -z "$WHEEL_DIR" ]; then
  echo "Upgrading pip inside the environment ..."
  .venv/bin/python -m pip install --upgrade pip
  echo "Installing packages from the default index (needs internet) ..."
  .venv/bin/python -m pip install -r requirements.txt -r requirements-dev.txt
else
  echo "Installing packages from local wheels in $WHEEL_DIR ..."
  .venv/bin/python -m pip install --no-index --find-links "$WHEEL_DIR" \
    -r requirements.txt -r requirements-dev.txt
fi

echo
echo "Done. The environment is ready in the .venv folder."
echo "To run the tool:"
echo "  .venv/bin/python -m alarm_pareto.main --input tests/data/sample_alarm_log.csv --vendor amat"
echo "To run the tests:"
echo "  .venv/bin/python -m pytest -q"
echo "  node tests/browser/run.mjs"
