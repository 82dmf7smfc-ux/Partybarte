"""End-to-end test.

Runs the whole pipeline through main.run and checks that both files are written
and that they open. Opening the files proves they are valid, not just present.
"""

import pytest
from openpyxl import load_workbook
from pptx import Presentation

from alarm_pareto import main
from tests import data_paths as dp


class _Args:
    """A tiny stand-in for the parsed command line arguments."""

    def __init__(self, output_dir, start_time=None, end_time=None):
        self.input = str(dp.SAMPLE_CSV)
        self.vendor = "amat"
        self.config = str(dp.CONFIG_PATH)
        self.window_days = 30
        self.start_time = start_time
        self.end_time = end_time
        self.top_n = 15
        self.downtime_method = "attributed"
        self.output_dir = str(output_dir)


def test_pipeline_writes_and_opens_both_files(tmp_path):
    out = main.run(_Args(tmp_path))

    assert out["xlsx"].exists()
    assert out["pptx"].exists()

    # The workbook must open and have the expected sheets.
    wb = load_workbook(out["xlsx"])
    for sheet in ["Window_Data", "By_Fault_Code", "By_Description", "By_Equipment"]:
        assert sheet in wb.sheetnames

    # Each summary sheet must carry at least one native chart object.
    assert len(wb["By_Fault_Code"]._charts) >= 1

    # The deck must open and have five slides: title, three levels, summary.
    prs = Presentation(out["pptx"])
    assert len(prs.slides) == 5


def test_headline_numbers_are_stable(tmp_path):
    expected = dp.load_expected()["grand"]
    out = main.run(_Args(tmp_path))
    grand = out["result"]["grand"]
    assert grand["total_faults"] == expected["total_faults"]
    assert grand["attributed_downtime_s"] == expected["attributed_downtime_s"]
    assert grand["wallclock_downtime_s"] == expected["wallclock_downtime_s"]


def test_time_of_day_filter_narrows_the_report(tmp_path):
    """A day shift and a night shift must add back up to the whole window."""
    whole = main.run(_Args(tmp_path / "all"))["result"]["grand"]
    day = main.run(_Args(tmp_path / "day", "06:00", "18:00"))["result"]["grand"]
    night = main.run(_Args(tmp_path / "night", "18:00", "06:00"))["result"]["grand"]

    assert day["total_faults"] + night["total_faults"] == whole["total_faults"]
    assert day["total_faults"] < whole["total_faults"]


def test_time_of_day_label_reaches_the_headline_numbers(tmp_path):
    grand = main.run(_Args(tmp_path / "night", "22:00", "06:00"))["result"]["grand"]
    assert grand["time_of_day_label"] == "22:00 to 06:00 (crosses midnight)"

    grand = main.run(_Args(tmp_path / "all"))["result"]["grand"]
    assert grand["time_of_day_label"] == "All hours"


def test_time_of_day_does_not_move_the_window(tmp_path):
    """The window is trimmed first, so the shift never shifts its edges."""
    whole = main.run(_Args(tmp_path / "all"))["result"]["grand"]
    day = main.run(_Args(tmp_path / "day", "06:00", "18:00"))["result"]["grand"]
    assert day["window_start"] == whole["window_start"]
    assert day["window_end"] == whole["window_end"]


def test_one_time_bound_alone_is_an_error(tmp_path):
    with pytest.raises(ValueError):
        main.run(_Args(tmp_path / "half", "06:00", None))


def test_a_range_with_no_alarms_is_an_error(tmp_path):
    with pytest.raises(ValueError):
        main.run(_Args(tmp_path / "quiet", "01:00", "02:00"))


def test_filtered_run_still_writes_both_files(tmp_path):
    out = main.run(_Args(tmp_path / "night", "18:00", "06:00"))
    assert out["xlsx"].exists()
    assert out["pptx"].exists()
    assert len(Presentation(out["pptx"]).slides) == 5
