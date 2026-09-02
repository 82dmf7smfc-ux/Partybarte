"""The audit log has to hold the exact bytes, including the ugly ones."""

import datetime

from fab_drivers.core.audit import AuditLog


def test_it_writes_one_file_per_day(tmp_path):
    log = AuditLog(tmp_path, "testdev")
    day_one = datetime.datetime(2026, 9, 1, 8, 0, 0)
    day_two = datetime.datetime(2026, 9, 2, 8, 0, 0)

    log.sent(b"$P01J\r", when=day_one)
    log.sent(b"$P01J\r", when=day_two)

    assert (tmp_path / "testdev_2026-09-01.log").exists()
    assert (tmp_path / "testdev_2026-09-02.log").exists()


def test_it_records_both_readable_and_hex_forms(tmp_path):
    log = AuditLog(tmp_path, "testdev")
    when = datetime.datetime(2026, 9, 2, 8, 0, 0)
    log.sent(b"$P01@b\r", when=when)

    text = (tmp_path / "testdev_2026-09-02.log").read_text(encoding="utf-8")
    assert "TX" in text
    # The carriage return must not end the line early.
    assert "\\r" in text
    assert len(text.strip().splitlines()) == 1
    # Hex is what you trust when the readable form is confusing.
    assert "24 50 30 31 40 62 0D" in text


def test_silence_is_recorded_as_an_event_not_as_nothing(tmp_path):
    # A quiet device is a finding. The log must show that we asked and got
    # nothing, otherwise it looks like we never asked.
    log = AuditLog(tmp_path, "testdev")
    when = datetime.datetime(2026, 9, 2, 8, 0, 0)
    log.received(b"", when=when)

    text = (tmp_path / "testdev_2026-09-02.log").read_text(encoding="utf-8")
    assert "silence" in text


def test_notes_land_in_the_same_file_as_the_traffic(tmp_path):
    log = AuditLog(tmp_path, "testdev")
    when = datetime.datetime(2026, 9, 2, 8, 0, 0)
    log.sent(b"x", when=when)
    log.note("retrying", when=when)

    text = (tmp_path / "testdev_2026-09-02.log").read_text(encoding="utf-8")
    assert "NOTE  retrying" in text
    assert len(text.strip().splitlines()) == 2
