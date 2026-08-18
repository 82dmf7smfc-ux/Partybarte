"""Check the ranking itself, not just the group totals.

The other tests check how much downtime each fault caused. This one checks the
order they are listed in, the percent of the total each one carries, the running
cumulative percent, and the "Other" bucket that holds everything past the top N.

That matters because a Pareto chart is read from the top down and the cumulative
line is the whole point of it. Two tools could agree on every total and still
draw different charts.

Every number here comes from the same golden files the browser tool is checked
against by tools/check_parity.mjs, so one set of hand-worked numbers governs
both tools.

The ranking is deliberately checked at a small top N so the "Other" bucket is
exercised. Users hit that bucket at the default of 15 whenever a tool has more
than 15 distinct faults.
"""

import json

import pytest

from alarm_pareto import aggregate as agg
from alarm_pareto import normalize as nz
from alarm_pareto import parse as parse_mod
from alarm_pareto import window as window_mod
from tests import data_paths as dp

# The three golden logs. Each is (name, log file, vendor block, window days).
SCENARIOS = [
    ("duration log", dp.SAMPLE_CSV, "amat", 30, dp.EXPECTED_JSON),
    ("set and clear log", dp.SETCLEAR_CSV, "amat_setclear_example", 30, dp.EXPECTED_SETCLEAR_JSON),
    ("daylight saving log", dp.DST_CSV, "amat_setclear_example", 365, dp.EXPECTED_DST_JSON),
]

LEVELS = ["fault_code", "description", "equipment"]

# What the percent columns are called in each ranked table. The browser tool
# calls them pct and cum in both, so the test maps one onto the other.
PCT_COLUMNS = {
    "by_count": ("count_pct", "cum_count_pct"),
    "by_downtime": ("downtime_pct", "cum_downtime_pct"),
}


def _run(csv_path, vendor, window_days, top_n, method):
    """Run the pipeline and return the aggregate result."""
    vendor_config = parse_mod.load_vendor_config(str(dp.CONFIG_PATH), vendor)
    raw = parse_mod.read_log(str(csv_path), vendor_config)
    table, mode = nz.normalize(raw, vendor_config)
    windowed, start, end = window_mod.apply_window(table, window_days)
    return agg.aggregate(
        windowed, mode, vendor_config, start, end,
        window_days=window_days, top_n=top_n, downtime_method=method,
    )


def _rows(result, level, which):
    """Turn one ranked table into the row shape the golden files use."""
    table = result["levels"][level][which]
    pct_col, cum_col = PCT_COLUMNS[which]
    out = []
    for _, row in table.iterrows():
        out.append({
            "rank": int(row["rank"]),
            "key": str(row[level]),
            "count": int(row["count"]),
            "attributed_s": float(row["attributed_s"]),
            "wallclock_s": float(row["wallclock_s"]),
            "pct": float(row[pct_col]),
            "cum": float(row[cum_col]),
        })
    return out


@pytest.mark.parametrize("name,csv_path,vendor,window_days,golden_path", SCENARIOS)
def test_ranking_matches_the_golden_file(name, csv_path, vendor, window_days, golden_path):
    expected = json.loads(golden_path.read_text(encoding="utf-8"))
    ranking = expected["ranking"]
    result = _run(csv_path, vendor, window_days, ranking["top_n"], ranking["method"])

    for level in LEVELS:
        for which in ["by_count", "by_downtime"]:
            actual_rows = _rows(result, level, which)
            expected_rows = ranking[level][which]
            where = "%s %s %s" % (name, level, which)

            assert len(actual_rows) == len(expected_rows), where
            # Order is part of the answer, so compare row by row.
            for actual, wanted in zip(actual_rows, expected_rows):
                assert actual["rank"] == wanted["rank"], where
                assert actual["key"] == wanted["key"], where
                assert actual["count"] == wanted["count"], where
                for field in ["attributed_s", "wallclock_s", "pct", "cum"]:
                    assert actual[field] == pytest.approx(wanted[field], abs=1e-6), (
                        "%s row %s field %s" % (where, wanted["key"], field)
                    )


def test_ties_are_broken_by_name_not_by_file_order():
    """Two faults with the same count must always list in the same order.

    Without an explicit tie-break, pandas would order these by however it
    grouped them and the browser tool would order them by however they appeared
    in the file. Both are defensible and they disagree.
    """
    expected = json.loads(dp.EXPECTED_JSON.read_text(encoding="utf-8"))
    rows = expected["ranking"]["equipment"]["by_count"]
    result = _run(dp.SAMPLE_CSV, "amat", 30, expected["ranking"]["top_n"],
                  expected["ranking"]["method"])
    actual = _rows(result, "equipment", "by_count")

    # CH-B and CH-C both have four faults. CH-B must come first, by name.
    assert [r["key"] for r in actual] == [r["key"] for r in rows]
    assert actual[1]["key"] == "CH-B"


# ---------------------------------------------------------------------------
# Timestamps.
# ---------------------------------------------------------------------------

def test_a_date_that_does_not_exist_is_rejected():
    """February 30th must be dropped, not nudged to March 2nd.

    The browser tool used to roll impossible dates forward, which invented an
    alarm that never happened. Both tools now drop the row.
    """
    result = _run(dp.DST_CSV, "amat_setclear_example", 365, 100, agg.METHOD_ATTRIBUTED)
    codes = set(result["occurrences"]["fault_code"])
    assert "E303" not in codes
    assert result["grand"]["total_faults"] == 3


def test_downtime_across_a_daylight_saving_change_is_clock_time():
    """An alarm spanning a daylight saving change is measured on the clock.

    The log has no timezone in it, so both tools treat the times as plain clock
    numbers. 01:30 to 03:30 is two hours, whatever the reading machine is set
    to. The browser tool used to read local time and get one hour here.
    """
    expected = json.loads(dp.EXPECTED_DST_JSON.read_text(encoding="utf-8"))
    result = _run(dp.DST_CSV, "amat_setclear_example", 365, 100, agg.METHOD_ATTRIBUTED)

    occ = result["occurrences"]
    spring = occ[occ["fault_code"] == "E101"]
    autumn = occ[occ["fault_code"] == "E202"]
    assert float(spring["duration_s"].iloc[0]) == 7200.0
    assert float(autumn["duration_s"].iloc[0]) == 5400.0
    assert result["grand"]["attributed_downtime_s"] == pytest.approx(
        expected["grand"]["attributed_downtime_s"]
    )
