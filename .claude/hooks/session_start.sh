#!/usr/bin/env bash
# Report what this machine can actually verify, at the start of every session.
#
# Sessions get started in very different places. A fab laptop with no internet.
# A cloud container with no packages installed. A machine with everything ready.
# Claude used to find this out by failing halfway through a task. Now it knows
# up front, and it knows what to do about each case.
#
# This never installs anything without being able to. It reports and moves on.

set -u
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0

py=""
for c in .venv/bin/python .venv/Scripts/python.exe python3 python; do
  if command -v "$c" >/dev/null 2>&1 || [ -x "$c" ]; then py="$c"; break; fi
done

echo "Project check for the alarm Pareto tools."
echo

# --- Can the Python analysis be tested here? ---------------------------------
if [ -z "$py" ]; then
  echo "Python: not found. The Python tests cannot run in this session."
else
  missing=""
  for m in pytest pandas numpy openpyxl pptx matplotlib; do
    "$py" -c "import $m" >/dev/null 2>&1 || missing="$missing $m"
  done
  if [ -z "$missing" ]; then
    echo "Python: ready. Run the tests with: $py -m pytest -q"
  else
    echo "Python: present, but these packages are missing:$missing"
    echo "  The Python tests cannot run until they are installed."
    echo "  Try: $py -m pip install -r requirements.txt"
    echo "  If that fails there is no package index reachable from here. That is"
    echo "  normal on a bench machine and in some containers. Do not work around"
    echo "  it by editing requirements.txt. See .claude/skills/offline-setup."
  fi
fi

# --- Can the browser tool be checked here? -----------------------------------
if command -v node >/dev/null 2>&1; then
  echo "Node: ready. Check the browser tool with: node tools/check_parity.mjs"
else
  echo "Node: not found. The browser parity check cannot run in this session."
  echo "  Continuous integration runs it on every push, so it is still covered."
fi

echo
echo "Both tools must give the same numbers. If you change the analysis in one,"
echo "change it in the other and run the parity check. See CLAUDE.md."
