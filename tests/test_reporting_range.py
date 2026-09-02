"""Tests for the reporting range and the in-range downtime number.

The reporting range is the list of blocks of clock time a report covers. With
no shift chosen it is one block, the window. With a night shift chosen it is
one block per night, each running 18:00 to 06:00 across two dates.

The in-range downtime number is wall-clock downtime measured against that list:
every alarm is cut down to the parts that fall inside a block, then overlaps are
merged. It is the answer to "how much of the night shift was the tool down",
which neither of the other two numbers gives.
"""

import pandas as pd
import pytest

from alarm_pareto import aggregate as agg
from alarm_pareto import reporting_range as rr

DAY_START, DAY_END = 6 * 60, 18 * 60      # 06:00 to 18:00
NIGHT_START, NIGHT_END = 18 * 60, 6 * 60  # 18:00 to 06:00, wraps


def ts(text):
    return pd.Timestamp(text)


def hours(seconds):
    return round(seconds / 3600.0, 6)


# --- building the range ----------------------------------------------------

def test_no_shift_gives_one_block_covering_the_window():
    ranges = rr.build_ranges(ts("2026-03-01 00:00"), ts("2026-03-31 00:00"))
    assert ranges == [(ts("2026-03-01 00:00"), ts("2026-03-31 00:00"))]
    assert hours(rr.total_seconds(ranges)) == 30 * 24


def test_a_zero_length_window_covers_nothing():
    assert rr.build_ranges(ts("2026-03-01 00:00"), ts("2026-03-01 00:00")) == []


def test_a_backwards_window_is_an_error():
    with pytest.raises(ValueError):
        rr.build_ranges(ts("2026-03-31 00:00"), ts("2026-03-01 00:00"))


def test_day_shift_gives_one_block_per_day():
    # Three whole days, 00:00 on the 1st to 00:00 on the 4th.
    ranges = rr.build_ranges(ts("2026-03-01 00:00"), ts("2026-03-04 00:00"),
                             DAY_START, DAY_END)
    assert len(ranges) == 3
    assert ranges[0] == (ts("2026-03-01 06:00"), ts("2026-03-01 18:00"))
    assert ranges[2] == (ts("2026-03-03 06:00"), ts("2026-03-03 18:00"))
    assert hours(rr.total_seconds(ranges)) == 36  # three twelve hour days


def test_night_shift_blocks_span_two_dates_each():
    """The heart of it. Each block starts on one day and ends on the next."""
    ranges = rr.build_ranges(ts("2026-03-01 00:00"), ts("2026-03-04 00:00"),
                             NIGHT_START, NIGHT_END)
    # The night that began on Feb 28 runs into the window until 06:00 on Mar 1,
    # so it counts as a partial block. Then the nights of the 1st, 2nd and 3rd.
    assert ranges[0] == (ts("2026-03-01 00:00"), ts("2026-03-01 06:00"))
    assert ranges[1] == (ts("2026-03-01 18:00"), ts("2026-03-02 06:00"))
    assert ranges[2] == (ts("2026-03-02 18:00"), ts("2026-03-03 06:00"))
    assert ranges[3] == (ts("2026-03-03 18:00"), ts("2026-03-04 00:00"))
    assert len(ranges) == 4


def test_blocks_are_sorted_and_never_overlap():
    ranges = rr.build_ranges(ts("2026-03-01 09:13"), ts("2026-04-05 21:47"),
                             NIGHT_START, NIGHT_END)
    for earlier, later in zip(ranges, ranges[1:]):
        assert earlier[0] < later[0]      # sorted by start
        assert earlier[1] <= later[0]     # and disjoint
    for start, end in ranges:
        assert end > start                # no empty blocks


def test_blocks_never_stick_out_past_the_window():
    start, end = ts("2026-03-01 09:13"), ts("2026-03-20 21:47")
    for tod in [(DAY_START, DAY_END), (NIGHT_START, NIGHT_END), (None, None)]:
        for block_start, block_end in rr.build_ranges(start, end, *tod):
            assert block_start >= start
            assert block_end <= end


def test_a_night_that_began_before_the_window_still_counts_its_tail():
    """The window opens at 02:00, mid-night-shift. Those two hours count."""
    ranges = rr.build_ranges(ts("2026-03-02 02:00"), ts("2026-03-02 12:00"),
                             NIGHT_START, NIGHT_END)
    assert ranges == [(ts("2026-03-02 02:00"), ts("2026-03-02 06:00"))]


def test_thirty_nights_add_up_to_the_expected_hours():
    ranges = rr.build_ranges(ts("2026-03-01 18:00"), ts("2026-03-31 06:00"),
                             NIGHT_START, NIGHT_END)
    assert len(ranges) == 30
    assert hours(rr.total_seconds(ranges)) == 30 * 12


# --- clipping alarms against the range ------------------------------------

def test_an_alarm_wholly_inside_a_block_is_untouched():
    ranges = rr.build_ranges(ts("2026-03-01 00:00"), ts("2026-03-04 00:00"),
                             NIGHT_START, NIGHT_END)
    pieces = rr.clip_intervals([(ts("2026-03-01 20:00"), ts("2026-03-01 22:00"))], ranges)
    assert pieces == [(ts("2026-03-01 20:00"), ts("2026-03-01 22:00"))]


def test_an_alarm_wholly_outside_every_block_disappears():
    ranges = rr.build_ranges(ts("2026-03-01 00:00"), ts("2026-03-04 00:00"),
                             NIGHT_START, NIGHT_END)
    assert rr.clip_intervals([(ts("2026-03-01 12:00"), ts("2026-03-01 13:00"))], ranges) == []


def test_an_alarm_straddling_the_start_of_a_shift_is_cut():
    """17:50 plus four hours: ten minutes of it are day, the rest is night."""
    ranges = rr.build_ranges(ts("2026-03-01 00:00"), ts("2026-03-04 00:00"),
                             NIGHT_START, NIGHT_END)
    pieces = rr.clip_intervals([(ts("2026-03-01 17:50"), ts("2026-03-01 21:50"))], ranges)
    assert pieces == [(ts("2026-03-01 18:00"), ts("2026-03-01 21:50"))]
    assert hours(agg.merged_seconds(pieces)) == round(3 + 50 / 60.0, 6)


def test_one_long_alarm_can_produce_several_pieces():
    """An alarm running two and a half days touches three separate nights."""
    ranges = rr.build_ranges(ts("2026-03-01 00:00"), ts("2026-03-05 00:00"),
                             NIGHT_START, NIGHT_END)
    pieces = rr.clip_intervals([(ts("2026-03-01 12:00"), ts("2026-03-04 00:00"))], ranges)
    # Nights of the 1st, 2nd and 3rd, the last one cut off at the window end.
    assert len(pieces) == 3
    assert hours(agg.merged_seconds(pieces)) == 12 + 12 + 6


def test_an_alarm_with_no_end_time_is_skipped():
    ranges = rr.build_ranges(ts("2026-03-01 00:00"), ts("2026-03-04 00:00"))
    assert rr.clip_intervals([(ts("2026-03-01 20:00"), pd.NaT)], ranges) == []


def test_a_zero_length_alarm_is_skipped():
    ranges = rr.build_ranges(ts("2026-03-01 00:00"), ts("2026-03-04 00:00"))
    assert rr.clip_intervals([(ts("2026-03-01 20:00"), ts("2026-03-01 20:00"))], ranges) == []


def test_clipping_against_an_empty_range_gives_nothing():
    assert rr.clip_intervals([(ts("2026-03-01 20:00"), ts("2026-03-01 22:00"))], []) == []


def test_clipped_time_never_exceeds_the_range_length():
    """However much downtime you throw at it, it cannot exceed the clock."""
    ranges = rr.build_ranges(ts("2026-03-01 00:00"), ts("2026-03-08 00:00"),
                             NIGHT_START, NIGHT_END)
    # One enormous alarm covering the entire window, several times over.
    pieces = rr.clip_intervals([(ts("2026-02-01 00:00"), ts("2026-04-01 00:00"))] * 5, ranges)
    assert agg.merged_seconds(pieces) == rr.total_seconds(ranges)


# --- the property that makes the number trustworthy -----------------------

def test_day_and_night_in_range_downtime_add_up_to_the_whole_window():
    """The clock does not care which shift you asked for.

    Downtime measured against the day shift plus downtime measured against the
    night shift must equal downtime measured against the whole window. This is
    the property the other two downtime numbers cannot offer, and it is the
    reason this one exists.
    """
    window = (ts("2026-03-01 00:00"), ts("2026-03-08 00:00"))
    alarms = [
        (ts("2026-03-01 17:50"), ts("2026-03-01 21:50")),  # straddles 18:00
        (ts("2026-03-02 05:00"), ts("2026-03-02 08:00")),  # straddles 06:00
        (ts("2026-03-03 12:00"), ts("2026-03-03 13:00")),  # all day shift
        (ts("2026-03-04 23:00"), ts("2026-03-05 01:00")),  # all night, two dates
        (ts("2026-03-05 12:00"), ts("2026-03-07 12:00")),  # two whole days
    ]

    def measured(tod):
        ranges = rr.build_ranges(window[0], window[1], *tod)
        return agg.merged_seconds(rr.clip_intervals(alarms, ranges))

    whole = measured((None, None))
    day = measured((DAY_START, DAY_END))
    night = measured((NIGHT_START, NIGHT_END))

    assert day + night == pytest.approx(whole)
    assert day > 0 and night > 0


def test_three_eight_hour_shifts_also_add_up():
    window = (ts("2026-03-01 00:00"), ts("2026-03-08 00:00"))
    alarms = [
        (ts("2026-03-01 05:00"), ts("2026-03-01 23:00")),
        (ts("2026-03-03 21:00"), ts("2026-03-04 07:00")),
        (ts("2026-03-06 13:30"), ts("2026-03-06 14:30")),
    ]

    def measured(tod):
        ranges = rr.build_ranges(window[0], window[1], *tod)
        return agg.merged_seconds(rr.clip_intervals(alarms, ranges))

    total = (measured((6 * 60, 14 * 60))
             + measured((14 * 60, 22 * 60))
             + measured((22 * 60, 6 * 60)))
    assert total == pytest.approx(measured((None, None)))


def test_in_range_never_exceeds_wall_clock_for_a_plain_window():
    """With no shift, clipping can only ever remove time, never add it."""
    window = (ts("2026-03-01 00:00"), ts("2026-03-08 00:00"))
    alarms = [
        (ts("2026-02-28 12:00"), ts("2026-03-01 12:00")),  # runs into the window
        (ts("2026-03-03 12:00"), ts("2026-03-03 15:00")),
        (ts("2026-03-07 12:00"), ts("2026-03-09 12:00")),  # runs off the end
    ]
    ranges = rr.build_ranges(*window)
    in_range = agg.merged_seconds(rr.clip_intervals(alarms, ranges))
    wallclock = agg.merged_seconds(alarms)
    assert in_range < wallclock
    assert in_range <= rr.total_seconds(ranges)


# --- the description string -----------------------------------------------

def test_describe_one_block():
    ranges = rr.build_ranges(ts("2026-03-01 00:00"), ts("2026-03-02 00:00"))
    assert rr.describe(ranges) == "24.0 hours of clock time, in one continuous block"


def test_describe_many_blocks():
    ranges = rr.build_ranges(ts("2026-03-01 18:00"), ts("2026-03-04 06:00"),
                             NIGHT_START, NIGHT_END)
    assert rr.describe(ranges) == "36.0 hours of clock time, in 3 blocks"


def test_describe_nothing():
    assert rr.describe([]) == "No time covered"
