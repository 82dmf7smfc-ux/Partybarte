"""Tests for the two downtime shapes that had no coverage.

The duration shape, where the log already says how long each alarm lasted, is
covered by the other test files. The two shapes tested here were not:

- Event pairing. Each alarm appears as two rows, a set and a clear, and the tool
  has to pair them up.
- Paired intervals. Each row carries both a set time and a clear time.

Event pairing is the harder of the two. Several alarms can be open at once, a
clear can arrive with no matching set, and a set can never clear at all. Each of
those cases is checked below.

The end-to-end event pairing numbers come from tests/data/expected_setclear.json.
The browser tool is checked against that same file by tools/check_parity.mjs, so
one set of hand-worked numbers governs both tools.

Note that the browser tool has no paired-interval mode. That shape is handled by
the Python tool only, so those tests have no browser counterpart.
"""

import pandas as pd
import pytest

from alarm_pareto import aggregate as agg
from alarm_pareto import normalize as nz
from alarm_pareto import parse as parse_mod
from alarm_pareto import window as window_mod
from tests import data_paths as dp

SETCLEAR_VENDOR = "amat_setclear_example"


def _run_setclear():
    """Run the pipeline over the set and clear sample log."""
    vendor_config = parse_mod.load_vendor_config(str(dp.CONFIG_PATH), SETCLEAR_VENDOR)
    raw = parse_mod.read_log(str(dp.SETCLEAR_CSV), vendor_config)
    table, mode = nz.normalize(raw, vendor_config)
    assert mode == nz.MODE_EVENT_PAIRING

    windowed, start, end = window_mod.apply_window(table, 30)
    result = agg.aggregate(
        windowed, mode, vendor_config, start, end,
        window_days=30, top_n=100, downtime_method=agg.METHOD_ATTRIBUTED,
    )
    return result, start, end


def _level_maps(result, level):
    """Pull count, attributed and wall-clock per group out of a ranked table."""
    table = result["levels"][level]["by_count"]
    return (
        dict(zip(table[level], table["count"])),
        dict(zip(table[level], table["attributed_s"])),
        dict(zip(table[level], table["wallclock_s"])),
    )


# ---------------------------------------------------------------------------
# Event pairing, end to end against the golden file.
# ---------------------------------------------------------------------------

def test_event_pairing_matches_the_golden_file():
    expected = dp.load_expected_setclear()
    result, start, end = _run_setclear()

    grand = result["grand"]
    assert grand["total_faults"] == expected["grand"]["total_faults"]
    assert grand["attributed_downtime_s"] == pytest.approx(expected["grand"]["attributed_downtime_s"])
    assert grand["wallclock_downtime_s"] == pytest.approx(expected["grand"]["wallclock_downtime_s"])

    assert str(start) == expected["window"]["window_start"]
    assert str(end) == expected["window"]["window_end"]

    for level in ["fault_code", "description", "equipment"]:
        counts, attributed, wallclock = _level_maps(result, level)
        assert counts == expected[level]["count"]
        for key, value in expected[level]["attributed_s"].items():
            assert attributed[key] == pytest.approx(value)
        for key, value in expected[level]["wallclock_s"].items():
            assert wallclock[key] == pytest.approx(value)


def test_a_clear_with_no_set_is_skipped():
    """E303 appears only as a clear. It must not become an occurrence."""
    result, _, _ = _run_setclear()
    codes = set(result["occurrences"]["fault_code"])
    assert "E303" not in codes


def test_a_set_that_never_clears_is_counted_with_zero_downtime():
    """E404 opens and never closes. It still counts, but adds no downtime."""
    result, _, _ = _run_setclear()
    occ = result["occurrences"]
    e404 = occ[occ["fault_code"] == "E404"]
    assert len(e404) == 1
    assert float(e404["duration_s"].iloc[0]) == 0.0


# ---------------------------------------------------------------------------
# Event pairing, focused cases built by hand.
# ---------------------------------------------------------------------------

def _events(rows):
    """Build a normalized event table from (time, code, equipment, state) rows."""
    table = pd.DataFrame(
        [
            {
                "ts_set": pd.Timestamp(t),
                "fault_code": code,
                "description": "text for " + code,
                "equipment": equip,
                "event_type": state,
            }
            for t, code, equip, state in rows
        ]
    )
    return table.sort_values("ts_set", kind="stable").reset_index(drop=True)


CONFIG = {"pairing_keys": ["equipment", "fault_code"]}


def test_a_clear_matches_the_most_recent_open_set():
    """Two sets open on the same key. The first clear closes the newer one.

    This is last in, first out. It matters when a fault re-fires before the
    first one is acknowledged. Pairing the wrong way around gives one very long
    alarm and one very short one instead of two believable ones.
    """
    occ = agg.build_occurrences(
        _events([
            ("2026-03-01 01:00:00", "E1", "CH-A", "set"),
            ("2026-03-01 02:00:00", "E1", "CH-A", "set"),
            ("2026-03-01 03:00:00", "E1", "CH-A", "clear"),
            ("2026-03-01 05:00:00", "E1", "CH-A", "clear"),
        ]),
        nz.MODE_EVENT_PAIRING,
        CONFIG,
    )
    durations = sorted(float(d) for d in occ["duration_s"])
    # The 02:00 set pairs with the 03:00 clear, which is one hour.
    # The 01:00 set pairs with the 05:00 clear, which is four hours.
    assert durations == [3600.0, 14400.0]


def test_alarms_on_different_equipment_do_not_pair_with_each_other():
    """The same fault code open on two chambers must stay separate."""
    occ = agg.build_occurrences(
        _events([
            ("2026-03-01 01:00:00", "E1", "CH-A", "set"),
            ("2026-03-01 02:00:00", "E1", "CH-B", "set"),
            ("2026-03-01 03:00:00", "E1", "CH-B", "clear"),
            ("2026-03-01 06:00:00", "E1", "CH-A", "clear"),
        ]),
        nz.MODE_EVENT_PAIRING,
        CONFIG,
    )
    by_equipment = dict(zip(occ["equipment"], occ["duration_s"]))
    assert float(by_equipment["CH-B"]) == 3600.0
    assert float(by_equipment["CH-A"]) == 18000.0


def test_unknown_event_markers_are_ignored():
    """A row that is neither a set nor a clear must not create an occurrence."""
    occ = agg.build_occurrences(
        _events([
            ("2026-03-01 01:00:00", "E1", "CH-A", "unknown"),
            ("2026-03-01 02:00:00", "E1", "CH-A", "set"),
            ("2026-03-01 03:00:00", "E1", "CH-A", "clear"),
        ]),
        nz.MODE_EVENT_PAIRING,
        CONFIG,
    )
    assert len(occ) == 1
    assert float(occ["duration_s"].iloc[0]) == 3600.0


def test_no_pairs_at_all_gives_an_empty_table_with_the_right_columns():
    """An all-orphan log must not crash the steps that come after."""
    occ = agg.build_occurrences(
        _events([("2026-03-01 01:00:00", "E1", "CH-A", "clear")]),
        nz.MODE_EVENT_PAIRING,
        CONFIG,
    )
    assert len(occ) == 0
    for column in ["fault_code", "description", "equipment", "ts_set", "ts_end", "duration_s"]:
        assert column in occ.columns


# ---------------------------------------------------------------------------
# Paired intervals. Each row carries both a set and a clear time.
# ---------------------------------------------------------------------------

def _intervals(rows):
    """Build a normalized table from (set time, clear time) pairs."""
    return pd.DataFrame(
        [
            {
                "ts_set": pd.Timestamp(start),
                "ts_clear": pd.NaT if clear is None else pd.Timestamp(clear),
                "fault_code": "E1",
                "description": "text for E1",
                "equipment": "CH-A",
            }
            for start, clear in rows
        ]
    )


def test_paired_interval_duration_is_clear_minus_set():
    occ = agg.build_occurrences(
        _intervals([("2026-03-01 01:00:00", "2026-03-01 03:30:00")]),
        nz.MODE_PAIRED_INTERVAL,
        {},
    )
    assert float(occ["duration_s"].iloc[0]) == 9000.0


def test_paired_interval_with_no_clear_time_credits_zero():
    """A blank clear time means the length is unknown. Zero is the safe answer.

    Guessing a duration here would inflate the downtime ranking, and the whole
    point of the ranking is to decide where to spend maintenance time.
    """
    occ = agg.build_occurrences(
        _intervals([("2026-03-01 01:00:00", None)]),
        nz.MODE_PAIRED_INTERVAL,
        {},
    )
    assert float(occ["duration_s"].iloc[0]) == 0.0


def test_paired_interval_with_a_clear_before_the_set_credits_zero():
    """A clear earlier than its set is bad data. It must never go negative."""
    occ = agg.build_occurrences(
        _intervals([("2026-03-01 05:00:00", "2026-03-01 01:00:00")]),
        nz.MODE_PAIRED_INTERVAL,
        {},
    )
    assert float(occ["duration_s"].iloc[0]) == 0.0


def test_paired_intervals_that_overlap_merge_for_wall_clock():
    """Overlapping alarms must not double count wall-clock time."""
    occ = agg.build_occurrences(
        _intervals([
            ("2026-03-01 01:00:00", "2026-03-01 04:00:00"),
            ("2026-03-01 03:00:00", "2026-03-01 06:00:00"),
        ]),
        nz.MODE_PAIRED_INTERVAL,
        {},
    )
    # Attributed credits each alarm its own three hours, so six hours total.
    assert float(occ["duration_s"].sum()) == 21600.0
    # Wall clock merges them into 01:00 to 06:00, which is five hours.
    pairs = list(zip(occ["ts_set"], occ["ts_end"]))
    assert agg.merged_seconds(pairs) == 18000.0
