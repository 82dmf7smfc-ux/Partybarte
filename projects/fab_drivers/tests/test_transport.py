"""The transport owns the port and logs the traffic. Both are tested here."""

import pytest

from fab_drivers.core.audit import AuditLog
from fab_drivers.core.mock_serial import MockSerial
from fab_drivers.core.transport import (
    PortBusy, SerialTransport, claim_port, release_port,
)


def test_an_exchange_returns_the_reply():
    port = MockSerial(lambda written: b"A65\r")
    transport = SerialTransport(port, terminator=b"\r")
    assert transport.exchange(b"$P01J\r") == b"A65\r"


def test_silence_comes_back_as_empty_bytes_and_does_not_raise():
    # Silence is a normal answer from a busy device. Deciding what to do about
    # it belongs one layer up, in the device retry logic.
    port = MockSerial(lambda written: b"")
    transport = SerialTransport(port, terminator=b"\r")
    assert transport.exchange(b"$P01J\r") == b""


def test_both_directions_reach_the_audit_log(tmp_path):
    port = MockSerial(lambda written: b"A65\r")
    audit = AuditLog(tmp_path, "testdev")
    transport = SerialTransport(port, audit=audit, terminator=b"\r")
    transport.exchange(b"$P01J\r")

    written = list(tmp_path.glob("*.log"))[0].read_text(encoding="utf-8")
    assert "TX" in written and "RX" in written
    assert "$P01J" in written
    assert "A65" in written


def test_a_leftover_reply_is_cleared_before_the_next_command():
    # If a previous exchange failed halfway, its reply may still be sitting in
    # the buffer. Reading it now would pair the wrong answer with this question,
    # which is worse than getting nothing back.
    replies = [b"stale answer\r", b"fresh answer\r"]
    port = MockSerial(lambda written: replies.pop(0))
    transport = SerialTransport(port, terminator=b"\r")

    transport.exchange(b"first\r")           # consumes the stale one
    assert transport.exchange(b"second\r") == b"fresh answer\r"


def test_a_frame_must_be_bytes():
    port = MockSerial(lambda written: b"ok\r")
    transport = SerialTransport(port, terminator=b"\r")
    with pytest.raises(TypeError):
        transport.exchange("$P01J\r")


def test_the_same_port_cannot_be_claimed_twice():
    # One process, one owner per port. Two owners produce interleaved frames
    # that look like a device fault.
    claim_port("COM_TEST")
    try:
        with pytest.raises(PortBusy):
            claim_port("COM_TEST")
    finally:
        release_port("COM_TEST")

    # After release it is available again.
    claim_port("COM_TEST")
    release_port("COM_TEST")


def test_closing_releases_the_port_name():
    claim_port("COM_CLOSE")
    port = MockSerial(lambda written: b"")
    transport = SerialTransport(port, name="COM_CLOSE")
    transport.close()

    assert port.is_open is False
    claim_port("COM_CLOSE")     # would raise PortBusy if close had not released
    release_port("COM_CLOSE")
