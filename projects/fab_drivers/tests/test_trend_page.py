"""The trend page is what people actually look at, and it must work offline."""

import datetime
import re

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
