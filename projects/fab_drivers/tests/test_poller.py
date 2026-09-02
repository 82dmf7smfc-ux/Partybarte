"""The poller keeps the last good value and is honest about how old it is."""

import csv

import pytest

from fab_drivers.core.history import HistoryWriter
from fab_drivers.core.poller import MINIMUM_INTERVAL_S, Poller


def test_a_sweep_records_every_reading():
    poller = Poller({"a": lambda: 1.0, "b": lambda: 2.0})
    readings = poller.sweep()
    assert readings["a"].value == 1.0
    assert readings["b"].value == 2.0
    assert readings["a"].stale is False


def test_a_failed_reading_keeps_the_last_good_value_but_marks_it_stale():
    # A number from forty seconds ago is still useful, as long as the screen
    # says it is forty seconds old.
    values = [5.0, None]
    poller = Poller({"a": lambda: values.pop(0)})

    poller.sweep()
    assert poller.readings["a"].value == 5.0
    assert poller.readings["a"].stale is False

    poller.sweep()
    assert poller.readings["a"].value == 5.0     # the old value is still there
    assert poller.readings["a"].stale is True
    assert poller.readings["a"].error == "no reply"


def test_one_bad_reading_does_not_stop_the_others():
    # Four pumps share a terminal and one is powered down. The other three must
    # still be read.
    def explode():
        raise IOError("cable unplugged")

    poller = Poller({"good": lambda: 1.0, "bad": explode})
    readings = poller.sweep()

    assert readings["good"].value == 1.0
    assert readings["good"].stale is False
    assert readings["bad"].stale is True
    assert "cable unplugged" in readings["bad"].error


def test_a_reading_that_has_never_worked_starts_stale():
    poller = Poller({"a": lambda: None})
    assert poller.readings["a"].stale is True
    assert poller.readings["a"].value is None
    assert poller.readings["a"].age_s() is None


def test_the_age_of_a_reading_is_measured_from_when_it_was_taken():
    poller = Poller({"a": lambda: 1.0})
    poller.sweep()
    taken_at = poller.readings["a"].at
    assert poller.readings["a"].age_s(now=taken_at + 40) == pytest.approx(40)


def test_polling_faster_than_the_floor_is_quietly_slowed_down():
    # Polling a tool harder does not get better data. It gets a busier device
    # and more chance of colliding with the tool's own software.
    poller = Poller({"a": lambda: 1.0}, interval_s=0.5)
    assert poller.interval_s == MINIMUM_INTERVAL_S


def test_a_slower_interval_is_left_alone():
    poller = Poller({"a": lambda: 1.0}, interval_s=60)
    assert poller.interval_s == 60


def test_a_sweep_writes_one_history_row(tmp_path):
    history = HistoryWriter(tmp_path, "testdev", ["a", "b"])
    poller = Poller({"a": lambda: 1.0, "b": lambda: 2.0}, history=history)
    poller.sweep()

    path = list(tmp_path.glob("*.csv"))[0]
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    assert rows[0] == ["timestamp", "a", "b"]
    assert rows[1][1:] == ["1.0", "2.0"]


def test_a_stale_reading_writes_an_empty_cell_not_the_old_value(tmp_path):
    # The trend file must only hold numbers that were really measured at the
    # time on that row. Repeating the old value would invent a flat line that
    # never happened.
    values = [5.0, None]
    history = HistoryWriter(tmp_path, "testdev", ["a"])
    poller = Poller({"a": lambda: values.pop(0)}, history=history)

    poller.sweep()
    poller.sweep()

    path = list(tmp_path.glob("*.csv"))[0]
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    assert rows[1][1] == "5.0"
    assert rows[2][1] == ""


def test_run_forever_stops_after_the_requested_number_of_sweeps():
    slept = []
    poller = Poller({"a": lambda: 1.0}, interval_s=30)
    poller.run_forever(sweeps=3, sleep=slept.append)

    # Three sweeps, and it does not sit and wait after the last one.
    assert slept == [30.0, 30.0]


def test_a_poller_needs_something_to_read():
    with pytest.raises(ValueError):
        Poller({})
