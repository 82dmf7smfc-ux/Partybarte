"""End-to-end test.

Runs the whole pipeline through main.run and checks that both files are written
and that they open. Opening the files proves they are valid, not just present.
"""

from openpyxl import load_workbook
from pptx import Presentation

from alarm_pareto import main
from tests import data_paths as dp


class _Args:
    """A tiny stand-in for the parsed command line arguments."""

    def __init__(self, output_dir):
        self.input = str(dp.SAMPLE_CSV)
        self.vendor = "amat"
        self.config = str(dp.CONFIG_PATH)
        self.window_days = 30
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
