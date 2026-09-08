"""Tests for the time-of-day filter.

The sample log has fourteen rows inside the thirty day window. Eleven of them
start between 06:00 and 18:00. The other three start at 22:00, 03:00, and
20:00. That split is what most of these tests check, because a day shift and a
night shift must add back up to the whole day with nothing counted twice.
"""

import pytest

from alarm_pareto import normalize as nz
from alarm_pareto import parse as parse_mod
from alarm_pareto import window as window_mod
from tests import data_paths as dp

# Rows in the window that start between 06:00 and 18:00, and the rest.
DAY_SHIFT_ROWS = 11
NIGHT_SHIFT_ROWS = 3


def _windowed():
    """The sample log, read and trimmed to the trailing thirty day window."""
    vendor_config = parse_mod.load_vendor_config(dp.CONFIG_PATH, "amat")
    raw = parse_mod.read_log(dp.SAMPLE_CSV, vendor_config)
    table, _ = nz.normalize(raw, vendor_config)
    windowed, _, _ = window_mod.apply_window(table, window_days=30)
    return windowed


def _kept(start_text, end_text):
    """Row count left after filtering the window to the given clock times."""
    start = window_mod.parse_time_of_day(start_text)
    end = window_mod.parse_time_of_day(end_text)
    return len(window_mod.apply_time_of_day(_windowed(), start, end))


# --- parsing ---------------------------------------------------------------

@pytest.mark.parametrize("text,expected", [
    ("00:00", 0),
    ("06:00", 360),
    ("6", 360),
    ("06", 360),
    ("18:30", 1110),
    ("23:59", 1439),
    ("24:00", 1440),
    ("07:15:45", 435),
    ("  08:00  ", 480),
])
def test_parse_time_of_day(text, expected):
    assert window_mod.parse_time_of_day(text) == expected


@pytest.mark.parametrize("text", [None, "", "   "])
def test_parse_blank_means_no_filter(text):
    assert window_mod.parse_time_of_day(text) is None


@pytest.mark.parametrize("text", [
    "25:00",     # hour past the end of the day
    "24:30",     # nothing may come after 24:00
    "06:60",     # minute out of range
    "half past", # not a time at all
    "6:00:00:0", # too many parts
])
def test_parse_rejects_bad_times(text):
    with pytest.raises(ValueError):
        window_mod.parse_time_of_day(text)


# --- what counts as a filter ----------------------------------------------

def test_no_bounds_is_not_a_filter():
    assert window_mod.is_time_of_day_filtered(None, None) is False


def test_one_bound_is_not_a_filter():
    assert window_mod.is_time_of_day_filtered(360, None) is False
    assert window_mod.is_time_of_day_filtered(None, 360) is False


def test_equal_bounds_mean_the_whole_day():
    assert window_mod.is_time_of_day_filtered(360, 360) is False


def test_midnight_to_midnight_is_the_whole_day():
    assert window_mod.is_time_of_day_filtered(0, window_mod.MINUTES_PER_DAY) is False


# --- filtering the sample --------------------------------------------------

def test_no_filter_keeps_every_windowed_row():
    expected = dp.load_expected()
    assert _kept(None, None) == expected["window"]["windowed_row_count"]


def test_day_shift():
    assert _kept("06:00", "18:00") == DAY_SHIFT_ROWS


def test_night_shift_wraps_past_midnight():
    assert _kept("18:00", "06:00") == NIGHT_SHIFT_ROWS


def test_two_shifts_add_up_to_the_whole_window():
    expected = dp.load_expected()
    total = _kept("06:00", "18:00") + _kept("18:00", "06:00")
    assert total == expected["window"]["windowed_row_count"]


def test_range_is_half_open():
    # One row starts at exactly 06:00. The start bound keeps it, the end bound
    # does not. This is what stops two shifts double counting the boundary.
    assert _kept("06:00", "07:00") == 1
    assert _kept("05:00", "06:00") == 0


def test_whole_day_range_keeps_every_windowed_row():
    expected = dp.load_expected()
    assert _kept("00:00", "24:00") == expected["window"]["windowed_row_count"]


def test_range_with_no_rows_comes_back_empty():
    assert _kept("01:00", "02:00") == 0


def test_filter_does_not_touch_the_original_table():
    table = _windowed()
    before = len(table)
    window_mod.apply_time_of_day(table, 360, 1080)
    assert len(table) == before


# --- labels ----------------------------------------------------------------

def test_label_without_a_filter():
    assert window_mod.time_of_day_label(None, None) == "All hours"


def test_label_for_a_plain_range():
    assert window_mod.time_of_day_label(360, 1080) == "06:00 to 18:00"


def test_label_says_when_the_range_crosses_midnight():
    label = window_mod.time_of_day_label(1320, 360)
    assert label == "22:00 to 06:00 (crosses midnight)"


def test_format_time_of_day():
    assert window_mod.format_time_of_day(0) == "00:00"
    assert window_mod.format_time_of_day(1439) == "23:59"
