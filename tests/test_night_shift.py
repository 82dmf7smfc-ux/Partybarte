"""Tests for the night shift, the case where a shift runs past midnight.

A night shift is written 18:00 to 06:00. The start is later than the end. That
is the whole difficulty: the kept clock time is in two pieces, an evening tail
before midnight and a morning head after it, and the two pieces sit on two
different calendar dates.

These tests are deliberately exhaustive rather than sampled. The filter is
cheap to run and the cost of a quiet off-by-one on a shift boundary is a report
that silently misses or double counts alarms, so every one of the 1440 minutes
in a day is checked rather than a handful of interesting ones.

The tables here are built in the test rather than read from the sample log,
because the sample log has only a few overnight rows and these tests need every
minute and several consecutive dates.
"""

import pandas as pd
import pytest

from alarm_pareto import window as window_mod

# The night shift under test, in minutes since midnight.
NIGHT_START = 18 * 60   # 1080
NIGHT_END = 6 * 60      # 360


def _table(timestamps):
    """A minimal table with just the column the filter looks at."""
    return pd.DataFrame({"ts_set": pd.to_datetime(pd.Series(timestamps))})


def _every_minute_of(date):
    """All 1440 timestamps in one calendar day, one per minute."""
    return pd.date_range("%s 00:00:00" % date, periods=1440, freq="min")


def _kept_minutes(table, start, end):
    """The set of clock minutes that survived the filter."""
    kept = window_mod.apply_time_of_day(table, start, end)
    return set((kept["ts_set"].dt.hour * 60 + kept["ts_set"].dt.minute).tolist())


# --- every minute of the clock, checked one at a time ----------------------

def test_night_shift_keeps_exactly_the_right_minutes():
    """All 1440 minutes of a day, checked against the definition by hand.

    A minute belongs to the 18:00-06:00 night shift when it is at or after
    18:00, or before 06:00. Nothing else. This spells that out independently of
    the implementation instead of reusing its expression.
    """
    table = _table(_every_minute_of("2026-03-10"))
    kept = _kept_minutes(table, NIGHT_START, NIGHT_END)

    expected = set()
    for minute in range(1440):
        if minute >= NIGHT_START or minute < NIGHT_END:
            expected.add(minute)

    assert kept == expected
    # 18:00 to midnight is 360 minutes, midnight to 06:00 is another 360.
    assert len(kept) == 720


def test_day_shift_is_the_exact_complement_of_the_night_shift():
    """Every minute lands in exactly one of the two shifts."""
    table = _table(_every_minute_of("2026-03-10"))
    night = _kept_minutes(table, NIGHT_START, NIGHT_END)
    day = _kept_minutes(table, NIGHT_END, NIGHT_START)

    assert night & day == set()            # nothing counted twice
    assert night | day == set(range(1440))  # nothing lost
    assert len(day) == 720


@pytest.mark.parametrize("start_hour", range(24))
def test_any_twelve_hour_shift_and_its_opposite_cover_the_whole_day(start_hour):
    """Not just 18:00. Every twelve hour shift start is checked.

    Twelve of these twenty four cases wrap past midnight, so this exercises the
    wrapping branch from every possible starting hour.
    """
    table = _table(_every_minute_of("2026-03-10"))
    start = start_hour * 60
    end = (start + 12 * 60) % 1440

    first = _kept_minutes(table, start, end)
    second = _kept_minutes(table, end, start)

    assert first & second == set()
    assert first | second == set(range(1440))
    assert len(first) == 720


@pytest.mark.parametrize("start_hour", range(24))
@pytest.mark.parametrize("length_hours", [1, 4, 8, 12, 16, 23])
def test_a_range_and_its_complement_always_partition_the_day(start_hour, length_hours):
    """The partition property, over every start hour and several lengths.

    This is the single strongest statement about the filter: for any range,
    the range and its complement between them keep every minute exactly once.
    An off-by-one at either bound, or a wrap handled wrongly, breaks it.
    """
    table = _table(_every_minute_of("2026-03-10"))
    start = start_hour * 60
    end = (start + length_hours * 60) % 1440

    inside = _kept_minutes(table, start, end)
    outside = _kept_minutes(table, end, start)

    assert inside & outside == set()
    assert inside | outside == set(range(1440))
    assert len(inside) == length_hours * 60


# --- the boundary minutes, called out one by one --------------------------

def test_the_shift_starts_at_exactly_eighteen_hundred():
    table = _table(["2026-03-10 17:59:00", "2026-03-10 18:00:00"])
    kept = window_mod.apply_time_of_day(table, NIGHT_START, NIGHT_END)
    assert len(kept) == 1
    assert kept["ts_set"].iloc[0] == pd.Timestamp("2026-03-10 18:00:00")


def test_the_shift_ends_just_before_oh_six_hundred():
    table = _table(["2026-03-11 05:59:00", "2026-03-11 06:00:00"])
    kept = window_mod.apply_time_of_day(table, NIGHT_START, NIGHT_END)
    assert len(kept) == 1
    assert kept["ts_set"].iloc[0] == pd.Timestamp("2026-03-11 05:59:00")


def test_seconds_do_not_push_a_row_over_a_boundary():
    """05:59:59 is still minute 359, so it is still inside the night shift."""
    table = _table(["2026-03-11 05:59:59", "2026-03-11 06:00:01"])
    kept = window_mod.apply_time_of_day(table, NIGHT_START, NIGHT_END)
    assert len(kept) == 1
    assert kept["ts_set"].iloc[0] == pd.Timestamp("2026-03-11 05:59:59")


def test_midnight_itself_is_inside_the_night_shift():
    table = _table(["2026-03-11 00:00:00"])
    assert len(window_mod.apply_time_of_day(table, NIGHT_START, NIGHT_END)) == 1


def test_the_last_minute_before_midnight_is_inside_the_night_shift():
    table = _table(["2026-03-10 23:59:00"])
    assert len(window_mod.apply_time_of_day(table, NIGHT_START, NIGHT_END)) == 1


def test_noon_is_outside_the_night_shift():
    table = _table(["2026-03-10 12:00:00"])
    assert len(window_mod.apply_time_of_day(table, NIGHT_START, NIGHT_END)) == 0


# --- two calendar dates, one shift ----------------------------------------

def test_one_night_spans_two_dates():
    """The point of the whole feature, stated as plainly as it can be.

    An alarm at 22:00 on the 10th and one at 03:00 on the 11th are the same
    night's work. Both must survive. The 12:00 row on the 11th is day shift and
    must not.
    """
    table = _table([
        "2026-03-10 22:00:00",   # evening tail, night of the 10th
        "2026-03-11 03:00:00",   # morning head, same night
        "2026-03-11 12:00:00",   # day shift on the 11th
    ])
    kept = window_mod.apply_time_of_day(table, NIGHT_START, NIGHT_END)
    assert list(kept["ts_set"]) == [
        pd.Timestamp("2026-03-10 22:00:00"),
        pd.Timestamp("2026-03-11 03:00:00"),
    ]


def test_every_night_in_a_long_run_of_days_is_picked_up():
    """Thirty nights, two rows each, plus a noon row per day as a distractor."""
    stamps = []
    for day in range(1, 31):
        stamps.append("2026-03-%02d 20:00:00" % day)       # evening tail
        stamps.append("2026-03-%02d 02:00:00" % (day + 1))  # morning head
        stamps.append("2026-03-%02d 12:00:00" % day)       # day shift
    table = _table(stamps)

    kept = window_mod.apply_time_of_day(table, NIGHT_START, NIGHT_END)
    assert len(kept) == 60
    # Not one noon row got through.
    assert (kept["ts_set"].dt.hour != 12).all()


def test_a_shift_that_crosses_a_month_end_is_not_special():
    """Nothing in the filter looks at the date, so month ends are ordinary."""
    table = _table(["2026-03-31 23:30:00", "2026-04-01 01:30:00"])
    assert len(window_mod.apply_time_of_day(table, NIGHT_START, NIGHT_END)) == 2


def test_a_shift_that_crosses_a_year_end_is_not_special():
    table = _table(["2026-12-31 23:30:00", "2027-01-01 01:30:00"])
    assert len(window_mod.apply_time_of_day(table, NIGHT_START, NIGHT_END)) == 2


def test_a_leap_day_is_not_special():
    table = _table(["2028-02-28 23:30:00", "2028-02-29 01:30:00"])
    assert len(window_mod.apply_time_of_day(table, NIGHT_START, NIGHT_END)) == 2


# --- the other shift patterns a fab actually runs -------------------------

def test_three_eight_hour_shifts_cover_the_day_exactly_once():
    """06-14, 14-22, 22-06. The third one wraps."""
    table = _table(_every_minute_of("2026-03-10"))
    first = _kept_minutes(table, 6 * 60, 14 * 60)
    second = _kept_minutes(table, 14 * 60, 22 * 60)
    third = _kept_minutes(table, 22 * 60, 6 * 60)

    assert len(first) == len(second) == len(third) == 480
    assert first & second == set()
    assert second & third == set()
    assert first & third == set()
    assert first | second | third == set(range(1440))


def test_a_shift_with_a_half_hour_boundary():
    """Some fabs hand over at 18:30, not 18:00."""
    table = _table(_every_minute_of("2026-03-10"))
    kept = _kept_minutes(table, 18 * 60 + 30, 6 * 60 + 30)
    assert len(kept) == 720
    assert (18 * 60 + 30) in kept
    assert (18 * 60 + 29) not in kept
    assert (6 * 60 + 29) in kept
    assert (6 * 60 + 30) not in kept


def test_night_shift_written_with_the_word_pm_style_hours():
    """6pm to 6am, typed the way the parser accepts it, is 18:00 to 06:00."""
    assert window_mod.parse_time_of_day("18:00") == NIGHT_START
    assert window_mod.parse_time_of_day("06:00") == NIGHT_END
    assert window_mod.time_of_day_label(NIGHT_START, NIGHT_END) == \
        "18:00 to 06:00 (crosses midnight)"


# --- the filter leaves the caller's table alone ---------------------------

def test_the_input_table_is_not_modified():
    table = _table(_every_minute_of("2026-03-10"))
    before = len(table)
    window_mod.apply_time_of_day(table, NIGHT_START, NIGHT_END)
    assert len(table) == before


def test_the_result_is_renumbered_from_zero():
    """Rows come back with a clean index, not the gapped one from filtering."""
    table = _table(_every_minute_of("2026-03-10"))
    kept = window_mod.apply_time_of_day(table, NIGHT_START, NIGHT_END)
    assert list(kept.index) == list(range(len(kept)))
