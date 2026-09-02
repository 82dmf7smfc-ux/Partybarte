"""The Granville-Phillips driver, tested against the mock. No hardware needed.

Four things matter most here, and they are the first four sections.

The frame on the wire is exactly what PROTOCOL.md says it is. A gauge that is
off is caught rather than trended as 9.99e9. A reply from the wrong address is
refused rather than believed. A command that changes the machine is refused
before it becomes bytes.
"""

import pytest

from fab_drivers.core.audit import AuditLog
from fab_drivers.core.device import DeviceError, NoReply
from fab_drivers.core.history import HistoryWriter
from fab_drivers.core.mock_serial import MockSerial
from fab_drivers.core.poller import Poller
from fab_drivers.core.policy import CommandRefused
from fab_drivers.core.transport import SerialTransport
from fab_drivers.devices.granville_phillips import (
    GranvillePhillipsGauge,
    GranvillePhillipsResponder,
    MODELS,
    format_address,
    format_pressure,
    history_columns,
    pressure_scales,
    serial_settings,
    write_granville_phillips_trend_page,
)
from fab_drivers.devices.granville_phillips.mock import (
    READING_WHEN_OFF,
    SYNTAX_ERROR,
)


def make_gauge(model="275", address=1, units="torr", tmp_path=None,
               **responder_kwargs):
    """Wire a driver up to a fake instrument. Returns the three parts."""
    fake = GranvillePhillipsResponder(model, address=address,
                                      **responder_kwargs)
    port = MockSerial(fake)
    audit = AuditLog(tmp_path, "granville_phillips") if tmp_path else None
    transport = SerialTransport(port, audit=audit, terminator=b"\r")
    gauge = GranvillePhillipsGauge(transport, model, address=address,
                                   units=units, retry_pause_s=0, pace_s=0)
    return gauge, port, fake


# ---- the frame on the wire ----

def test_a_read_is_framed_the_way_the_protocol_says():
    gauge, port, _ = make_gauge("275", pressures={"CG": 2.4e-3})
    gauge.read_pressure()
    # Start character, two hexadecimal address characters, the command, then a
    # bare carriage return. No checksum, no line feed.
    assert port.written == [b"#01RD\r"]


def test_the_worked_example_from_the_manual_round_trips():
    # #01RD -> *01 9.34E-06 is the one worked exchange any source gave, so it
    # is worth pinning down on its own.
    gauge, port, _ = make_gauge("356", pressures={"IG": 9.34e-6})
    value, why = gauge.read_pressure()
    assert port.written == [b"#01RD\r"]
    assert value == pytest.approx(9.34e-6)
    assert why == ""


def test_the_address_is_two_hexadecimal_characters():
    # Address 10 is 0A on the wire, not 10. Sending "10" would address module
    # sixteen, which on a shared pair is somebody else's gauge.
    assert format_address(1) == "01"
    assert format_address(10) == "0A"
    assert format_address(31) == "1F"

    gauge, port, _ = make_gauge("350", address=10, pressures={"CGA": 1.0e-3})
    gauge.read_pressure("CGA")
    assert port.written == [b"#0ARD A\r"]


def test_a_gauge_selector_rides_in_the_command_not_the_address():
    # The 350 has four gauges behind one address. The gauge is chosen by the
    # command modifier. The address still says which controller.
    gauge, port, _ = make_gauge("350", pressures={"IG1": 2.0e-8, "CGB": 5.0})
    gauge.read_pressure("IG1")
    gauge.read_pressure("CGB")
    assert port.written == [b"#01RD 1\r", b"#01RD B\r"]


def test_the_reply_format_is_the_scientific_one():
    assert format_pressure(9.34e-6) == "9.34E-06"
    assert format_pressure(760.0) == "7.60E+02"


def test_the_degas_and_setpoint_reads_exist_on_the_350_only():
    gauge, port, _ = make_gauge("350", degas="1", setpoints="0110")
    assert gauge.read_degas_status() == "1"
    assert gauge.read_setpoint_status() == "0110"
    assert port.written == [b"#01DGS\r", b"#01PC S\r"]

    # A 275 has no degas, so the command is not on its allowed list at all.
    module, module_port, _ = make_gauge("275", pressures={"CG": 1.0})
    with pytest.raises(CommandRefused):
        module.read_degas_status()
    assert module_port.written == []


# ---- a gauge that cannot be read ----

def test_a_gauge_that_is_off_answers_with_a_number_that_must_not_be_trusted():
    # The point of the whole check. The module is not silent. It answers.
    gauge, _, fake = make_gauge("275")
    assert fake.pressure_of("CG") == READING_WHEN_OFF

    value, why = gauge.read_pressure()
    assert value is None
    assert "no reading yet" in why


def test_a_starting_up_gauge_is_a_hole_and_not_a_huge_pressure():
    # 9.99E+09 for the first few seconds after power up. If this were trended
    # as a number it would flatten every real reading on the chart.
    gauge, _, _ = make_gauge("356", pressures={"IG": 9.99e9})
    value, _ = gauge.read_pressure()
    assert value is None


def test_a_zero_reading_is_a_hole_too():
    # Not documented anywhere, and not something a log axis can place either.
    gauge, _, _ = make_gauge("275", pressures={"CG": 0.0})
    value, why = gauge.read_pressure()
    assert value is None
    assert "zero or negative" in why


def test_reading_every_gauge_leaves_a_hole_where_one_is_off():
    gauge, _, _ = make_gauge("350", pressures={"IG1": 3.0e-8, "CGA": 1.2e-2})
    assert gauge.read_all_pressures() == {
        "IG1": pytest.approx(3.0e-8),
        "IG2": None,
        "CGA": pytest.approx(1.2e-2),
        "CGB": None,
    }


# ---- a reply from the wrong module ----

def test_a_reply_from_another_address_is_refused_not_believed():
    # This is the RS-485 failure. Every module on the pair hears every frame, so
    # a second module answering puts a plausible pressure in front of you and
    # nothing about the number says it came from the wrong gauge.
    gauge, _, _ = make_gauge("275", pressures={"CG": 1.0e-3},
                             wrong_address=["CG"])
    with pytest.raises(DeviceError) as problem:
        gauge.read_pressure()
    assert "came from address" in str(problem.value)


def test_a_module_ignores_a_frame_sent_to_another_address():
    # The other half of the same behaviour. The mock module is at address 1, and
    # the driver is pointed at address 2, so nothing answers at all.
    fake = GranvillePhillipsResponder("275", address=1,
                                      pressures={"CG": 1.0e-3})
    port = MockSerial(fake)
    transport = SerialTransport(port, terminator=b"\r")
    gauge = GranvillePhillipsGauge(transport, "275", address=2, units="torr",
                                   retry_pause_s=0)
    with pytest.raises(NoReply):
        gauge.read_pressure()


def test_an_address_the_model_does_not_have_is_refused_when_built():
    # A 275's switch runs 0 to 15. Address 40 is not a thing it can be.
    fake = GranvillePhillipsResponder("275", address=1)
    transport = SerialTransport(MockSerial(fake), terminator=b"\r")
    with pytest.raises(CommandRefused):
        GranvillePhillipsGauge(transport, "275", address=40, units="torr")


# ---- commands that must be refused ----

def test_turning_a_filament_on_is_refused_before_it_becomes_bytes():
    gauge, port, _ = make_gauge("350")
    with pytest.raises(CommandRefused) as refusal:
        gauge.query("F1 1", target=1)
    # The refusal says why, not just that it failed.
    assert "burns out" in str(refusal.value)
    # And nothing at all went to the port.
    assert port.written == []


def test_starting_degas_is_refused():
    gauge, port, _ = make_gauge("350")
    with pytest.raises(CommandRefused) as refusal:
        gauge.query("DG1 ON", target=1)
    assert "bakes the gauge grid" in str(refusal.value)
    assert port.written == []


def test_changing_the_units_is_refused():
    # The one that would quietly ruin a trend file rather than break anything.
    gauge, port, _ = make_gauge("275")
    with pytest.raises(CommandRefused) as refusal:
        gauge.query("SUT", target=1)
    assert "what every reading means" in str(refusal.value)
    # All three unit commands, one per unit, and none of them may be sent.
    for command in ("SUM", "SUP"):
        with pytest.raises(CommandRefused):
            gauge.query(command, target=1)
    assert port.written == []


def test_setting_the_address_offset_is_refused():
    gauge, port, _ = make_gauge("275")
    with pytest.raises(CommandRefused) as refusal:
        gauge.query("SA", target=1)
    assert "renumbers a gauge" in str(refusal.value)
    assert port.written == []


def test_calibration_commands_are_refused():
    gauge, port, _ = make_gauge("275")
    for command in ("SZ", "SS", "SW"):
        with pytest.raises(CommandRefused):
            gauge.query(command, target=1)
    assert port.written == []


def test_a_command_nobody_listed_is_refused_as_well():
    gauge, port, _ = make_gauge("275")
    with pytest.raises(CommandRefused):
        gauge.query("RS", target=1)
    assert port.written == []


def test_a_gauge_selector_from_another_model_is_refused():
    # RD A is a 350 command. A 275 has one gauge and no selector.
    gauge, port, _ = make_gauge("275")
    with pytest.raises(CommandRefused):
        gauge.query("RD A", target=1)
    assert port.written == []


# ---- the models differ ----

def test_each_model_knows_its_own_gauges():
    assert [c.key for c in MODELS["275"].channels] == ["CG"]
    assert [c.key for c in MODELS["356"].channels] == ["IG"]
    assert [c.key for c in MODELS["350"].channels] == ["IG1", "IG2", "CGA",
                                                       "CGB"]


def test_the_375_says_out_loud_that_it_is_not_fully_sourced():
    # No source found says how to select a channel on a 375. A warning that only
    # lives in a markdown file is one nobody reads at the bench.
    gauge, _, _ = make_gauge("375", pressures={"CG": 1.0})
    assert "not fully sourced" in gauge.describe_sources()
    assert "multi-channel controller" in gauge.describe_sources()

    module, _, _ = make_gauge("275", pressures={"CG": 1.0})
    assert "not fully sourced" not in module.describe_sources()


def test_a_model_with_several_gauges_insists_on_being_told_which():
    gauge, _, _ = make_gauge("350", pressures={"IG1": 1.0e-8})
    with pytest.raises(ValueError) as problem:
        gauge.read_pressure()
    assert "IG1" in str(problem.value)


def test_the_port_settings_are_eight_bits_no_parity_on_every_model():
    for model in MODELS:
        settings = serial_settings(model)
        assert settings["bytesize"] == 8
        assert settings["parity"] == "N"
        assert settings["stopbits"] == 1
        assert settings["baud"] == 9600


def test_an_unknown_model_is_refused_when_the_driver_is_built():
    fake = GranvillePhillipsResponder("275")
    transport = SerialTransport(MockSerial(fake), terminator=b"\r")
    with pytest.raises(ValueError) as problem:
        GranvillePhillipsGauge(transport, "475", units="torr")
    assert "275" in str(problem.value)


def test_the_units_must_be_stated_because_the_instrument_will_not_say():
    # There is no read-units query on these instruments. A default would produce
    # a trend file whose units changed halfway through, with plausible numbers
    # either side of the change.
    fake = GranvillePhillipsResponder("275")
    transport = SerialTransport(MockSerial(fake), terminator=b"\r")
    with pytest.raises(ValueError) as problem:
        GranvillePhillipsGauge(transport, "275")
    assert "do not report their own units" in str(problem.value)

    with pytest.raises(ValueError):
        GranvillePhillipsGauge(transport, "275", units="psi")


# ---- silence and broken replies ----

def test_silence_is_retried_and_then_gives_up():
    gauge, port, _ = make_gauge("275", pressures={"CG": 1.0e-3},
                                silent=["CG"])
    with pytest.raises(NoReply):
        gauge.read_pressure()
    # Three attempts in total, which is the library standard.
    assert port.written == [b"#01RD\r"] * 3


def test_a_reply_with_no_terminator_is_not_retried():
    gauge, port, _ = make_gauge("275", pressures={"CG": 1.0e-3},
                                garbled=["CG"])
    with pytest.raises(DeviceError) as problem:
        gauge.read_pressure()
    # Sent once. A broken reply means the settings are wrong, and sending the
    # same command twice more only writes the same failure to the log again.
    assert port.written == [b"#01RD\r"]
    assert "carriage return" in str(problem.value)


def test_a_syntax_error_reply_is_reported_as_an_error_not_a_reading():
    # The mock answers ?01 SYNTX_ER to anything it does not know. Getting there
    # means the policy leaked, so this test reaches past it on purpose.
    gauge, _, _ = make_gauge("350")
    gauge.policy.allowed.add("RD Z")
    with pytest.raises(DeviceError) as problem:
        gauge.query("RD Z", target=1)
    assert SYNTAX_ERROR in str(problem.value)


def test_a_reply_that_is_not_a_number_is_a_device_error():
    # A well formed reply whose payload is a word rather than a pressure. It
    # should say what it got, rather than crash somewhere odd.
    port = MockSerial([b"*01 OPEN\r"])
    transport = SerialTransport(port, terminator=b"\r")
    gauge = GranvillePhillipsGauge(transport, "275", units="torr",
                                   retry_pause_s=0)
    with pytest.raises(DeviceError) as problem:
        gauge.read_pressure()
    assert "expected a pressure" in str(problem.value)


def test_every_frame_reaches_the_audit_log(tmp_path):
    gauge, _, _ = make_gauge("275", tmp_path=tmp_path,
                             pressures={"CG": 4.4e-4})
    gauge.read_pressure()
    log = list(tmp_path.glob("granville_phillips_*.log"))[0].read_text(
        encoding="utf-8")
    assert "#01RD" in log
    assert "TX" in log and "RX" in log


# ---- the driver plugs into the poller and the trend page ----

def test_the_driver_gives_the_poller_one_source_per_gauge(tmp_path):
    gauge, _, _ = make_gauge("350", pressures={"IG1": 2.0e-8, "CGA": 8.0e-3})
    columns = [c.key for c in MODELS["350"].channels]
    history = HistoryWriter(tmp_path, "gp350", columns)
    poller = Poller(gauge.pressure_sources(), interval_s=30, history=history)

    readings = poller.sweep()
    assert readings["IG1"].value == pytest.approx(2.0e-8)
    assert readings["IG1"].stale is False
    # IG2 is switched off, so it is stale and the CSV cell is empty.
    assert readings["IG2"].stale is True

    written = list(tmp_path.glob("gp350_*.csv"))[0].read_text(encoding="utf-8")
    header, row = written.strip().splitlines()
    assert header == "timestamp,IG1,IG2,CGA,CGB"
    assert row.endswith(",")


def test_a_column_carries_the_unit_because_the_instrument_will_not():
    assert history_columns("275", "torr") == ["CG Convectron (torr)"]
    assert history_columns("350", "mbar") == [
        "IG1 Ion gauge 1 (mbar)",
        "IG2 Ion gauge 2 (mbar)",
        "CGA Convectron A (mbar)",
        "CGB Convectron B (mbar)",
    ]


def test_every_pressure_column_is_asked_for_a_log_axis():
    columns = history_columns("350", "torr")
    assert pressure_scales(columns) == {column: "log" for column in columns}


def test_the_trend_page_is_built_from_the_shared_generator(tmp_path):
    columns = history_columns("275", "torr")
    history = HistoryWriter(tmp_path, "gp275", columns)
    # A pumpdown across five decades, with one failed reading in the middle.
    for value in (7.5e2, 2.0e1, 4.0e-1, None, 6.0e-3, 9.0e-4):
        history.append({columns[0]: value})

    out = tmp_path / "page.html"
    write_granville_phillips_trend_page(tmp_path, "gp275", out, "275", "torr")
    page = out.read_text(encoding="utf-8")

    assert "Granville-Phillips 275 pressure, torr" in page
    assert "<svg" in page
    # A log axis, said out loud on the page, with one gridline per decade. The
    # readings run from 9e-4 to 750 torr, so the axis is snapped to 1e-4 up to
    # 1e+3, which is eight decades and so eight gridlines.
    assert "Log scale" in page
    assert page.count('class="grid"') == 8
    # The top of the axis is always labelled. Labels below it are thinned out
    # when there are many decades, so not every gridline carries one.
    assert "1E+03" in page
    assert "1E-03" in page
    # The gap still breaks the line, on a log axis as on a linear one.
    assert page.count("<polyline") == 2
    # The page carries its own data and fetches nothing. These machines have no
    # internet, and a page opened from disk cannot read a file next to it.
    assert "http://" not in page
    assert "https://" not in page
