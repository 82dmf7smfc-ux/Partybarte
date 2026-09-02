"""A fake Thermo chiller, so the driver can be built and tested with nothing
attached.

Give one of these to MockSerial as its responder:

    from fab_drivers.core.mock_serial import MockSerial
    fake = ThermoChillerResponder("THERMOFLEX", address=1, temperature=18.4)
    port = MockSerial(fake)

The failure cases matter as much as the good readings, and they are most of why
this file is longer than it looks like it needs to be. The retry logic, the
staleness logic, the checksum check and the address check are only ever
exercised against these.

Six failures are modelled.

1. Silence. The chiller does not answer at all. That is what a wrong baud rate,
   a wrong cable, a wrong address, and serial communication switched off at the
   front panel all look like from here. The last of those is the common one on
   this instrument and it is not a fault.
2. A bad checksum. The frame arrives complete and one byte in it is wrong. This
   is the one that matters most on a binary protocol, because without the
   checksum those bytes would decode into a perfectly plausible temperature.
3. A truncated frame. The chiller starts a reply and stops. The count byte says
   how long the frame should be, so the driver can tell this from silence.
4. An error reply. The chiller answers with command 0F and a reason byte, which
   is what it does when it does not recognise a command or the checksum did not
   agree.
5. A reply from the wrong address. The RS-485 one. Every chiller on the pair
   hears every frame, so a second chiller answering puts somebody else's
   temperature in front of you, and it looks like a temperature.
6. A chiller in alarm. It answers everything normally and its status bits say
   something is wrong. That is the case a trend has to catch, and it is the one
   that is easiest to write a driver that misses.

There is a deliberate choice in here worth knowing about. **This mock computes
its checksums with its own arithmetic, not by calling the driver's checksum
function.** A mock that shares the driver's checksum code agrees with the driver
whatever the driver does, including when the driver is wrong. The one in the
tests is checked against the manual's worked examples instead.
"""

from .driver import (
    COMMANDS_BY_NAME,
    ERROR_COMMAND,
    LEAD_RS232,
    LEAD_RS485,
    MODELS,
    UNIT_NAMES,
)

# The unit index for each unit name, which is the way round the mock needs it.
UNIT_INDEX = {name: index for index, name in UNIT_NAMES.items()}


def mock_checksum(body):
    """The checksum, written out the long way on purpose.

    This is the same arithmetic the driver does and it is deliberately not the
    same code. A mock that imports the driver's checksum will agree with the
    driver even when the driver is wrong, and then the tests prove nothing about
    the one part of this protocol that cannot be eyeballed.

    Add the bytes. Keep the low byte. Flip every bit.
    """
    total = 0
    for byte in body:
        total = total + byte
    low_byte = total % 256
    return low_byte ^ 0xFF


def encode_measurement(value, unit="C", precision=1):
    """The three data bytes for one measurement.

    The qualifier byte first, then the value as a signed 16 bit integer, most
    significant byte first. The qualifier is the number of decimal places in the
    high nibble and the unit index in the low nibble.

    The integer is signed, so a chiller below zero encodes properly. That is the
    manual's own worked example: -10.5 degrees is -105, which is FF 97.
    """
    qualifier = (precision << 4) | UNIT_INDEX[unit]
    scaled = int(round(value * (10 ** precision)))
    return bytes([qualifier]) + scaled.to_bytes(2, byteorder="big", signed=True)


class ThermoChillerResponder:
    """Answers like a real Thermo NESLAB or ThermoFlex chiller.

    model:       "RTE", "RTE_DIGITAL_PLUS" or "THERMOFLEX". It decides which
                 commands this fake knows and what its status bits mean.
    address:     the address this fake chiller is set to. A frame sent to any
                 other address is ignored completely, the way a real chiller on
                 a shared pair ignores one.
    rs485:       True to expect and send the CC lead character instead of CA.
    temperature: the bath temperature it reports.
    setpoint:    the setpoint it reports.
    values:      any other reading by command name, overriding the defaults.
    units:       the unit each command answers in, by command name. Change one
                 to test the driver refusing a reading in the wrong unit.
    faults:      status bit names that are set. Anything not named is clear.
    version:     the two protocol version bytes read_acknowledge returns.

    And the failure switches, each a set of command names:

    silent:      answer nothing at all.
    bad_checksum: answer with the last byte wrong.
    truncated:   answer with the frame cut short.
    wrong_address: answer with somebody else's address in the frame.
    refused:     answer with the chiller's own error reply.
    """

    # The defaults a chiller reports for the readings that are not temperature
    # or setpoint. Plausible numbers for a chiller supplying process water.
    DEFAULT_VALUES = {
        "read_external_sensor": 19.2,
        "read_low_temperature_limit": 5.0,
        "read_high_temperature_limit": 35.0,
        "read_flow": 12.4,
        "read_supply_pressure": 3.10,
        "read_suction_pressure": 0.40,
        "read_low_flow_limit": 4.0,
        "read_high_flow_limit": 20.0,
        "read_low_pressure_limit": 1.0,
        "read_high_pressure_limit": 5.0,
    }

    # What unit each reading comes back in, and to how many decimal places.
    DEFAULT_UNITS = {
        "read_internal_temperature": ("C", 1),
        "read_external_sensor": ("C", 1),
        "read_setpoint": ("C", 1),
        "read_low_temperature_limit": ("C", 1),
        "read_high_temperature_limit": ("C", 1),
        "read_flow": ("LPM", 1),
        "read_supply_pressure": ("bar", 2),
        "read_suction_pressure": ("bar", 2),
        "read_low_flow_limit": ("LPM", 1),
        "read_high_flow_limit": ("LPM", 1),
        "read_low_pressure_limit": ("bar", 2),
        "read_high_pressure_limit": ("bar", 2),
    }

    def __init__(self, model, address=1, rs485=False, temperature=18.4,
                 setpoint=18.0, values=None, units=None, faults=(),
                 version=(0x00, 0x01), silent=(), bad_checksum=(),
                 truncated=(), wrong_address=(), refused=()):
        if model not in MODELS:
            raise ValueError(
                "%r is not a model this mock knows. The ones it knows are: %s"
                % (model, ", ".join(sorted(MODELS)))
            )
        self.profile = MODELS[model]
        self.model = model
        self.address = address
        self.rs485 = rs485
        self.lead = LEAD_RS485 if rs485 else LEAD_RS232

        self.values = dict(self.DEFAULT_VALUES)
        self.values["read_internal_temperature"] = temperature
        self.values["read_setpoint"] = setpoint
        self.values.update(values or {})

        self.units = dict(self.DEFAULT_UNITS)
        self.units.update(units or {})

        self.faults = set(faults)
        self.version = bytes(version)

        self.silent = set(silent)
        self.bad_checksum = set(bad_checksum)
        self.truncated = set(truncated)
        self.wrong_address = set(wrong_address)
        self.refused = set(refused)

        # Every command byte this fake was sent, so a test can assert on the
        # exact conversation rather than only on the answer.
        self.asked = []

        # Which command name goes with which byte, for looking a frame up.
        self.by_byte = {command.byte: name
                        for name, command in COMMANDS_BY_NAME.items()}

    # ---- what the chiller knows about itself ----

    def status_bytes(self):
        """The status data bytes for this fake's fault list.

        Built from whichever bit table this model uses, so a fault name set on a
        ThermoFlex lands in the ThermoFlex bit position and a fault name set on
        an RTE lands in the RTE one. That is the whole point of keeping the two
        tables apart.
        """
        table = self.profile.status_bits
        out = bytearray(len(table))
        for index, names in enumerate(table):
            for bit, name in enumerate(names):
                if name is not None and name in self.faults:
                    # The table reads bit 7 first, the way the manual prints it.
                    out[index] |= 1 << (7 - bit)
        return bytes(out)

    def data_for(self, command_name):
        """The data bytes this fake answers one command with."""
        if command_name == "read_acknowledge":
            return self.version
        if command_name == "read_status":
            return self.status_bytes()
        unit, precision = self.units[command_name]
        return encode_measurement(self.values[command_name], unit, precision)

    # ---- the responder itself ----

    def __call__(self, written):
        """Take the bytes the driver wrote, give back what the chiller would.

        Returning b"" is silence, which is what a real port gives when nothing
        answers before the timeout.
        """
        if len(written) < 6:
            # Not a whole frame. A real chiller is still waiting for the rest of
            # it and has not decided anything yet.
            return b""

        lead = written[0]
        address = (written[1] << 8) | written[2]
        command_byte = written[3]
        self.asked.append(command_byte)

        if lead != self.lead:
            # Wrong lead character. On RS-485 a chiller ignores an RS-232 frame
            # completely, and this looks exactly like a dead cable.
            return b""

        if address != self.address:
            # Not for this chiller. On a shared pair it hears the frame and says
            # nothing, which is the whole point of addressing.
            return b""

        # Check the checksum the way a real chiller does, and answer with its own
        # error reply rather than going silent. This is a real behaviour worth
        # copying: a host with a broken checksum gets told, it does not time out.
        body = written[1:-1]
        if written[-1] != mock_checksum(body):
            return self.error_reply(0x03, command_byte)

        command_name = self.by_byte.get(command_byte)
        if command_name is None or command_name not in self.profile.reads:
            # A command this model does not have. The policy should have refused
            # it long before here, so reaching this in a test means the safety
            # gate leaked.
            return self.error_reply(0x01, command_byte)

        if command_name in self.silent:
            return b""
        if command_name in self.refused:
            return self.error_reply(0x01, command_byte)

        data = self.data_for(command_name)

        if command_name in self.wrong_address:
            # Somebody else's chiller answering. The temperature is perfectly
            # plausible, which is exactly why the driver has to check.
            other = self.address + 1 if self.address < 100 else 1
            return self.good_reply(command_byte, data, address=other)

        frame = self.good_reply(command_byte, data)

        if command_name in self.bad_checksum:
            # One byte wrong, at the end. Everything before it decodes into a
            # perfectly ordinary temperature, which is the point.
            return frame[:-1] + bytes([frame[-1] ^ 0xFF])
        if command_name in self.truncated:
            # The chiller started talking and stopped. The count byte still says
            # how long the frame should have been, so this is not silence.
            return frame[:-2]

        return frame

    def good_reply(self, command_byte, data, address=None):
        """A reply frame: lead, address, command, count, data, checksum."""
        if address is None:
            address = self.address
        body = bytes([0x00, address & 0xFF, command_byte, len(data)]) + data
        return bytes([self.lead]) + body + bytes([mock_checksum(body)])

    def error_reply(self, reason, command_byte):
        """The chiller's own error reply, command 0F.

        Two data bytes: the reason, then the command byte it received. Straight
        from the manual's table.
        """
        data = bytes([reason, command_byte])
        body = bytes([0x00, self.address & 0xFF, ERROR_COMMAND, len(data)]) + data
        return bytes([self.lead]) + body + bytes([mock_checksum(body)])
