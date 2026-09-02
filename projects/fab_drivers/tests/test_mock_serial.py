"""The mock stands in for a real port, so its behaviour has to be believable."""

from fab_drivers.core.mock_serial import MockSerial


def test_it_replies_using_the_responder():
    port = MockSerial(lambda written: b"A65\r")
    port.write(b"$P01J\r")
    assert port.read_until(b"\r") == b"A65\r"


def test_it_records_exactly_what_was_written():
    port = MockSerial(lambda written: b"ok\r")
    port.write(b"first\r")
    port.write(b"second\r")
    assert port.written == [b"first\r", b"second\r"]


def test_an_empty_reply_reads_back_as_silence():
    # This is how the retry path gets tested without waiting on a real timeout.
    port = MockSerial(lambda written: b"")
    port.write(b"$P01J\r")
    assert port.read_until(b"\r") == b""


def test_a_list_responder_plays_replies_in_order():
    port = MockSerial([b"", b"A65\r"])
    port.write(b"q\r")
    assert port.read_until(b"\r") == b""
    port.write(b"q\r")
    assert port.read_until(b"\r") == b"A65\r"


def test_reading_stops_at_the_terminator_and_keeps_the_rest():
    port = MockSerial(lambda written: b"one\rtwo\r")
    port.write(b"q\r")
    assert port.read_until(b"\r") == b"one\r"
    assert port.read_until(b"\r") == b"two\r"


def test_resetting_the_input_buffer_throws_away_a_stale_reply():
    port = MockSerial(lambda written: b"old\r")
    port.write(b"q\r")
    port.reset_input_buffer()
    assert port.read_until(b"\r") == b""


def test_reading_a_fixed_number_of_bytes():
    # The binary protocols read by length rather than up to a terminator, so
    # the mock has to offer read the way pyserial does.
    port = MockSerial(lambda written: bytes([0xCA, 0x00, 0x01, 0x20, 0x00]))
    port.write(b"q")
    assert port.read(3) == bytes([0xCA, 0x00, 0x01])
    assert port.read(2) == bytes([0x20, 0x00])


def test_reading_more_than_is_there_returns_what_is_there():
    # This is how a real port behaves when it times out partway through a
    # reply, and it is how the transport tells a short frame from silence.
    port = MockSerial(lambda written: b"ab")
    port.write(b"q")
    assert port.read(10) == b"ab"
    assert port.read(10) == b""
