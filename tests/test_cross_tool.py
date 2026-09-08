"""The Python half of the cross-tool agreement check.

The browser tool and the Python tool implement the same analysis twice. This
file checks the Python tool against tests/data/cross_tool_golden.json;
tests/browser/run.mjs checks the browser tool against the same file. Neither
suite can pass by agreeing with the other tool's bugs, because both are
measured against numbers worked out independently of both.

If you change the analysis and only one suite goes red, the red one is telling
you the tools have drifted. Fix the tool, not the fixture. The fixture changes
only when the definition of a number changes, and then by hand.
"""

import json

import pytest

from alarm_pareto import aggregate as agg
from alarm_pareto import main
from tests import data_paths as dp

GOLDEN_PATH = dp.SAMPLE_CSV.parent / "cross_tool_golden.json"


def load_golden():
    return json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))


GOLDEN = load_golden()


class _Args:
    """The parsed command line, as main.run wants it."""

    def __init__(self, output_dir, start_time=None, end_time=None):
        self.input = str(dp.SAMPLE_CSV)
        self.vendor = GOLDEN["vendor"]
        self.config = str(dp.CONFIG_PATH)
        self.window_days = GOLDEN["window"]["days"]
        self.start_time = start_time
        self.end_time = end_time
        self.top_n = 15
        self.downtime_method = agg.METHOD_ATTRIBUTED
        self.output_dir = str(output_dir)


def run_case(tmp_path, case, tag):
    return main.run(_Args(tmp_path / tag, case["tod_start"], case["tod_end"]))["result"]["grand"]


def case_ids():
    return [c["name"] for c in GOLDEN["cases"]]


# --- the fixture itself ----------------------------------------------------

def test_the_golden_file_describes_the_sample_we_actually_ship():
    """A fixture pointing at the wrong log would pass everything and mean nothing."""
    assert GOLDEN["input"] == dp.SAMPLE_CSV.name
    assert len(dp.SAMPLE_CSV.read_text(encoding="utf-8").strip().splitlines()) == \
        GOLDEN["window"]["rows_in_file"] + 1  # +1 for the header


# --- the fixed numbers -----------------------------------------------------

@pytest.mark.parametrize("case", GOLDEN["cases"], ids=case_ids())
def test_every_golden_case(tmp_path, case):
    """Each case in the fixture, checked field by field.

    Only the fields a case actually states are checked, so a case can pin the
    row count alone without being forced to spell out every hour.
    """
    grand = run_case(tmp_path, case, case["name"].replace(" ", "_").replace(",", ""))

    checks = [
        ("rows", "total_faults", None),
        ("attributed_hours", "attributed_downtime_hours", None),
        ("wallclock_hours", "wallclock_downtime_hours", None),
        ("in_range_hours", "in_range_downtime_hours", None),
        ("covered_hours", "range_hours", None),
        ("range_blocks", "range_blocks", None),
    ]
    for golden_key, grand_key, _ in checks:
        if golden_key not in case:
            continue
        assert grand[grand_key] == pytest.approx(case[golden_key]), \
            "%s: %s was %r, the golden file says %r" % (
                case["name"], grand_key, grand[grand_key], case[golden_key])


# --- the laws --------------------------------------------------------------

def _parts_grand(tmp_path, parts, tag):
    out = []
    for i, (start, end) in enumerate(parts):
        out.append(main.run(_Args(tmp_path / ("%s_%d" % (tag, i)), start, end))["result"]["grand"])
    return out


def test_shifts_partition_rows(tmp_path):
    law = GOLDEN["laws"]["shifts_partition_rows"]
    parts = _parts_grand(tmp_path, law["parts"], "rows2")
    assert sum(g["total_faults"] for g in parts) == law["equals_rows"]


def test_three_shifts_partition_rows(tmp_path):
    law = GOLDEN["laws"]["three_shifts_partition_rows"]
    parts = _parts_grand(tmp_path, law["parts"], "rows3")
    assert sum(g["total_faults"] for g in parts) == law["equals_rows"]


def test_shifts_partition_in_range(tmp_path):
    """The property that justifies the third downtime number existing."""
    law = GOLDEN["laws"]["shifts_partition_in_range"]
    parts = _parts_grand(tmp_path, law["parts"], "inr2")
    total = sum(g["in_range_downtime_hours"] for g in parts)
    assert total == pytest.approx(law["equals_hours"])


def test_three_shifts_partition_in_range(tmp_path):
    law = GOLDEN["laws"]["three_shifts_partition_in_range"]
    parts = _parts_grand(tmp_path, law["parts"], "inr3")
    total = sum(g["in_range_downtime_hours"] for g in parts)
    assert total == pytest.approx(law["equals_hours"])


def test_shifts_partition_covered_time(tmp_path):
    law = GOLDEN["laws"]["shifts_partition_covered_time"]
    parts = _parts_grand(tmp_path, law["parts"], "cov2")
    assert sum(g["range_hours"] for g in parts) == pytest.approx(law["equals_hours"])


@pytest.mark.parametrize("case", GOLDEN["cases"], ids=case_ids())
def test_in_range_never_exceeds_covered_time(tmp_path, case):
    """The one bound in-range genuinely has. It is not bounded by the other two."""
    grand = run_case(tmp_path, case, "bound_" + case["name"].replace(" ", "_").replace(",", ""))
    assert grand["in_range_downtime_hours"] <= grand["range_hours"] + 1e-9
    assert 0 <= grand["in_range_downtime_pct"] <= 100


def test_in_range_may_exceed_wall_clock(tmp_path):
    """Guard against anyone "tidying up" by asserting the wrong bound.

    On second shift the in-range number is larger than both other numbers,
    because a fault that started on first shift was still running at 14:00. A
    test asserting in_range <= wallclock would pass on most of this sample and
    be wrong. This pins the counterexample so nobody adds that assertion.
    """
    case = next(c for c in GOLDEN["cases"] if c["name"].startswith("second shift"))
    grand = run_case(tmp_path, case, "second_shift_bound")
    assert grand["in_range_downtime_hours"] > grand["wallclock_downtime_hours"]
    assert grand["in_range_downtime_hours"] > grand["attributed_downtime_hours"]
