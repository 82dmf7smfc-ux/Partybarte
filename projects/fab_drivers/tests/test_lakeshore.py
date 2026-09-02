"""The Lakeshore driver, tested against the mock. No hardware needed.

Three things matter most here, and they are the first three sections.

The frame on the wire is exactly what PROTOCOL.md says it is. A sensor that is
not connected is caught rather than trended as a zero. A command that changes
the machine is refused before it becomes bytes.
"""

import pytest

from fab_drivers.core.audit import AuditLog
from fab_drivers.core.device import DeviceError, NoReply
from fab_drivers.core.history import HistoryWriter
from fab_drivers.core.mock_serial import MockSerial
from fab_drivers.core.poller import Poller
from fab_drivers.core.policy import CommandRefused
from fab_drivers.core.transport import SerialTransport
from fab_drivers.devices.lakeshore import (
    LakeshoreMonitor,
    LakeshoreResponder,
    MODELS,
    describe_status,
    history_columns,
    serial_settings,
    write_lakeshore_trend_page,
)
from fab_drivers.devices.lakeshore.mock import (
    STATUS_NOT_CONNECTED,
    STATUS_OVER_RANGE,
    format_reading,
)


def make_monitor(model="336", tmp_path=None, **responder_kwargs):
    """Wire a driver up to a fake instrument. Returns the pair."""
    fake = LakeshoreResponder(model, **responder_kwargs)
    port = MockSerial(fake)
    audit = AuditLog(tmp_path, "lakeshore") if tmp_path else None
    transport = SerialTransport(port, audit=audit, terminator=b"\r\n")
    monitor = LakeshoreMonitor(transport, model, retry_pause_s=0, pace_s=0)
    return monitor, port, fake


# ---- the frame on the wire ----

def test_a_reading_query_is_framed_the_way_the_protocol_says():
    monitor, port, _ = make_monitor("336", readings={"A": 77.35})
    monitor.read_kelvin("A")
    # Command, one space, the input name, then a carriage return and a line
    # feed. No checksum, no address prefix, no start character.
    assert port.written == [b"KRDG? A\r\n"]


def test_an_identity_query_carries_no_input():
    monitor, port, _ = make_monitor("218")
    assert monitor.identify() == "LSCI,MODEL218,LSA00000,1.7"
    assert port.written == [b"*IDN?\r\n"]


def test_a_good_reply_is_parsed_into_a_number():
    monitor, _, _ = make_monitor("336", readings={"B": 4.2})
    assert monitor.read_kelvin("B") == pytest.approx(4.2)


def test_the_reply_format_is_the_signed_fixed_width_one():
    # +077.350, sign always present. This is the format the driver has to cope
    # with, so it is worth pinning down in a test of its own.
    assert format_reading(77.35) == "+077.350"
    assert format_reading(4.2) == "+004.200"
    assert format_reading(-12.5) == "-012.500"


def test_celsius_and_sensor_units_have_their_own_commands():
    monitor, port, _ = make_monitor("336", readings={"A": 300.0})
    assert monitor.read_celsius("A") == pytest.approx(26.85)
    assert monitor.read_sensor_units("A") == pytest.approx(3.0)
    assert port.written == [b"CRDG? A\r\n", b"SRDG? A\r\n"]


def test_an_input_name_comes_back_as_text():
    monitor, _, _ = make_monitor("336", readings={"A": 4.2},
                                 names={"A": "Cold head"})
    assert monitor.read_input_name("A") == "Cold head"


# ---- a sensor that cannot be read ----

def test_an_unconnected_sensor_answers_with_a_number_that_must_not_be_trusted():
    # The point of the whole status check. Input B has no sensor, so the
    # instrument still answers KRDG? with a number.
    monitor, _, _ = make_monitor("336", readings={"A": 4.2})
    assert monitor.read_kelvin("B") == 0.0
    # And RDGST? is the only thing that says so.
    assert monitor.read_status("B") == STATUS_NOT_CONNECTED


def test_a_checked_reading_returns_none_for_an_unconnected_sensor():
    monitor, _, _ = make_monitor("336", readings={"A": 4.2})
    value, why = monitor.read_checked_kelvin("B")
    assert value is None
    assert why == "sensor units over range"


def test_a_checked_reading_returns_the_number_for_a_good_sensor():
    monitor, _, _ = make_monitor("336", readings={"A": 4.2})
    value, why = monitor.read_checked_kelvin("A")
    assert value == pytest.approx(4.2)
    assert why == ""


def test_an_out_of_range_sensor_is_caught_too():
    monitor, _, _ = make_monitor("336", readings={"A": 4.2},
                                 statuses={"A": STATUS_OVER_RANGE})
    value, why = monitor.read_checked_kelvin("A")
    assert value is None
    assert why == "temperature over range"


def test_several_status_bits_are_all_named():
    assert describe_status(0) == ""
    assert describe_status(1) == "invalid reading"
    assert describe_status(16 + 128) == ("temperature under range, "
                                         "sensor units over range")
    # A bit with no name still says something, rather than reading as good.
    assert describe_status(2) == "reading status 2"


def test_reading_every_input_leaves_a_hole_where_a_sensor_is_bad():
    monitor, _, _ = make_monitor("336", readings={"A": 4.2, "C": 300.0})
    assert monitor.read_all_kelvin() == {
        "A": pytest.approx(4.2),
        "B": None,
        "C": pytest.approx(300.0),
        "D": None,
    }


# ---- commands that must be refused ----

def test_a_reset_is_refused_before_it_becomes_bytes():
    monitor, port, _ = make_monitor("336")
    with pytest.raises(CommandRefused) as refusal:
        monitor.query("*RST")
    # The refusal says why, not just that it failed.
    assert "sensor setup" in str(refusal.value)
    # And nothing at all went to the port.
    assert port.written == []


def test_a_setpoint_write_is_refused():
    monitor, port, _ = make_monitor("336")
    with pytest.raises(CommandRefused) as refusal:
        monitor.query("SETP")
    assert "heater" in str(refusal.value)
    assert port.written == []


def test_clearing_the_status_registers_is_refused_even_though_it_looks_harmless():
    monitor, port, _ = make_monitor("336")
    with pytest.raises(CommandRefused):
        monitor.query("*CLS")
    assert port.written == []


def test_a_command_nobody_listed_is_refused_as_well():
    monitor, port, _ = make_monitor("336")
    with pytest.raises(CommandRefused):
        monitor.query("PID?")
    assert port.written == []


def test_an_input_that_does_not_exist_on_this_model_is_refused():
    # E is not an input on a 336, and 1 is not one either. On a 218 they are
    # numbered instead of lettered.
    monitor, port, _ = make_monitor("336", readings={"A": 4.2})
    with pytest.raises(CommandRefused):
        monitor.read_kelvin("E")
    with pytest.raises(CommandRefused):
        monitor.read_kelvin("1")
    assert port.written == []


def test_an_identity_query_may_not_be_aimed_at_an_input():
    monitor, _, _ = make_monitor("336")
    with pytest.raises(CommandRefused):
        monitor.query("*IDN?", target="A")


# ---- the models differ ----

def test_the_218_numbers_its_inputs_and_the_336_letters_them():
    assert MODELS["218"].inputs == ["1", "2", "3", "4", "5", "6", "7", "8"]
    assert MODELS["336"].inputs == ["A", "B", "C", "D"]
    assert MODELS["224"].inputs == ["A", "B", "C1", "C2", "C3", "C4", "C5",
                                    "D1", "D2", "D3", "D4", "D5"]


def test_the_218_reads_every_input_with_one_query():
    monitor, port, _ = make_monitor(
        "218", readings={str(n): 10.0 * n for n in range(1, 9)})
    readings = monitor.read_all_kelvin()
    assert readings["1"] == pytest.approx(10.0)
    assert readings["8"] == pytest.approx(80.0)
    # One batch query, then one status query per input.
    assert port.written[0] == b"KRDG? 0\r\n"
    assert port.written.count(b"KRDG? 0\r\n") == 1


def test_the_336_asks_each_input_in_turn():
    monitor, port, _ = make_monitor("336", readings={"A": 4.2})
    monitor.read_all_kelvin()
    assert b"KRDG? 0\r\n" not in port.written
    assert b"RDGST? A\r\n" in port.written


def test_the_port_settings_are_seven_bits_odd_parity_on_every_model():
    for model in MODELS:
        settings = serial_settings(model)
        assert settings["bytesize"] == 7
        assert settings["parity"] == "O"
        assert settings["stopbits"] == 1
    assert serial_settings("218")["baud"] == 9600
    assert serial_settings("224")["baud"] == 57600
    assert serial_settings("336")["baud"] == 57600


def test_an_unknown_model_is_refused_when_the_driver_is_built():
    with pytest.raises(ValueError) as problem:
        make_monitor("335")
    assert "218" in str(problem.value)


# ---- silence and broken replies ----

def test_silence_is_retried_and_then_gives_up():
    monitor, port, _ = make_monitor("336", readings={"A": 4.2},
                                    silent=["A"])
    with pytest.raises(NoReply):
        monitor.read_kelvin("A")
    # Three attempts in total, which is the library standard.
    assert port.written == [b"KRDG? A\r\n"] * 3


def test_a_reply_with_no_terminator_is_not_retried():
    monitor, port, _ = make_monitor("336", readings={"A": 4.2},
                                    garbled=["A"])
    with pytest.raises(DeviceError) as problem:
        monitor.read_kelvin("A")
    # Sent once. A broken reply means the settings are wrong, and sending the
    # same command twice more only writes the same failure to the log again.
    assert port.written == [b"KRDG? A\r\n"]
    # The message points at the likely cause.
    assert "odd parity" in str(problem.value)


def test_a_reply_that_is_not_a_number_is_a_device_error():
    monitor, _, _ = make_monitor("336", readings={"A": 4.2},
                                 names={"A": "Cold head"})
    # INNAME? legitimately returns text. Asking for it as a temperature is a
    # driver mistake, and it should say so rather than crash oddly.
    with pytest.raises(DeviceError):
        monitor._read_number("INNAME?", "A")


def test_every_frame_reaches_the_audit_log(tmp_path):
    monitor, _, _ = make_monitor("336", tmp_path=tmp_path,
                                 readings={"A": 4.2})
    monitor.read_kelvin("A")
    log = list(tmp_path.glob("lakeshore_*.log"))[0].read_text(encoding="utf-8")
    assert "KRDG? A" in log
    assert "TX" in log and "RX" in log


# ---- the driver plugs into the poller and the trend page ----

def test_the_driver_gives_the_poller_one_source_per_input(tmp_path):
    monitor, _, _ = make_monitor("336", readings={"A": 4.2, "B": 77.35})
    columns = MODELS["336"].inputs
    history = HistoryWriter(tmp_path, "lakeshore", columns)
    poller = Poller(monitor.kelvin_sources(), interval_s=30, history=history)

    readings = poller.sweep()
    assert readings["A"].value == pytest.approx(4.2)
    assert readings["A"].stale is False
    # C has no sensor, so it is stale and the CSV cell is empty.
    assert readings["C"].stale is True

    written = list(tmp_path.glob("lakeshore_*.csv"))[0].read_text(
        encoding="utf-8")
    header, row = written.strip().splitlines()
    assert header == "timestamp,A,B,C,D"
    assert row.endswith(",,")


def test_a_column_can_carry_the_name_from_the_front_panel():
    assert history_columns("336") == ["A", "B", "C", "D"]
    assert history_columns("336", {"A": "Cold head", "B": ""}) == [
        "A Cold head", "B", "C", "D"]


def test_the_trend_page_is_built_from_the_shared_generator(tmp_path):
    columns = MODELS["336"].inputs
    history = HistoryWriter(tmp_path, "lakeshore", columns)
    history.append({"A": 4.21, "B": 77.35, "C": None, "D": 295.1})
    history.append({"A": 4.19, "B": 77.40, "C": None, "D": 295.2})

    out = tmp_path / "page.html"
    write_lakeshore_trend_page(tmp_path, "lakeshore", out, "336")
    page = out.read_text(encoding="utf-8")

    assert "Lakeshore 336 temperatures, kelvin" in page
    assert "<svg" in page
    # The page carries its own data and fetches nothing. These machines have no
    # internet, and a page opened from disk cannot read a file next to it.
    assert "http://" not in page
    assert "https://" not in page
