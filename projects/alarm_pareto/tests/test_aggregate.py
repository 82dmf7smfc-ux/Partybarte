"""Tests for the ranking and downtime math.

The most important test here is the overlap merge. Two alarms that overlap must
not be double counted in the true wall-clock number.
"""

import pandas as pd

from alarm_pareto import aggregate as agg
from alarm_pareto import normalize as nz
from alarm_pareto import parse as parse_mod
from alarm_pareto import window as window_mod
from tests import data_paths as dp


def _ts(text):
    return pd.Timestamp(text)


# ---- Unit tests for the overlap merge helper ----

def test_merge_overlapping_intervals_counts_shared_time_once():
    # 10:00-14:00 is 4 hours. 12:00-15:00 is 3 hours. They overlap.
    # The real down time is 10:00-15:00, which is 5 hours = 18000 seconds.
    intervals = [
        (_ts("2026-02-10 10:00:00"), _ts("2026-02-10 14:00:00")),
        (_ts("2026-02-10 12:00:00"), _ts("2026-02-10 15:00:00")),
    ]
    assert agg.merged_seconds(intervals) == 18000.0


def test_merge_disjoint_intervals_adds_up():
    # Two separate one-hour blocks with a gap. Total is 2 hours.
    intervals = [
        (_ts("2026-02-10 10:00:00"), _ts("2026-02-10 11:00:00")),
        (_ts("2026-02-10 13:00:00"), _ts("2026-02-10 14:00:00")),
    ]
    assert agg.merged_seconds(intervals) == 7200.0


def test_merge_touching_intervals_is_one_block():
    # One block ends exactly when the next starts. That is a single 2 hour block.
    intervals = [
        (_ts("2026-02-10 10:00:00"), _ts("2026-02-10 11:00:00")),
        (_ts("2026-02-10 11:00:00"), _ts("2026-02-10 12:00:00")),
    ]
    assert agg.merged_seconds(intervals) == 7200.0


def test_merge_ignores_empty_and_bad_intervals():
    intervals = [
        (_ts("2026-02-10 10:00:00"), _ts("2026-02-10 10:00:00")),  # zero length
        (pd.NaT, _ts("2026-02-10 12:00:00")),                      # missing start
        (_ts("2026-02-10 13:00:00"), _ts("2026-02-10 14:00:00")),  # real one hour
    ]
    assert agg.merged_seconds(intervals) == 3600.0


# ---- Golden tests for the full aggregation ----

def _result(method=agg.METHOD_ATTRIBUTED):
    vendor_config = parse_mod.load_vendor_config(dp.CONFIG_PATH, "amat")
    raw = parse_mod.read_log(dp.SAMPLE_CSV, vendor_config)
    table, mode = nz.normalize(raw, vendor_config)
    windowed, start, end = window_mod.apply_window(table, window_days=30)
    return agg.aggregate(windowed, mode, vendor_config, start, end,
                         window_days=30, top_n=15, downtime_method=method)


def test_grand_totals_match_golden():
    expected = dp.load_expected()["grand"]
    grand = _result()["grand"]
    assert grand["total_faults"] == expected["total_faults"]
    assert grand["attributed_downtime_s"] == expected["attributed_downtime_s"]
    assert grand["wallclock_downtime_s"] == expected["wallclock_downtime_s"]


def test_attributed_is_more_than_wallclock():
    # Because of the overlap, attributed downtime must be larger than wall clock.
    grand = _result()["grand"]
    assert grand["attributed_downtime_s"] > grand["wallclock_downtime_s"]


def _table_to_dicts(df, level):
    """Turn a ranked table into simple lookup dicts keyed by the group value."""
    count = {}
    attributed = {}
    wall = {}
    for _, row in df.iterrows():
        key = row[level]
        count[key] = int(row["count"])
        attributed[key] = float(row["attributed_s"])
        wall[key] = float(row["wallclock_s"])
    return count, attributed, wall


def test_each_level_matches_golden():
    expected = dp.load_expected()
    result = _result()
    for level in agg.GROUPING_LEVELS:
        # The by_count table holds every group, so we read the measures from it.
        df = result["levels"][level]["by_count"]
        count, attributed, wall = _table_to_dicts(df, level)
        exp = expected[level]
        assert count == exp["count"], level
        assert attributed == {k: float(v) for k, v in exp["attributed_s"].items()}, level
        assert wall == {k: float(v) for k, v in exp["wallclock_s"].items()}, level


def test_cumulative_percent_reaches_100():
    result = _result()
    for level in agg.GROUPING_LEVELS:
        by_count = result["levels"][level]["by_count"]
        by_downtime = result["levels"][level]["by_downtime"]
        assert round(by_count["cum_count_pct"].iloc[-1], 2) == 100.0
        assert round(by_downtime["cum_downtime_pct"].iloc[-1], 2) == 100.0


def test_top_offenders_are_ranked_by_attributed():
    result = _result()
    names = [o["name"] for o in result["top_offenders"]]
    # E101 has the most attributed downtime, then E303, then E202.
    assert names == ["E101", "E303", "E202"]


def test_other_bucket_appears_when_top_n_is_small():
    # With top_n = 2 at the fault-code level there are 4 codes, so one Other row.
    vendor_config = parse_mod.load_vendor_config(dp.CONFIG_PATH, "amat")
    raw = parse_mod.read_log(dp.SAMPLE_CSV, vendor_config)
    table, mode = nz.normalize(raw, vendor_config)
    windowed, start, end = window_mod.apply_window(table, window_days=30)
    result = agg.aggregate(windowed, mode, vendor_config, start, end,
                           window_days=30, top_n=2, downtime_method=agg.METHOD_ATTRIBUTED)
    by_count = result["levels"]["fault_code"]["by_count"]
    assert "Other" in by_count["fault_code"].values
    # Top 2 codes plus one Other row is 3 rows total.
    assert len(by_count) == 3
    # The counts must still add up to the full 14 faults.
    assert by_count["count"].sum() == 14
