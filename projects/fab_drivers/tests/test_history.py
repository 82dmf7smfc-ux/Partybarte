"""The CSV history is what the trend model reads. Its shape must be stable."""

import csv
import datetime

import pytest

from fab_drivers.core.history import HistoryWriter


def read_rows(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.reader(f))


def test_a_new_file_gets_a_header_and_the_row(tmp_path):
    writer = HistoryWriter(tmp_path, "testdev", ["first_stage_k", "second_stage_k"])
    when = datetime.datetime(2026, 9, 2, 8, 0, 0)
    path = writer.append({"first_stage_k": 65.2, "second_stage_k": 12.4}, when=when)

    rows = read_rows(path)
    assert rows[0] == ["timestamp", "first_stage_k", "second_stage_k"]
    assert rows[1] == ["2026-09-02 08:00:00", "65.2", "12.4"]


def test_the_header_is_written_once_per_file(tmp_path):
    writer = HistoryWriter(tmp_path, "testdev", ["value"])
    when = datetime.datetime(2026, 9, 2, 8, 0, 0)
    writer.append({"value": 1}, when=when)
    path = writer.append({"value": 2}, when=when)

    rows = read_rows(path)
    assert len(rows) == 3
    assert rows[0][0] == "timestamp"


def test_a_new_day_starts_a_new_file_with_its_own_header(tmp_path):
    writer = HistoryWriter(tmp_path, "testdev", ["value"])
    writer.append({"value": 1}, when=datetime.datetime(2026, 9, 1, 23, 59, 0))
    writer.append({"value": 2}, when=datetime.datetime(2026, 9, 2, 0, 1, 0))

    for day in ["2026-09-01", "2026-09-02"]:
        rows = read_rows(tmp_path / ("testdev_%s.csv" % day))
        assert rows[0][0] == "timestamp"
        assert len(rows) == 2


def test_a_missing_reading_is_an_empty_cell_and_never_a_zero(tmp_path):
    # This is the one that protects the trend. A zero would look like a real
    # measurement and would drag any average built on the column.
    writer = HistoryWriter(tmp_path, "testdev", ["a", "b"])
    when = datetime.datetime(2026, 9, 2, 8, 0, 0)
    path = writer.append({"a": 5.0, "b": None}, when=when)

    rows = read_rows(path)
    assert rows[1] == ["2026-09-02 08:00:00", "5.0", ""]


def test_an_unknown_column_is_refused(tmp_path):
    # A typo in a column name would otherwise vanish silently and leave a gap in
    # the file that nobody notices until the trend looks wrong.
    writer = HistoryWriter(tmp_path, "testdev", ["a"])
    with pytest.raises(ValueError) as caught:
        writer.append({"typo": 1})
    assert "not columns of this file" in str(caught.value)


def test_the_timestamp_column_cannot_be_declared_twice(tmp_path):
    with pytest.raises(ValueError):
        HistoryWriter(tmp_path, "testdev", ["timestamp", "a"])
