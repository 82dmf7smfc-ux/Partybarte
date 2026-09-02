"""Tests for the trailing-window filter.

The window ends at the latest timestamp in the file, not today's date. One row
in the sample sits in January, well before the window. It must be dropped.
"""

import pandas as pd

from alarm_pareto import normalize as nz
from alarm_pareto import parse as parse_mod
from alarm_pareto import window as window_mod
from tests import data_paths as dp


def _windowed():
    vendor_config = parse_mod.load_vendor_config(dp.CONFIG_PATH, "amat")
    raw = parse_mod.read_log(dp.SAMPLE_CSV, vendor_config)
    table, _ = nz.normalize(raw, vendor_config)
    return window_mod.apply_window(table, window_days=30)


def test_window_row_count():
    expected = dp.load_expected()
    windowed, _, _ = _windowed()
    assert len(windowed) == expected["window"]["windowed_row_count"]


def test_window_end_is_latest_timestamp():
    expected = dp.load_expected()
    _, _, window_end = _windowed()
    assert window_end == pd.Timestamp(expected["window"]["window_end"])


def test_window_start_is_end_minus_days():
    expected = dp.load_expected()
    _, window_start, _ = _windowed()
    assert window_start == pd.Timestamp(expected["window"]["window_start"])


def test_january_row_is_excluded():
    windowed, _, _ = _windowed()
    # No timestamp in the window should be in January 2026.
    assert (windowed["ts_set"] >= pd.Timestamp("2026-01-22 20:00:00")).all()
