"""The trend page is what people actually look at, and it must work offline."""

import datetime
import re

import pytest

from fab_drivers.core.history import HistoryWriter
from fab_drivers.core.trend_page import (
    read_history, render_trend_page, write_trend_page,
)


def make_history(tmp_path, values, day=None, name="testdev", column="temp_k"):
    """Write a day of readings, one a minute. None means a failed reading."""
    day = day or datetime.date(2026, 9, 2)
    writer = HistoryWriter(tmp_path, name, [column])
    for minute, value in enumerate(values):
        when = datetime.datetime(day.year, day.month, day.day, 8, minute, 0)
        writer.append({column: value}, when=when)
    return writer


def test_it_reads_back_the_rows_it_was_given(tmp_path):
    make_history(tmp_path, [10.0, 11.0, 12.0])
    rows = read_history(tmp_path, "testdev", days=1,
                        today=datetime.date(2026, 9, 2))
    assert len(rows) == 3
    assert rows[0]["temp_k"] == "10.0"


def test_it_reads_several_days_oldest_first(tmp_path):
    make_history(tmp_path, [1.0], day=datetime.date(2026, 9, 1))
    make_history(tmp_path, [2.0], day=datetime.date(2026, 9, 2))
    rows = read_history(tmp_path, "testdev", days=2,
                        today=datetime.date(2026, 9, 2))
    assert [r["temp_k"] for r in rows] == ["1.0", "2.0"]


def test_a_missing_day_is_simply_absent(tmp_path):
    make_history(tmp_path, [1.0], day=datetime.date(2026, 9, 2))
    rows = read_history(tmp_path, "testdev", days=7,
                        today=datetime.date(2026, 9, 2))
    assert len(rows) == 1


def test_the_page_fetches_nothing_from_anywhere(tmp_path):
    # The rule for this whole repository. These machines have no internet, and a
    # page opened from disk could not load a neighbouring file anyway. If this
    # test ever fails, the page has stopped being self-contained.
    make_history(tmp_path, [10.0, 11.0])
    page = render_trend_page(
        read_history(tmp_path, "testdev", days=1, today=datetime.date(2026, 9, 2)),
        ["temp_k"], "Test device")

    assert "http://" not in page
    assert "https://" not in page
    assert "//cdn" not in page
    # No tag may pull in an outside file.
    assert not re.search(r"<script[^>]+src=", page)
    assert not re.search(r"<link[^>]+href=", page)
    assert not re.search(r"<img[^>]+src=", page)


def test_the_readings_are_in_the_page(tmp_path):
    make_history(tmp_path, [10.0, 20.0, 15.0])
    page = render_trend_page(
        read_history(tmp_path, "testdev", days=1, today=datetime.date(2026, 9, 2)),
        ["temp_k"], "Test device")

    # The summary reports the latest, the lowest and the highest.
    assert "<td>15</td>" in page
    assert "<td>10</td>" in page
    assert "<td>20</td>" in page


def test_a_gap_breaks_the_line_instead_of_drawing_through_it(tmp_path):
    # Drawing a straight line across a gap invents readings that were never
    # taken. It is the same mistake as writing the last value into the CSV, one
    # layer further on.
    make_history(tmp_path, [10.0, 11.0, None, 13.0, 14.0])
    page = render_trend_page(
        read_history(tmp_path, "testdev", days=1, today=datetime.date(2026, 9, 2)),
        ["temp_k"], "Test device")

    # Two runs of readings means two separate lines, not one.
    assert page.count("<polyline") == 2


def test_readings_with_no_gaps_are_a_single_line(tmp_path):
    make_history(tmp_path, [10.0, 11.0, 12.0])
    page = render_trend_page(
        read_history(tmp_path, "testdev", days=1, today=datetime.date(2026, 9, 2)),
        ["temp_k"], "Test device")
    assert page.count("<polyline") == 1


def test_a_lone_reading_between_gaps_is_drawn_as_a_dot(tmp_path):
    # A one point line would be invisible, and the reading would vanish.
    make_history(tmp_path, [None, 12.0, None])
    page = render_trend_page(
        read_history(tmp_path, "testdev", days=1, today=datetime.date(2026, 9, 2)),
        ["temp_k"], "Test device")
    assert "<circle" in page
    assert "<polyline" not in page


def test_a_column_with_no_readings_says_so_instead_of_breaking(tmp_path):
    make_history(tmp_path, [None, None])
    page = render_trend_page(
        read_history(tmp_path, "testdev", days=1, today=datetime.date(2026, 9, 2)),
        ["temp_k"], "Test device")
    assert "No readings in this window" in page
    assert "no data" in page


def test_an_empty_history_still_produces_a_readable_page(tmp_path):
    page = render_trend_page([], ["temp_k"], "Test device")
    assert "No readings found for this window" in page
    assert "Test device" in page


def test_a_flat_line_does_not_divide_by_zero(tmp_path):
    # Every reading identical means the lowest and the highest are the same.
    make_history(tmp_path, [7.0, 7.0, 7.0])
    page = render_trend_page(
        read_history(tmp_path, "testdev", days=1, today=datetime.date(2026, 9, 2)),
        ["temp_k"], "Test device")
    assert "<polyline" in page


def test_a_text_column_is_summarised_but_not_plotted(tmp_path):
    # Some readings are status words, not numbers. They belong in the table.
    writer = HistoryWriter(tmp_path, "testdev", ["state"])
    writer.append({"state": "cooling"},
                  when=datetime.datetime(2026, 9, 2, 8, 0, 0))
    page = render_trend_page(
        read_history(tmp_path, "testdev", days=1, today=datetime.date(2026, 9, 2)),
        ["state"], "Test device")
    assert "No readings in this window" in page


def test_the_device_name_is_escaped_not_injected(tmp_path):
    page = render_trend_page([], ["temp_k"], "<script>alert(1)</script>")
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;" in page


def test_writing_the_page_creates_the_file(tmp_path):
    make_history(tmp_path, [10.0, 11.0])
    out = tmp_path / "pages" / "testdev.html"
    written = write_trend_page(tmp_path, "testdev", ["temp_k"], out,
                               title="Test device", days=1,
                               today=datetime.date(2026, 9, 2))
    assert written.exists()
    assert "Test device" in written.read_text(encoding="utf-8")


# ---- the log scale, which pressure needs and temperature does not ----

def test_a_linear_axis_hides_a_pumpdown_and_a_log_axis_does_not(tmp_path):
    # This is the whole reason the generator learned about scales. The readings
    # cross five decades. On a linear axis every one of them below about 1 torr
    # lands on the bottom of the chart, so the part of the pumpdown that matters
    # is a flat line along the bottom edge.
    make_history(tmp_path, [7.5e2, 2.0e1, 4.0e-1, 6.0e-3, 9.0e-4],
                 column="p_torr")
    rows = read_history(tmp_path, "testdev", days=1,
                        today=datetime.date(2026, 9, 2))

    linear = render_trend_page(rows, ["p_torr"], "Gauge")
    logged = render_trend_page(rows, ["p_torr"], "Gauge",
                               scales={"p_torr": "log"})

    def y_values(page):
        points = re.search(r'<polyline class="line" points="([^"]+)"', page)
        return [float(pair.split(",")[1]) for pair in points.group(1).split()]

    linear_ys = y_values(linear)
    log_ys = y_values(logged)

    # On the linear chart the last four readings all land within five pixels of
    # the bottom, because 20 torr and 0.0009 torr are the same place once the
    # top of the axis is 750. The chart is 180 pixels tall inside its margins,
    # so that is under three percent of it for four decades of pumping.
    assert max(linear_ys[1:]) - min(linear_ys[1:]) < 5.0
    # On the log chart the same four readings are spread over most of the
    # height, which is the whole point.
    assert max(log_ys) - min(log_ys) > 100.0


def test_a_log_axis_labels_whole_decades(tmp_path):
    make_history(tmp_path, [1.0e-6, 1.0e-3], column="p_torr")
    page = render_trend_page(
        read_history(tmp_path, "testdev", days=1,
                     today=datetime.date(2026, 9, 2)),
        ["p_torr"], "Gauge", scales={"p_torr": "log"})
    assert "1E-06" in page
    assert "1E-03" in page
    assert "Log scale" in page


def test_a_gap_still_breaks_the_line_on_a_log_axis(tmp_path):
    # The gap rule does not bend for a different axis.
    make_history(tmp_path, [1.0e-3, 2.0e-4, None, 5.0e-6, 1.0e-6],
                 column="p_torr")
    page = render_trend_page(
        read_history(tmp_path, "testdev", days=1,
                     today=datetime.date(2026, 9, 2)),
        ["p_torr"], "Gauge", scales={"p_torr": "log"})
    assert page.count("<polyline") == 2


def test_a_zero_reading_becomes_a_gap_on_a_log_axis_and_is_counted(tmp_path):
    # A gauge that is switched off may report exactly zero, and there is no
    # place on a log axis to put it. Dropping it silently would be the same
    # mistake as trending it. So it becomes a gap and the page says how many.
    make_history(tmp_path, [1.0e-3, 9.0e-4, 0.0, 5.0e-4, 4.0e-4],
                 column="p_torr")
    page = render_trend_page(
        read_history(tmp_path, "testdev", days=1,
                     today=datetime.date(2026, 9, 2)),
        ["p_torr"], "Gauge", scales={"p_torr": "log"})
    assert "1 reading was zero or negative" in page
    # And it broke the line, rather than being joined across.
    assert page.count("<polyline") == 2


def test_a_column_of_nothing_but_zeroes_says_so_on_a_log_axis(tmp_path):
    make_history(tmp_path, [0.0, 0.0], column="p_torr")
    page = render_trend_page(
        read_history(tmp_path, "testdev", days=1,
                     today=datetime.date(2026, 9, 2)),
        ["p_torr"], "Gauge", scales={"p_torr": "log"})
    assert "No readings in this window that a log axis can show" in page


def test_a_single_reading_on_a_log_axis_gets_a_decade_of_room(tmp_path):
    # One reading sitting exactly on a power of ten would otherwise divide by
    # zero when the axis top and bottom came out the same.
    make_history(tmp_path, [1.0e-5], column="p_torr")
    page = render_trend_page(
        read_history(tmp_path, "testdev", days=1,
                     today=datetime.date(2026, 9, 2)),
        ["p_torr"], "Gauge", scales={"p_torr": "log"})
    assert "<circle" in page


def test_a_misspelled_column_in_the_scales_is_caught(tmp_path):
    # Otherwise the chart quietly stays linear and nothing says why.
    make_history(tmp_path, [1.0e-3], column="p_torr")
    rows = read_history(tmp_path, "testdev", days=1,
                        today=datetime.date(2026, 9, 2))
    with pytest.raises(ValueError) as problem:
        render_trend_page(rows, ["p_torr"], "Gauge", scales={"p_tor": "log"})
    assert "p_tor" in str(problem.value)


def test_an_unknown_scale_is_refused(tmp_path):
    make_history(tmp_path, [1.0e-3], column="p_torr")
    rows = read_history(tmp_path, "testdev", days=1,
                        today=datetime.date(2026, 9, 2))
    with pytest.raises(ValueError):
        render_trend_page(rows, ["p_torr"], "Gauge",
                          scales={"p_torr": "logarithmic"})


def test_a_tiny_number_is_summarised_in_scientific_notation(tmp_path):
    # 1e-9 torr printed as 0.00 was the old behaviour, and it made the summary
    # table useless for every gauge in the plan.
    make_history(tmp_path, [4.2e-9], column="p_torr")
    page = render_trend_page(
        read_history(tmp_path, "testdev", days=1,
                     today=datetime.date(2026, 9, 2)),
        ["p_torr"], "Gauge", scales={"p_torr": "log"})
    assert "4.20E-09" in page
    assert "<td>0.00</td>" not in page


def test_ordinary_numbers_are_still_shown_plainly(tmp_path):
    # The change to the summary must not turn a temperature into 7.73E+01.
    make_history(tmp_path, [77.35, 4.2])
    page = render_trend_page(
        read_history(tmp_path, "testdev", days=1,
                     today=datetime.date(2026, 9, 2)),
        ["temp_k"], "Monitor")
    assert "77.35" in page
    assert "E+" not in page


# ---------------------------------------------------------------------------
# Two lines on one chart
#
# A reading and the setpoint it is supposed to be holding belong on the same
# axes. On separate charts each one scales to its own values, so a setpoint
# that never moves fills its chart just as much as a temperature that has
# drifted, and the gap between them, which is the only thing worth looking at,
# is nowhere on the page.
# ---------------------------------------------------------------------------

def overlay_rows():
    """A reading drifting away from a setpoint that does not move."""
    return [
        {"timestamp": "2026-09-01 10:00:00", "Temp": "18.0", "Setpoint": "18.0"},
        {"timestamp": "2026-09-01 10:10:00", "Temp": "19.5", "Setpoint": "18.0"},
        {"timestamp": "2026-09-01 10:20:00", "Temp": "22.0", "Setpoint": "18.0"},
    ]


def test_an_overlaid_column_is_drawn_on_the_other_columns_chart():
    page = render_trend_page(overlay_rows(), ["Temp", "Setpoint"], "Chiller",
                             overlays={"Temp": "Setpoint"})
    # One chart, holding both names, and a legend saying which line is which.
    assert page.count("<svg") == 1
    assert "Temp and Setpoint" in page
    assert 'class="line alt"' in page
    assert 'class="key alt"' in page


def test_an_overlaid_column_still_gets_its_own_summary_row():
    # It has no chart of its own, but its latest, lowest and highest are still
    # worth having in the table.
    page = render_trend_page(overlay_rows(), ["Temp", "Setpoint"], "Chiller",
                             overlays={"Temp": "Setpoint"})
    assert "<td>Setpoint</td>" in page
    assert "<td>Temp</td>" in page


def test_both_lines_share_one_axis():
    # The whole point. The axis has to cover both series, so the gap between
    # them is to scale. If the axis only covered the first, the setpoint would
    # be drawn off the bottom of the chart.
    page = render_trend_page(overlay_rows(), ["Temp", "Setpoint"], "Chiller",
                             overlays={"Temp": "Setpoint"})
    # The axis runs from the lowest reading on either line to the highest.
    assert ">18<" in page or ">18.00<" in page
    assert ">22<" in page or ">22.00<" in page


def test_a_page_with_no_overlays_is_exactly_as_it_was():
    # Nine other drivers use this path and none of them asked for a change.
    page = render_trend_page(overlay_rows(), ["Temp", "Setpoint"], "Chiller")
    assert page.count("<svg") == 2
    assert 'class="line alt"' not in page
    assert "Temp and Setpoint" not in page


def test_a_misspelled_overlay_column_is_refused():
    # Silently dropping the second line would leave a page that looks finished
    # and answers the wrong question.
    with pytest.raises(ValueError) as caught:
        render_trend_page(overlay_rows(), ["Temp", "Setpoint"], "Chiller",
                          overlays={"Temp": "Set point"})
    assert "not being plotted" in str(caught.value)


def test_a_chain_of_overlays_is_refused():
    # Two lines on one axis is readable. Three is not, and a chain is a way of
    # asking for three without noticing.
    rows = [{"timestamp": "t", "A": "1", "B": "2", "C": "3"}]
    with pytest.raises(ValueError) as caught:
        render_trend_page(rows, ["A", "B", "C"], "Thing",
                          overlays={"A": "B", "B": "C"})
    assert "chain" in str(caught.value)


def test_a_gap_in_the_second_line_stays_a_gap():
    # Two readings each side of the hole, so each side is a line rather than a
    # lone dot. A single reading between two gaps is drawn as a dot instead,
    # which is a different case and is tested elsewhere.
    rows = [
        {"timestamp": "t1", "Temp": "18.0", "Setpoint": "18.0"},
        {"timestamp": "t2", "Temp": "18.5", "Setpoint": "18.0"},
        {"timestamp": "t3", "Temp": "19.0", "Setpoint": ""},
        {"timestamp": "t4", "Temp": "19.5", "Setpoint": "18.0"},
        {"timestamp": "t5", "Temp": "20.0", "Setpoint": "18.0"},
    ]
    page = render_trend_page(rows, ["Temp", "Setpoint"], "Chiller",
                             overlays={"Temp": "Setpoint"})
    # The setpoint is drawn as two runs with a break, not one line straight
    # through the hole.
    assert page.count('class="line alt"') == 2
