"""Tests for reading and renaming the log.

These check that vendor columns map to internal names, that the mode is detected,
and that timestamps and durations are parsed into real numbers and dates.
"""

import pandas as pd

from alarm_pareto import normalize as nz
from alarm_pareto import parse as parse_mod
from tests import data_paths as dp


def _load():
    vendor_config = parse_mod.load_vendor_config(dp.CONFIG_PATH, "amat")
    raw = parse_mod.read_log(dp.SAMPLE_CSV, vendor_config)
    table, mode = nz.normalize(raw, vendor_config)
    return raw, table, mode


def test_raw_row_count_matches_file():
    expected = dp.load_expected()
    vendor_config = parse_mod.load_vendor_config(dp.CONFIG_PATH, "amat")
    raw = parse_mod.read_log(dp.SAMPLE_CSV, vendor_config)
    assert len(raw) == expected["window"]["raw_row_count"]


def test_columns_are_renamed_to_internal_names():
    _, table, _ = _load()
    for name in ["ts_set", "fault_code", "description", "equipment", "duration_s"]:
        assert name in table.columns


def test_mode_is_duration():
    # The amat config maps a duration column, so the tool should pick duration mode.
    _, _, mode = _load()
    assert mode == nz.MODE_DURATION


def test_timestamps_are_datetimes():
    _, table, _ = _load()
    assert pd.api.types.is_datetime64_any_dtype(table["ts_set"])


def test_duration_is_numeric_seconds():
    _, table, _ = _load()
    assert pd.api.types.is_numeric_dtype(table["duration_s"])
    # The first row after sorting is the out-of-window January row with 3600 s.
    assert table["duration_s"].min() >= 0


def test_missing_vendor_raises_clear_error():
    try:
        parse_mod.load_vendor_config(dp.CONFIG_PATH, "does_not_exist")
    except KeyError as err:
        assert "does_not_exist" in str(err)
    else:
        raise AssertionError("Expected a KeyError for an unknown vendor.")
