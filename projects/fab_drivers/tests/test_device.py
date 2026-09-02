"""The device base class holds the retry rule and the safety gate together.

These tests use a tiny fake driver that frames a command the way the CTI
On-Board terminal does. That protocol is the one we have verified worked examples
for, so it is a fair stand-in for a real driver without being one.
"""

import pytest

from fab_drivers.core.audit import AuditLog
from fab_drivers.core.device import Device, DeviceError, NoReply
from fab_drivers.core.mock_serial import MockSerial
from fab_drivers.core.policy import CommandPolicy, CommandRefused
from fab_drivers.core.transport import SerialTransport


def checksum(body):
    """The CTI checksum, verified against the worked examples in both manuals."""
    total = sum(ord(c) & 0x7F for c in body) & 0xFF
    folded = (total ^ (total >> 6)) & 0x3F
    return chr(0x30 + folded)


class ExampleDriver(Device):
    """A stand-in driver, framing like the CTI terminal does.

    A command aimed at a pump is addressed P + two digits + the command. A
    command aimed at the terminal itself has no address and is sent as is.
    """

    def build_frame(self, command, target=None):
        body = command if target is None else "P%02d%s" % (target, command)
        return ("$" + body + checksum(body) + "\r").encode("ascii")

    def parse_reply(self, raw):
        text = raw.decode("ascii", errors="replace").rstrip("\r")
        if not text.startswith("$"):
            raise DeviceError("reply did not start with $: %r" % text)
        body, sent_checksum = text[1:-1], text[-1]
        if checksum(body) != sent_checksum:
            raise DeviceError("checksum mismatch on %r" % text)
        return body[1:]


def make_device(responder, tmp_path=None, retries=2):
    port = MockSerial(responder)
    audit = AuditLog(tmp_path, "testdev") if tmp_path else None
    transport = SerialTransport(port, audit=audit, terminator=b"\r")
    policy = CommandPolicy(
        "example",
        allowed=["J", "K"],
        banned={"g": "Locks other ports out, including the tool's own."},
        targets=range(0, 20),
    )
    device = ExampleDriver(transport, policy, name="example", retries=retries,
                           retry_pause_s=0)
    return device, port


def framed(body):
    return ("$" + body + checksum(body) + "\r").encode("ascii")


def test_a_good_reply_is_parsed():
    device, _ = make_device(lambda written: framed("A65.2"))
    assert device.query("J", target=1) == "65.2"


def test_the_frame_on_the_wire_is_the_one_the_manual_describes():
    device, port = make_device(lambda written: framed("A65.2"))
    device.query("J", target=1)
    # The manual's worked example: body P01J, checksum character, carriage
    # return. The address is composed by the driver, not carried in the command.
    assert port.written == [b"$P01J" + checksum("P01J").encode() + b"\r"]


def test_the_same_command_reaches_a_different_pump():
    device, port = make_device(lambda written: framed("A70.1"))
    device.query("J", target=12)
    assert port.written == [b"$P12J" + checksum("P12J").encode() + b"\r"]


def test_an_unknown_pump_address_never_reaches_the_port():
    device, port = make_device(lambda written: framed("A65.2"))
    with pytest.raises(CommandRefused):
        device.query("J", target=44)
    assert port.written == []


def test_a_banned_command_never_reaches_the_port():
    # The gate runs before the frame is built, so nothing is written at all.
    device, port = make_device(lambda written: framed("A1"))
    with pytest.raises(CommandRefused):
        device.query("g")
    assert port.written == []


def test_a_command_that_is_merely_unlisted_also_never_reaches_the_port():
    device, port = make_device(lambda written: framed("A1"))
    with pytest.raises(CommandRefused):
        device.query("A1", target=1)    # pump on, a control command
    assert port.written == []


def test_silence_is_retried_the_standard_number_of_times():
    # The library standard is one try plus two retries, so three frames.
    device, port = make_device(lambda written: b"")
    with pytest.raises(NoReply):
        device.query("J", target=1)
    assert len(port.written) == 3


def test_a_device_that_answers_on_the_last_attempt_still_works():
    replies = [b"", b"", framed("A65.2")]
    device, port = make_device(lambda written: replies.pop(0))
    assert device.query("J", target=1) == "65.2"
    assert len(port.written) == 3


def test_a_broken_reply_is_not_retried():
    # Silence may be a busy device. A bad checksum means the link or the port
    # settings are wrong, and asking twice more only repeats the same failure.
    device, port = make_device(lambda written: b"$A65.2X\r")
    with pytest.raises(DeviceError):
        device.query("J", target=1)
    assert len(port.written) == 1


def test_try_query_turns_a_failure_into_none():
    device, _ = make_device(lambda written: b"")
    assert device.try_query("J", target=1) is None


def test_try_query_still_refuses_a_banned_command():
    # try_query softens failures, not the safety gate. A refused command is a
    # programming mistake, and swallowing it would hide the mistake.
    device, port = make_device(lambda written: b"")
    with pytest.raises(CommandRefused):
        device.try_query("g")
    assert port.written == []


def test_the_retries_and_the_giving_up_are_both_in_the_audit_log(tmp_path):
    device, _ = make_device(lambda written: b"", tmp_path=tmp_path)
    with pytest.raises(NoReply):
        device.query("J", target=1)

    text = list(tmp_path.glob("*.log"))[0].read_text(encoding="utf-8")
    assert "trying again" in text
    assert "marking stale" in text
    # The log has to say which pump went quiet, not just that something did.
    assert "on 1" in text


def test_a_driver_needs_a_policy():
    port = MockSerial(lambda written: b"")
    transport = SerialTransport(port, terminator=b"\r")
    with pytest.raises(TypeError):
        ExampleDriver(transport, policy=None)
