"""Small helper so every test finds the sample files the same way."""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
SAMPLE_CSV = DATA_DIR / "sample_alarm_log.csv"
EXPECTED_JSON = DATA_DIR / "expected_summary.json"

# The set and clear log, and its golden numbers. The browser tool is checked
# against this same file by tools/check_parity.mjs.
SETCLEAR_CSV = DATA_DIR / "sample_setclear_log.csv"
EXPECTED_SETCLEAR_JSON = DATA_DIR / "expected_setclear.json"

# A log that spans both daylight saving changes and carries one impossible
# date. It exists to keep the two tools reading timestamps the same way.
DST_CSV = DATA_DIR / "sample_dst_log.csv"
EXPECTED_DST_JSON = DATA_DIR / "expected_dst.json"

# The vendor config that ships inside the package.
CONFIG_PATH = Path(__file__).parents[1] / "alarm_pareto" / "config" / "vendor_columns.json"


def load_expected():
    """Return the golden expected values as a dictionary."""
    return json.loads(EXPECTED_JSON.read_text(encoding="utf-8"))


def load_expected_setclear():
    """Return the golden values for the set and clear sample log."""
    return json.loads(EXPECTED_SETCLEAR_JSON.read_text(encoding="utf-8"))
