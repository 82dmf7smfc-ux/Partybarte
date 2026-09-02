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


# ---------------------------------------------------------------------------
# Reading a reply that has no terminator
#
# A binary protocol cannot use a terminator, because any byte value can appear
# in the payload and so no byte is left over to mean "the end". The Thermo
# chiller driver is the first one like that, and the AE Bus and Modbus drivers
# will be too. Those protocols carry a length instead, and a driver passes a
# reply_size function that reads it.
# ---------------------------------------------------------------------------

def length_at_index_four(buffer):
    """A stand-in framing rule, shaped like the Thermo chiller's.

    Five bytes of header, the fifth of which is the number of data bytes to
    follow, then those bytes, then one checksum byte.
    """
    if len(buffer) < 5:
        return None
    return 6 + buffer[4]


def test_a_sized_reply_is_read_to_exactly_its_own_length():
    frame = bytes([0xCA, 0x00, 0x01, 0x20, 0x03, 0x11, 0x02, 0x71, 0x57])
    port = MockSerial(lambda written: frame)
    transport = SerialTransport(port, reply_size=length_at_index_four)
    assert transport.exchange(b"anything") == frame


def test_a_sized_reply_does_not_eat_into_the_next_one():
    # This is the failure that matters. Read one byte too many and the next
    # exchange starts on somebody else's last byte, and every reply after that
    # is off by one while still looking like data.
    first = bytes([0xCA, 0x00, 0x01, 0x20, 0x00, 0xDE])
    second = bytes([0xCA, 0x00, 0x01, 0x70, 0x00, 0x8E])
    port = MockSerial(lambda written: first + second)
    transport = SerialTransport(port, reply_size=length_at_index_four)
    assert transport.exchange(b"anything") == first


def test_a_sized_reply_that_stops_short_comes_back_short():
    # A device that stops halfway is not the same as one that never spoke, and
    # the driver has to be able to tell them apart. So the transport hands back
    # what arrived and lets the driver's checksum fail on it.
    port = MockSerial(lambda written: bytes([0xCA, 0x00, 0x01]))
    transport = SerialTransport(port, reply_size=length_at_index_four)
    assert transport.exchange(b"anything") == bytes([0xCA, 0x00, 0x01])


def test_silence_on_a_sized_reply_is_still_silence():
    port = MockSerial(lambda written: b"")
    transport = SerialTransport(port, reply_size=length_at_index_four)
    assert transport.exchange(b"anything") == b""


def test_a_device_that_never_stops_talking_does_not_hang_the_loop():
    # reply_size never resolves here, because the fifth byte says there are
    # more data bytes than will ever arrive in one frame. Without the cap this
    # would read forever.
    def never_enough(buffer):
        return None

    port = MockSerial(lambda written: b"x" * 4096)
    transport = SerialTransport(port, reply_size=never_enough,
                                max_reply_bytes=64)
    assert len(transport.exchange(b"anything")) == 64


def test_a_terminator_transport_is_unchanged_by_all_this():
    # Nine other drivers use the terminator path. It has to behave exactly as
    # it did before reply_size existed.
    port = MockSerial(lambda written: b"*01 9.34E-06\r")
    transport = SerialTransport(port, terminator=b"\r")
    assert transport.exchange(b"#01RD\r") == b"*01 9.34E-06\r"
