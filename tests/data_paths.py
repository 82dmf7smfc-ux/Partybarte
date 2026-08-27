"""Small helper so every test finds the sample files the same way."""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
SAMPLE_CSV = DATA_DIR / "sample_alarm_log.csv"
# A second sample in the paired-interval shape, used by the Picosun tests.
SAMPLE_PICOSUN_CSV = DATA_DIR / "sample_picosun_log.csv"
EXPECTED_JSON = DATA_DIR / "expected_summary.json"

# The vendor config that ships inside the package.
CONFIG_PATH = Path(__file__).parents[1] / "alarm_pareto" / "config" / "vendor_columns.json"


def load_expected():
    """Return the golden expected values as a dictionary."""
    return json.loads(EXPECTED_JSON.read_text(encoding="utf-8"))
