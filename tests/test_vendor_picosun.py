"""Tests for the Picosun vendor blocks and the paired-interval downtime path.

The Picosun block is the first one that ships with both an alarm-on and an
alarm-off time on the same row. That is the "paired interval" shape. These
tests prove the shipped config is well formed and that the analysis handles
that shape correctly, including the overlap merge for wall-clock downtime.

The expected numbers below were worked out by hand from
tests/data/sample_picosun_log.csv. If a code change makes one fail, the change
altered the analysis.
"""

import json

import pytest

from alarm_pareto import aggregate as agg
from alarm_pareto import normalize as nz
from alarm_pareto import parse as parse_mod
from alarm_pareto import window as window_mod
from tests import data_paths as dp

SECONDS_PER_HOUR = 3600.0


def _shipped_vendor_names():
    """Every real vendor block in the shipped config. Help keys start with '_'."""
    blocks = json.loads(dp.CONFIG_PATH.read_text(encoding="utf-8"))
    return [name for name in blocks if not name.startswith("_")]


def _analyze(vendor):
    """Run the pipeline up to the rankings for the Picosun sample log."""
    vendor_config = parse_mod.load_vendor_config(dp.CONFIG_PATH, vendor)
    raw = parse_mod.read_log(dp.SAMPLE_PICOSUN_CSV, vendor_config)
    table, mode = nz.normalize(raw, vendor_config)
    windowed, start, end = window_mod.apply_window(table, 30)
    return agg.aggregate(windowed, mode, vendor_config, start, end, window_days=30)


@pytest.mark.parametrize("vendor", _shipped_vendor_names())
def test_every_shipped_vendor_block_is_usable(vendor):
    # Each block must name a downtime shape the tool understands and must map
    # every internal name the rest of the pipeline requires.
    vendor_config = parse_mod.load_vendor_config(dp.CONFIG_PATH, vendor)
    mode = nz.detect_mode(vendor_config)
    assert mode in (nz.MODE_DURATION, nz.MODE_PAIRED_INTERVAL, nz.MODE_EVENT_PAIRING)

    mapped = vendor_config["columns"]
    for name in nz.REQUIRED_ALWAYS:
        assert name in mapped, "%s is missing '%s'" % (vendor, name)

    # A pairing key must itself be a mapped column, or pairing cannot run.
    for key in vendor_config.get("pairing_keys", []):
        assert key in mapped, "%s pairing key '%s' is not mapped" % (vendor, key)


def test_picosun_uses_the_paired_interval_mode():
    vendor_config = parse_mod.load_vendor_config(dp.CONFIG_PATH, "picosun")
    assert nz.detect_mode(vendor_config) == nz.MODE_PAIRED_INTERVAL


def test_picosun_setclear_example_uses_the_event_mode():
    vendor_config = parse_mod.load_vendor_config(dp.CONFIG_PATH, "picosun_setclear_example")
    assert nz.detect_mode(vendor_config) == nz.MODE_EVENT_PAIRING


def test_window_drops_the_january_row():
    # The newest onset is 2026-02-21, so the 30 day window starts 2026-01-22.
    # The January row falls outside it. Seven of the eight rows remain.
    result = _analyze("picosun")
    assert result["grand"]["total_faults"] == 7


def test_duration_comes_from_the_two_timestamps():
    # Attributed downtime credits every alarm its own full length.
    # 4h + 3h + 0.5h + 1h + 2h + 1h + 0.5h = 12h.
    result = _analyze("picosun")
    assert result["grand"]["attributed_downtime_s"] == pytest.approx(12 * SECONDS_PER_HOUR)


def test_overlapping_alarms_are_merged_for_wallclock():
    # The two P-101 alarms on 2026-02-10 overlap: 10:00-14:00 and 12:00-15:00.
    # Attributed counts 7h. Wall clock counts 10:00-15:00, which is 5h. So the
    # grand wall-clock total is 12h - 7h + 5h = 10h.
    result = _analyze("picosun")
    assert result["grand"]["wallclock_downtime_s"] == pytest.approx(10 * SECONDS_PER_HOUR)


def test_fault_code_ranking_is_by_downtime():
    # P-101 leads on both count and downtime.
    result = _analyze("picosun")
    by_downtime = result["levels"]["fault_code"]["by_downtime"]
    top = by_downtime.iloc[0]
    assert top["fault_code"] == "P-101"
    assert int(top["count"]) == 3
    # 4h + 3h + 1h attributed, but 5h + 1h once the overlap is merged.
    assert float(top["attributed_hours"]) == pytest.approx(8.0)
    assert float(top["wallclock_hours"]) == pytest.approx(6.0)


def test_equipment_level_splits_the_two_reactors():
    result = _analyze("picosun")
    by_count = result["levels"]["equipment"]["by_count"]
    counts = dict(zip(by_count["equipment"], by_count["count"]))
    assert counts == {"R1": 3, "R2": 4}
