"""Check that the browser tool and the Python tool agree.

The same analysis is written twice in this project. Once in Python, in the
alarm_pareto package. Once in JavaScript, inside alarm_pareto.html. They must
give the same numbers for the same log, or the two tools quietly disagree and
nobody notices.

The other tests in this folder check the Python side against
tests/data/expected_summary.json. This test checks the browser side against the
same file, so one golden file governs both tools.

The work is done by tools/check_parity.mjs, which runs the real shipped
JavaScript. Nothing is copied, so the check cannot go stale. That script needs
Node, which is not part of the offline runtime. If Node is missing the test
skips rather than fails, because the shipped tools do not need it. Continuous
integration has Node, so the check always runs there.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
PARITY_SCRIPT = ROOT / "tools" / "check_parity.mjs"


@pytest.mark.skipif(shutil.which("node") is None, reason="Node is not installed on this machine")
def test_browser_tool_matches_the_golden_file():
    result = subprocess.run(
        ["node", str(PARITY_SCRIPT)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    # On failure the script explains exactly which numbers disagree. Show that
    # message instead of a bare exit code.
    assert result.returncode == 0, result.stdout + result.stderr
