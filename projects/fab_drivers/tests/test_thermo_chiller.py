"""The Thermo chiller driver, tested against the mock. No hardware needed.

Five things matter most here, and they are the first five sections.

The checksum agrees with the manual byte for byte, on every worked example the
two manuals print. The frame on the wire is exactly what PROTOCOL.md says it is.
A reply whose checksum fails is refused rather than decoded into a plausible
temperature. A chiller in alarm is noticed. A command that changes the machine
is refused before it becomes bytes, and refused twice over.

The checksum section is the important one. This is the first protocol in the
library with a checksum in it, and a checksum written from a prose description
and never checked against a real frame will happily agree with a mock that has
the same mistake in it. So the manual's own printed frames are the test.
"""

import pytest

from fab_drivers.core.audit import AuditLog
from fab_drivers.core.device import DeviceError, NoReply
from fab_drivers.core.history import HistoryWriter
from fab_drivers.core.mock_serial import MockSerial
from fab_drivers.core.poller import Poller
from fab_drivers.core.policy import CommandRefused
from fab_drivers.core.transport import SerialTransport
from fab_drivers.devices.thermo_chiller import (
    COMMANDS,
    COMMANDS_BY_NAME,
    LEAD_RS232,
    LEAD_RS485,
    MODELS,
    ThermoChiller,
    ThermoChillerResponder,
    build_policy,
    build_transport,
    checksum,
    column_for,
    decode_measurement,
    decode_status,
    history_columns,
    reply_size,
    serial_settings,
    setpoint_overlay,
    split_qualifier,
    write_thermo_chiller_trend_page,
)
from fab_drivers.devices.thermo_chiller.driver import WRITE_BIT


def hexframe(text):
    """Turn a manual's printed frame, like "CA 00 01 20 00 DE", into bytes."""
    return bytes.fromhex(text.replace(" ", ""))


def make_chiller(model="THERMOFLEX", address=1, rs485=False, tmp_path=None,
                 **responder_kwargs):
    """Wire a driver up to a fake chiller. Returns the three parts."""
    fake = ThermoChillerResponder(model, address=address, rs485=rs485,
                                  **responder_kwargs)
    port = MockSerial(fake)
    audit = AuditLog(tmp_path, "thermo_chiller") if tmp_path else None
    transport = build_transport(port, audit=audit)
    chiller = ThermoChiller(transport, model, address=address, rs485=rs485,
                            retry_pause_s=0)
    return chiller, fake, port


# ---------------------------------------------------------------------------
# The checksum, against the manuals' own worked examples
# ---------------------------------------------------------------------------

# Every complete frame the two manuals print with its checksum. Each entry is
# the frame exactly as printed, and where it came from.
#
# These are not examples this project invented. They are the manufacturer's own
# bytes, and the point of the test below is that the code agrees with them
# without ever having been shown them.
MANUAL_EXAMPLES = [
    # --- RTE 110/112 manual, Appendix A, Table 1, the READ block ---
    ("CA 00 01 20 00 DE", "RTE 110 Table 1, Read Internal Temperature"),
    ("CA 00 01 21 00 DD", "RTE 110 Table 1, Read External Sensor"),
    ("CA 00 01 70 00 8E", "RTE 110 Table 1, Read Setpoint"),
    ("CA 00 01 40 00 BE", "RTE 110 Table 1, Read Low Temperature Limit"),
    ("CA 00 01 60 00 9E", "RTE 110 Table 1, Read High Temperature Limit"),
    ("CA 00 01 71 00 8D", "RTE 110 Table 1, Read Proportional Band"),
    ("CA 00 01 72 00 8C", "RTE 110 Table 1, Read Integral"),
    ("CA 00 01 73 00 8B", "RTE 110 Table 1, Read Derivative"),
    ("CA 00 01 00 00 FE", "RTE 110 Table 1, Request Acknowledge"),

    # --- RTE 110/112 manual, Appendix A, the worked exchanges in the text ---
    ("CA 00 01 20 03 11 FF 97 34",
     "RTE 110 body, reply of -10.5 C, the negative worked example"),
    ("CA 00 01 F0 02 01 2C DF",
     "RTE 110 body, Set Setpoint 30.0 C. A write, and this driver never sends "
     "it. It is here because it is a checksum the manual printed."),
    ("CA 00 01 F0 03 11 01 2C CD", "RTE 110 body, the reply to that write"),

    # --- RTE Digital Plus manual, Appendix B, Table 1 additions ---
    ("CA 00 01 09 00 F5", "Digital Plus Table 1, Read Status"),
    ("CA 00 01 75 00 89", "Digital Plus Table 1, Read Cool Integral"),
    ("CA 00 01 76 00 88", "Digital Plus Table 1, Read Cool Derivative"),

    # --- RTE Digital Plus manual, Appendix B, the worked exchanges ---
    ("CA 00 01 20 03 11 02 71 57", "Digital Plus body, reply of 62.5 C"),
    ("CC 00 03 F0 02 01 2C DD",
     "Digital Plus body, Set Setpoint on RS-485 at address 3. The RS-485 lead "
     "character and a non-default address in one frame."),
    ("CC 00 03 F0 03 11 01 2C CB",
     "Digital Plus body, the RS-485 reply to that write"),
]


@pytest.mark.parametrize("printed,where", MANUAL_EXAMPLES)
def test_checksum_agrees_with_every_worked_example_in_the_manuals(printed,
                                                                  where):
    """The checksum this code computes is the byte the manual printed.

    This is the test that stops the whole driver being confidently wrong. The
    mock computes its checksums with its own arithmetic and would agree with a
    broken driver. The manual will not.
    """
    frame = hexframe(printed)
    # Everything except the lead character and the checksum byte, which is what
    # the manual says goes into the sum.
    body = frame[1:-1]
    assert checksum(body) == frame[-1], (
        "%s: the manual prints %s, and this code computes 0x%02X"
        % (where, printed, checksum(body))
    )


def test_the_one_manual_checksum_that_disagrees_with_the_manual():
    """Read Cool Proportional Band is printed as 84 and the rule gives 8A.

    The Digital Plus Table 1 prints "CA 00 01 74 00 84". Summing 00+01+74+00
    gives 75, and 75 XOR FF is 8A, not 84. The one independent ThermoFlex
    library found also sends 8A.

    This is recorded as a test rather than a comment so that anybody who changes
    the checksum has to come and look at it. A bench visit settles it in one
    command, and it is in REVIEW.md as an item to check.
    """
    body = hexframe("00 01 74 00")
    assert checksum(body) == 0x8A
    assert checksum(body) != 0x84


def test_the_manuals_worked_replies_decode_to_the_temperatures_they_say():
    """The three replies the manuals work through give the right numbers.

    The negative one is the one that matters. A chiller below zero is ordinary,
    and the one open source library found decodes this field as unsigned, which
    would turn -10.5 into 6553.1.
    """
    minus_ten_five = hexframe("CA 00 01 20 03 11 FF 97 34")
    reading = decode_measurement(minus_ten_five[5:8])
    assert reading.value == pytest.approx(-10.5)
    assert reading.unit == "C"
    assert reading.precision == 1

    sixty_two_five = hexframe("CA 00 01 20 03 11 02 71 57")
    assert decode_measurement(sixty_two_five[5:8]).value == pytest.approx(62.5)

    thirty = hexframe("CC 00 03 F0 03 11 01 2C CB")
    assert decode_measurement(thirty[5:8]).value == pytest.approx(30.0)


def test_the_qualifier_byte_table_from_the_manual():
    """All four qualifier values the manual's own table lists."""
    assert split_qualifier(0x10) == (1, "none")
    assert split_qualifier(0x20) == (2, "none")
    assert split_qualifier(0x11) == (1, "C")
    assert split_qualifier(0x21) == (2, "C")


def test_the_manuals_qualifier_example():
    """"The temperature of 45.6 C would be represented by the qualifier 11 hex,
    followed by the 2 bytes 01 C8 hex (456 decimal)." Quoted from Table 2."""
    reading = decode_measurement(hexframe("11 01 C8"))
    assert reading.value == pytest.approx(45.6)
    assert reading.unit == "C"


# ---------------------------------------------------------------------------
# The frame on the wire
# ---------------------------------------------------------------------------

# The manual's Table 1 request frames, against the names this driver uses.
TABLE_1_REQUESTS = [
    ("read_acknowledge", "CA 00 01 00 00 FE"),
    ("read_status", "CA 00 01 09 00 F5"),
    ("read_internal_temperature", "CA 00 01 20 00 DE"),
    ("read_external_sensor", "CA 00 01 21 00 DD"),
    ("read_setpoint", "CA 00 01 70 00 8E"),
    ("read_low_temperature_limit", "CA 00 01 40 00 BE"),
    ("read_high_temperature_limit", "CA 00 01 60 00 9E"),
]


@pytest.mark.parametrize("command_name,printed", TABLE_1_REQUESTS)
def test_build_frame_produces_the_manuals_bytes(command_name, printed):
    """Every frame this driver sends is one the manual printed."""
    chiller, _, _ = make_chiller("RTE_DIGITAL_PLUS")
    assert chiller.build_frame(command_name, target=1) == hexframe(printed)


def test_rs485_uses_the_other_lead_character():
    """CA is RS-232 and CC is RS-485. Same frame otherwise."""
    chiller, _, _ = make_chiller("RTE_DIGITAL_PLUS", address=3, rs485=True)
    frame = chiller.build_frame("read_internal_temperature", target=3)
    assert frame[0] == LEAD_RS485
    assert frame == hexframe("CC 00 03 20 00 DC")

    wired_for_rs232, _, _ = make_chiller("RTE_DIGITAL_PLUS", address=3)
    assert wired_for_rs232.build_frame("read_internal_temperature",
                                       target=3)[0] == LEAD_RS232


def test_the_address_goes_in_the_frame_not_in_the_command():
    """A different address changes two bytes and nothing else."""
    chiller, _, _ = make_chiller("RTE_DIGITAL_PLUS", address=17)
    frame = chiller.build_frame("read_internal_temperature", target=17)
    assert frame[1:3] == b"\x00\x11"
    assert frame[3] == 0x20
    assert checksum(frame[1:-1]) == frame[-1]


def test_reply_size_reads_the_length_out_of_the_frame():
    """This protocol has no terminator. The length is byte four.

    reply_size says "not yet" until five bytes have arrived, then says exactly
    how long the whole frame is. Everything about reading a binary frame off a
    real port depends on this being right.
    """
    frame = hexframe("CA 00 01 20 03 11 02 71 57")
    assert reply_size(b"") is None
    assert reply_size(frame[:4]) is None
    # Five bytes is enough. Three data bytes plus the six of overhead is nine.
    assert reply_size(frame[:5]) == 9
    assert reply_size(frame) == 9
    # A frame with no data bytes at all is six long.
    assert reply_size(hexframe("CA 00 01 20 00")) == 6


def test_the_transport_stops_at_the_end_of_the_frame():
    """It must not read one byte past the frame.

    If it did, the next exchange would start on somebody else's last byte and
    every reply after that would be off by one. So the port is handed two
    replies back to back and the transport has to take only the first.
    """
    first = hexframe("CA 00 01 20 03 11 02 71 57")
    second = hexframe("CA 00 01 70 03 11 01 2C CD")
    port = MockSerial(lambda written: first + second)
    transport = SerialTransport(port, reply_size=reply_size)
    assert transport.exchange(b"anything") == first


def test_the_transport_hands_back_a_short_frame_rather_than_hanging():
    """A chiller that stops halfway gives a short reply, not silence."""
    port = MockSerial(lambda written: hexframe("CA 00 01 20 03 11"))
    transport = SerialTransport(port, reply_size=reply_size)
    assert transport.exchange(b"anything") == hexframe("CA 00 01 20 03 11")


# ---------------------------------------------------------------------------
# The good path
# ---------------------------------------------------------------------------

def test_reading_a_temperature_and_a_setpoint():
    chiller, fake, _ = make_chiller(temperature=18.4, setpoint=18.0)
    assert chiller.read_temperature() == pytest.approx(18.4)
    assert chiller.read_setpoint() == pytest.approx(18.0)
    assert fake.asked == [0x20, 0x70]


def test_a_chiller_below_zero_reads_as_below_zero():
    """The signed integer, end to end, through the mock and the driver.

    This is the bug the one open source library has, and it would only ever
    appear on a chiller cold enough to matter.
    """
    chiller, _, _ = make_chiller("RTE", temperature=-10.5)
    assert chiller.read_temperature() == pytest.approx(-10.5)


def test_the_chiller_states_its_unit_and_the_driver_records_it():
    """Unlike the pressure gauges, this instrument says what its numbers mean."""
    chiller, _, _ = make_chiller()
    pressure = chiller.read("read_supply_pressure")
    assert pressure.unit == "bar"
    assert pressure.value == pytest.approx(3.10)
    assert pressure.precision == 2

    flow = chiller.read("read_flow")
    assert flow.unit == "LPM"
    assert flow.value == pytest.approx(12.4)


def test_a_reading_in_the_wrong_unit_is_refused_not_converted():
    """A front panel switched to Fahrenheit is caught, not quietly converted.

    Converting silently is how a trend column ends up holding two units, with
    every number in it plausible.
    """
    chiller, _, _ = make_chiller(
        units={"read_internal_temperature": ("F", 1)})
    with pytest.raises(DeviceError) as caught:
        chiller.read_temperature()
    assert "F" in str(caught.value)
    assert "refused rather than converted" in str(caught.value)


def test_read_acknowledge_returns_the_version_bytes():
    chiller, _, _ = make_chiller(version=(0x00, 0x01))
    assert chiller.read_acknowledge() == b"\x00\x01"


def test_read_all_returns_every_measurement_this_model_has():
    chiller, _, _ = make_chiller()
    readings = chiller.read_all()
    # Not measurements, so not in here.
    assert "read_acknowledge" not in readings
    assert "read_status" not in readings
    assert readings["read_internal_temperature"] == pytest.approx(18.4)
    assert readings["read_supply_pressure"] == pytest.approx(3.10)


def test_an_rte_has_no_flow_or_pressure_to_read():
    """A bath has no pump pressure. The model decides what exists."""
    chiller, _, _ = make_chiller("RTE")
    assert "read_flow" not in chiller.profile.reads
    with pytest.raises(CommandRefused):
        chiller.query("read_flow", target=1)


# ---------------------------------------------------------------------------
# The failure paths
# ---------------------------------------------------------------------------

def test_a_bad_checksum_is_refused_and_is_not_retried():
    """The whole reason a checksum exists.

    Every byte before the last one decodes into an ordinary temperature. Only
    the checksum says the link corrupted it. And it is not retried, because a
    checksum failure is a link problem, not a busy chiller, and sending the same
    command twice more only fills the log with the same failure.
    """
    chiller, _, port = make_chiller(bad_checksum=["read_internal_temperature"])
    with pytest.raises(DeviceError) as caught:
        chiller.read_temperature()
    assert "checksum did not agree" in str(caught.value)
    assert len(port.written) == 1, "a broken reply must not be retried"


def test_a_truncated_frame_is_refused():
    """The chiller started a reply and stopped. Not the same as silence."""
    chiller, _, port = make_chiller(truncated=["read_internal_temperature"])
    with pytest.raises(DeviceError) as caught:
        chiller.read_temperature()
    assert "data bytes" in str(caught.value)
    assert len(port.written) == 1


def test_silence_is_retried_and_then_gives_up():
    """Three attempts in total, which is the library standard.

    On this instrument the everyday cause of silence is not a fault. Serial
    communication has to be switched on at the front panel, and a chiller with
    it switched off says nothing at all.
    """
    chiller, _, port = make_chiller(silent=["read_internal_temperature"])
    with pytest.raises(NoReply):
        chiller.read_temperature()
    assert len(port.written) == 3


def test_the_chillers_own_error_reply_is_reported_with_its_reason():
    """Command 0F, with the reason byte and the command it received."""
    chiller, _, _ = make_chiller(refused=["read_internal_temperature"])
    with pytest.raises(DeviceError) as caught:
        chiller.read_temperature()
    assert "did not recognise the command byte" in str(caught.value)


def test_a_reply_from_the_wrong_address_is_refused():
    """The RS-485 one. Somebody else's temperature is still a temperature."""
    chiller, _, _ = make_chiller("RTE_DIGITAL_PLUS", address=3, rs485=True,
                                 wrong_address=["read_internal_temperature"])
    with pytest.raises(DeviceError) as caught:
        chiller.read_temperature()
    assert "came from address 4" in str(caught.value)


def test_a_chiller_wired_for_the_other_interface_says_nothing():
    """CC on the wire and CA in the driver means every frame is ignored.

    Worth a test because it looks exactly like a dead cable, and knowing it is
    the rs485 setting saves an hour at the bench.
    """
    fake = ThermoChillerResponder("RTE_DIGITAL_PLUS", address=1, rs485=True)
    port = MockSerial(fake)
    chiller = ThermoChiller(build_transport(port), "RTE_DIGITAL_PLUS",
                            address=1, rs485=False, retry_pause_s=0)
    with pytest.raises(NoReply):
        chiller.read_temperature()


def test_a_reading_that_fails_becomes_a_hole_and_not_a_number():
    """read_all and the poller sources record None, never a stale value."""
    chiller, _, _ = make_chiller(silent=["read_supply_pressure"])
    readings = chiller.read_all()
    assert readings["read_supply_pressure"] is None
    assert readings["read_internal_temperature"] == pytest.approx(18.4)

    sources = chiller.trend_sources()
    assert sources["read_supply_pressure"]() is None
    assert sources["read_internal_temperature"]() == pytest.approx(18.4)


# ---------------------------------------------------------------------------
# A chiller in alarm
# ---------------------------------------------------------------------------

def test_a_thermoflex_in_alarm_reports_its_faults():
    """The case a trend exists to catch.

    A chiller in alarm answers every command normally. Its temperature is still
    a number. Only the status bits say anything is wrong, which is why they are
    read at all.
    """
    chiller, _, _ = make_chiller(faults=["low flow fault",
                                         "high pressure fault"])
    status = chiller.read_status()
    assert status["low flow fault"] is True
    assert status["high pressure fault"] is True
    assert status["running"] is False

    assert chiller.read_faults() == ["high pressure fault", "low flow fault"]


def test_a_healthy_chiller_reports_no_faults():
    chiller, _, _ = make_chiller(faults=["running"])
    assert chiller.read_faults() == []
    assert chiller.read_status()["running"] is True


def test_an_rte_in_alarm_uses_the_rte_bit_table():
    """The two families do not agree on what the bits mean.

    A name set on an RTE has to land in the RTE bit position. This is the test
    that stops the two tables being quietly merged into one.
    """
    chiller, _, _ = make_chiller("RTE_DIGITAL_PLUS",
                                 faults=["low level fault", "pump on"])
    status = chiller.read_status()
    assert status["low level fault"] is True
    assert status["pump on"] is True
    # An RTE has no such thing, so the name must not appear at all.
    assert "low flow fault" not in status
    assert chiller.read_faults() == ["low level fault"]


def test_the_two_status_tables_do_not_share_bit_positions():
    """Proved directly, rather than trusted.

    The same status byte decoded with the two tables gives two different
    answers. If somebody ever merges the tables, this fails.
    """
    one_byte = bytes([0b00000001])
    rte = decode_status(one_byte, MODELS["RTE"].status_bits)
    flex = decode_status(one_byte, MODELS["THERMOFLEX"].status_bits)
    assert rte["RTD3 shorted"] is True
    assert flex["running"] is True
    assert set(rte) != set(flex)


def test_unused_bits_are_not_given_invented_names():
    """The manual marks some bits unused. They stay out of the answer."""
    status = decode_status(bytes(5), MODELS["RTE"].status_bits)
    assert "cool LED on" in status
    assert len(status) == 37, "five bytes of eight bits, minus three unused"


# ---------------------------------------------------------------------------
# The safety gate
# ---------------------------------------------------------------------------

def test_every_write_command_is_refused_by_name():
    """Each banned command, with the reason attached to it."""
    chiller, _, port = make_chiller()
    for command in ["set_setpoint", "set_low_temperature_limit",
                    "set_high_temperature_limit", "set_on_off_array",
                    "set_heat_proportional_band", "set_cool_derivative"]:
        with pytest.raises(CommandRefused) as caught:
            chiller.query(command, target=1)
        assert "banned" in str(caught.value)
    assert port.written == [], "not one banned command became bytes"


def test_setting_a_setpoint_is_refused_and_reading_one_is_not():
    """The pair this device turns on.

    Read Setpoint is command 70 and Set Setpoint is command F0. They do the same
    thing to a chart and opposite things to a machine.
    """
    chiller, _, _ = make_chiller()
    assert chiller.read_setpoint() == pytest.approx(18.0)
    with pytest.raises(CommandRefused) as caught:
        chiller.query("set_setpoint", target=1)
    assert "most dangerous command" in str(caught.value)


def test_a_command_nobody_listed_is_refused_too():
    """The allowed list is what decides, not the banned list."""
    chiller, _, _ = make_chiller()
    with pytest.raises(CommandRefused):
        chiller.query("read_display_message", target=1)


def test_no_allowed_command_on_any_model_writes_anything():
    """Bit 7 set means it writes. Checked across every model at once.

    This is the structural half of the safety gate. It would catch a future
    session adding a command to an allowed list without reading PROTOCOL.md.
    """
    for model, profile in MODELS.items():
        for command_name in profile.reads:
            entry = COMMANDS_BY_NAME[command_name]
            assert entry.byte < WRITE_BIT, (
                "%s allows %s, which is command byte 0x%02X, and every command "
                "with bit 7 set writes something"
                % (model, command_name, entry.byte)
            )


def test_the_command_table_itself_holds_no_write_commands():
    """Nothing this driver knows how to build writes anything."""
    for command in COMMANDS:
        assert command.byte < WRITE_BIT


def test_build_frame_refuses_a_write_byte_even_if_the_policy_let_it_through():
    """The second line of defence, tested on its own.

    The policy is the first. This exists for the case where somebody edits the
    allowed list and not the reasoning, so the two have to be got past
    separately.
    """
    chiller, _, _ = make_chiller()
    COMMANDS_BY_NAME["set_setpoint_for_this_test_only"] = type(
        "FakeCommand", (), {"byte": 0xF0, "name": "x", "label": "x",
                            "unit": None})()
    try:
        with pytest.raises(ValueError) as caught:
            chiller.build_frame("set_setpoint_for_this_test_only", target=1)
        assert "bit 7 set" in str(caught.value)
    finally:
        del COMMANDS_BY_NAME["set_setpoint_for_this_test_only"]


def test_an_address_this_model_cannot_have_is_refused():
    """RS-232 is address 1 only. RS-485 goes to 100."""
    with pytest.raises(CommandRefused):
        make_chiller("RTE", address=7)
    chiller, _, _ = make_chiller("RTE_DIGITAL_PLUS", address=100)
    assert chiller.address == 100
    with pytest.raises(CommandRefused):
        make_chiller("RTE_DIGITAL_PLUS", address=101)


def test_every_model_builds_a_policy_and_settings():
    for model, profile in MODELS.items():
        policy = build_policy(model)
        assert policy.allowed
        assert set(policy.banned) & {"set_setpoint", "set_on_off_array"}
        settings = serial_settings(model)
        assert settings["bytesize"] == 8
        assert settings["parity"] == "N"
        assert settings["timeout"] == 1.0
        assert settings["baud"] == profile.baud
    # The RTE family runs at two speeds, so the override has to work.
    assert serial_settings("RTE", baud=19200)["baud"] == 19200


# ---------------------------------------------------------------------------
# The audit log, the history file and the trend page
# ---------------------------------------------------------------------------

def test_every_frame_is_logged_in_both_directions(tmp_path):
    """A binary protocol makes this matter more, not less.

    You cannot read these frames off the screen, so the log is the only place
    the actual bytes ever exist.
    """
    chiller, _, _ = make_chiller(tmp_path=tmp_path)
    chiller.read_temperature()
    written = list(tmp_path.glob("*.log"))
    assert written, "the audit log wrote nothing"
    text = written[0].read_text()
    assert "ca 00 01 20 00 de" in text.lower()


def test_the_trend_columns_name_their_units():
    columns = history_columns("THERMOFLEX")
    assert "Bath temperature (C)" in columns
    assert "Setpoint (C)" in columns
    assert "Pump supply pressure (bar)" in columns
    assert column_for("read_flow") == "Process flow (LPM)"

    # A bath has no pump, so it has no pressure column.
    rte_columns = history_columns("RTE")
    assert rte_columns == ["Bath temperature (C)", "Setpoint (C)"]


def test_a_page_is_written_from_polled_readings(tmp_path):
    """The whole stack, from the fake chiller to the HTML file.

    The setpoint and the temperature are on the same page on purpose. A chiller
    drifting from its setpoint is what a trend is for, and the drift is
    invisible unless both lines are there.
    """
    chiller, _, _ = make_chiller(temperature=18.4, setpoint=18.0)
    history = HistoryWriter(tmp_path, "chiller",
                            history_columns("THERMOFLEX"))
    sources = {column_for(name): function
               for name, function in chiller.trend_sources().items()}
    poller = Poller(sources, interval_s=0, history=history)
    poller.sweep()
    poller.sweep()

    out = tmp_path / "chiller_trend.html"
    written = write_thermo_chiller_trend_page(tmp_path, "chiller", out,
                                              "THERMOFLEX")
    page = written.read_text(encoding="utf-8")
    assert "Bath temperature (C)" in page
    assert "Setpoint (C)" in page
    assert "18.4" in page
    # The setpoint is drawn over the temperature, on one pair of axes, not on
    # a chart of its own. This is checked here rather than only in the trend
    # page tests because it is the thing this driver exists to show.
    assert "Bath temperature (C) and Setpoint (C)" in page
    assert 'class="line alt"' in page


def test_the_setpoint_shares_the_temperatures_axes():
    """A setpoint on its own chart cannot answer the question it is for.

    Each chart scales to its own readings, so a setpoint that has not moved
    fills its chart exactly as much as a temperature that has drifted. The gap
    between them is the whole point, and it only exists on shared axes.
    """
    overlay = setpoint_overlay("THERMOFLEX")
    assert overlay == {"Bath temperature (C)": "Setpoint (C)"}

    # An RTE has both readings too, so it gets the same treatment.
    assert setpoint_overlay("RTE") == {"Bath temperature (C)": "Setpoint (C)"}


def test_a_failed_reading_leaves_a_gap_in_the_page(tmp_path):
    """A hole is obvious. A number carried over from last time is not."""
    chiller, _, _ = make_chiller(silent=["read_supply_pressure"])
    history = HistoryWriter(tmp_path, "chiller",
                            history_columns("THERMOFLEX"))
    sources = {column_for(name): function
               for name, function in chiller.trend_sources().items()}
    Poller(sources, interval_s=0, history=history).sweep()

    rows = list(tmp_path.glob("chiller_*.csv"))
    assert rows
    text = rows[0].read_text()
    header, first = text.splitlines()[0], text.splitlines()[1]
    column = header.split(",").index("Pump supply pressure (bar)")
    assert first.split(",")[column] == "", "a failed reading must stay empty"


def test_describe_sources_says_out_loud_what_is_unverified():
    """The caveat has to reach the bench, not just PROTOCOL.md."""
    flex, _, _ = make_chiller("THERMOFLEX")
    said = flex.describe_sources()
    assert "not a manual" in said
    assert "REVIEW.md" in said

    rte, _, _ = make_chiller("RTE_DIGITAL_PLUS")
    assert "read directly" in rte.describe_sources()
