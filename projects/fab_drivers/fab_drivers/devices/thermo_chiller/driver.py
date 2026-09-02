"""Read temperature, setpoint, pressure and fault state from Thermo chillers.

Read PROTOCOL.md next to this file before changing anything here. It names every
source and says how strong each one is. Two Thermo NESLAB manuals were read
directly for this driver, which is a first for this project, so most of what
follows is quoted from a manual rather than guessed at.

The short version. This is the first binary protocol in the library. A frame is
a lead character, a two byte address, a command byte, a count of data bytes,
those data bytes, and a checksum. There is no terminator. A frame is found by
its length, and the length is byte four of the frame.

    CA 00 01 20 00 DE        ->   CA 00 01 20 03 11 02 71 57
    read internal temperature      62.5 degrees C

The checksum is the low byte of the sum of everything except the lead character
and the checksum itself, exclusive-ored with FF. Nineteen frames were taken out
of the manuals with the checksums they print, and every one of them is a test.
"""

import time

from ...core.device import Device, DeviceError
from ...core.policy import CommandPolicy
from ...core.transport import TransportError

# The first byte of every frame. Which one depends on the wire, not the model.
LEAD_RS232 = 0xCA
LEAD_RS485 = 0xCC

# The reply that is an error rather than an answer. The host never sends this.
ERROR_COMMAND = 0x0F

# What the first data byte of an error reply means. The first two are from the
# manuals, read directly. The third is from the ThermoFlex library only and is
# in REVIEW.md as unverified.
ERROR_REASONS = {
    0x01: "the chiller did not recognise the command byte",
    0x02: "the chiller rejected the data (this code is not in either manual, "
          "and comes from the ThermoFlex library only)",
    0x03: "the chiller did not agree with the checksum",
}

# Every frame is this many bytes plus its data bytes: lead, address MSB, address
# LSB, command, count, then the data, then the checksum.
HEADER_LENGTH = 5
FRAME_OVERHEAD = HEADER_LENGTH + 1

# Where the count of data bytes sits, counting from zero.
COUNT_INDEX = 4

# Any command byte at or above this writes something. See PROTOCOL.md. This is
# an observed regularity across both manuals' whole command tables, not a rule
# either manual states, so it is a second line of defence and not the first one.
# The allowed list is the first one.
WRITE_BIT = 0x80

# The unit names the low nibble of the qualifier byte can carry. Index 0 and 1
# are from the manual, read directly. The rest are from the ThermoFlex library
# only and are listed in REVIEW.md.
UNIT_NAMES = {
    0: "none",
    1: "C",
    2: "F",
    3: "LPM",
    4: "GPM",
    5: "s",
    6: "PSI",
    7: "bar",
    8: "MOhm.cm",
    9: "%",
    10: "V",
    11: "kPa",
}


class Command:
    """One command byte, with the name the allowed list uses.

    name:   what the driver and the policy call it. A readable name, because a
            list of bare hex bytes is a list nobody can check by eye.
    byte:   the byte that actually goes in the frame.
    label:  a plain description, used in trend column names.
    unit:   the unit this reading is expected to come back in, or None to accept
            whatever the chiller says. The chiller states its unit in every
            reply, so this is checked rather than assumed.
    """

    def __init__(self, name, byte, label, unit=None):
        self.name = name
        self.byte = byte
        self.label = label
        self.unit = unit


# Every command this driver can send. Reads only. The bytes are from the manuals
# except where PROTOCOL.md says otherwise.
COMMANDS = [
    Command("read_acknowledge", 0x00, "Protocol version"),
    Command("read_status", 0x09, "Fault and alarm bits"),
    Command("read_internal_temperature", 0x20, "Bath temperature", unit="C"),
    Command("read_external_sensor", 0x21, "External probe", unit="C"),
    Command("read_setpoint", 0x70, "Setpoint", unit="C"),
    Command("read_low_temperature_limit", 0x40, "Low temperature limit",
            unit="C"),
    Command("read_high_temperature_limit", 0x60, "High temperature limit",
            unit="C"),
    # ThermoFlex only, and from the ThermoFlex library rather than a manual.
    Command("read_flow", 0x10, "Process flow"),
    Command("read_supply_pressure", 0x28, "Pump supply pressure"),
    Command("read_suction_pressure", 0x29, "Pump suction pressure"),
    Command("read_low_flow_limit", 0x30, "Low flow limit"),
    Command("read_high_flow_limit", 0x50, "High flow limit"),
    Command("read_low_pressure_limit", 0x48, "Low pressure limit"),
    Command("read_high_pressure_limit", 0x68, "High pressure limit"),
]

COMMANDS_BY_NAME = {command.name: command for command in COMMANDS}

# Refused before a frame is built, with the reason written next to it. This list
# is not the safety mechanism. Anything missing from a model's allowed list is
# refused too. The list exists so the reason is here, where the next person
# reading the driver will see it. Every byte here is named in a manual.
BANNED_COMMANDS = {
    "set_setpoint":
        "Command F0. Changes the temperature of the water feeding live "
        "equipment. This is the most dangerous command on the instrument, and "
        "it is one byte away from read_setpoint, which is command 70.",
    "set_low_temperature_limit":
        "Command C0. Moves the low alarm limit. Widening an alarm limit does "
        "not change the water. It stops anyone being told the water is wrong, "
        "which is worse, because nothing announces it.",
    "set_high_temperature_limit":
        "Command E0. Moves the high alarm limit. Same reason.",
    "set_heat_proportional_band":
        "Command F1. Retunes the heat side of the control loop. A badly tuned "
        "loop swings for hours, and nobody connects that to a command sent "
        "last week.",
    "set_heat_integral": "Command F2. Same reason as F1.",
    "set_heat_derivative": "Command F3. Same reason as F1.",
    "set_cool_proportional_band":
        "Command F4. Retunes the cool side of the control loop. Same reason "
        "as F1.",
    "set_cool_integral": "Command F5. Same reason as F4.",
    "set_cool_derivative": "Command F6. Same reason as F4.",
    "set_on_off_array":
        "Command 81. Turns the chiller on and off, and switches its faults, "
        "its alarm mute, its auto restart and its serial communications. "
        "Turning the cooling water off under a running tool is the worst "
        "single command in this library. Its own manual notes that a unit shut "
        "down over the serial link has to be restarted over the serial link.",
}


# ---- the fault and alarm bits ----
#
# Two families, two tables, kept apart on purpose. A bit that means "pump on" in
# one and "high pressure fault" in the other would give a trend that is
# confidently wrong. Each table is a list per data byte, bit 7 first, so it
# reads in the same order the manual prints it.

# From the Digital Plus manual, Table 2, read directly.
RTE_STATUS_BITS = [
    ["RTD1 open fault", "RTD1 shorted fault", "RTD1 open", "RTD1 shorted",
     "RTD3 open fault", "RTD3 shorted fault", "RTD3 open", "RTD3 shorted"],
    ["RTD2 open fault", "RTD2 shorted fault", "RTD2 open warn",
     "RTD2 shorted warn", "RTD2 open", "RTD2 shorted", "refrigerant high temp",
     "HTC fault"],
    ["high fixed temp fault", "low fixed temp fault", "high temp fault",
     "low temp fault", "low level fault", "high temp warn", "low temp warn",
     "low level warn"],
    ["buzzer on", "alarm muted", "unit faulted", "unit stopping", "unit on",
     "pump on", "compressor on", "heater on"],
    ["RTD2 controlling", "heat LED flashing", "heat LED on",
     "cool LED flashing", "cool LED on", None, None, None],
]

# From the ThermoFlex library only. Unverified. See REVIEW.md.
THERMOFLEX_STATUS_BITS = [
    ["low temp fault", "high temp fault", "low fixed temp fault",
     "high fixed temp fault", "RTD3 open", "RTD2 open", "RTD1 open",
     "running"],
    ["HPC fault", "LPC fault", "motor overload fault", "phase monitor fault",
     "high level fault", "drip pan fault", "low pressure fault",
     "high pressure fault"],
    ["high pressure fault, factory", "low fixed flow warning",
     "invalid level fault", "5V sense fault", "low level fault",
     "low flow fault", "local EMO fault", "external EMO fault"],
    [None, None, None, None, None, "powering down", "powering up",
     "low pressure fault, factory"],
]


class ModelProfile:
    """What one family of chillers has that the other does not.

    The protocol is the same for both. What differs is which registers exist
    behind it and what the status bits mean. That is a capability list, not a
    second protocol, which is why this is one class and not two. See
    DECISIONS.md.

    name:        what to call it in messages.
    reads:       the command names this model answers, in sweep order.
    trend_reads: the subset worth putting on a trend page, in column order.
    status_bits: which bit table to use.
    status_source: where that bit table came from, said out loud.
    baud:        the default port speed.
    addresses:   the addresses this model can be set to.
    """

    def __init__(self, name, reads, trend_reads, status_bits, status_source,
                 baud, addresses, note=""):
        self.name = name
        self.reads = list(reads)
        self.trend_reads = list(trend_reads)
        self.status_bits = status_bits
        self.status_source = status_source
        self.baud = baud
        self.addresses = list(addresses)
        self.note = note


# Eight data bits, no parity, one stop bit, on every model, from both manuals.
DATA_BITS = 8
PARITY = "N"
STOP_BITS = 1

MODELS = {
    # The older RTE line. RS-232 only, 9600 baud, one address.
    "RTE": ModelProfile(
        "NESLAB RTE",
        reads=["read_acknowledge", "read_status", "read_internal_temperature",
               "read_external_sensor", "read_setpoint",
               "read_low_temperature_limit", "read_high_temperature_limit"],
        trend_reads=["read_internal_temperature", "read_setpoint"],
        status_bits=RTE_STATUS_BITS,
        status_source="the RTE Digital Plus manual, read directly",
        baud=9600,
        addresses=[1],
        note="An RTE 110 or 112 runs at 9600 baud. An RTE Digital Plus, which "
             "is the RTE 7, 10, 17 and 25 family, runs at 19200. Pass baud to "
             "serial_settings to change it.",
    ),

    # The Digital Plus controller. Same commands, RS-485 as well, faster port.
    "RTE_DIGITAL_PLUS": ModelProfile(
        "NESLAB RTE Digital Plus",
        reads=["read_acknowledge", "read_status", "read_internal_temperature",
               "read_external_sensor", "read_setpoint",
               "read_low_temperature_limit", "read_high_temperature_limit"],
        trend_reads=["read_internal_temperature", "read_setpoint"],
        status_bits=RTE_STATUS_BITS,
        status_source="the RTE Digital Plus manual, read directly",
        baud=19200,
        addresses=range(1, 101),
    ),

    # The ThermoFlex chillers. These are the ones with a pump, so these are the
    # ones with flow and pressure to read.
    "THERMOFLEX": ModelProfile(
        "ThermoFlex",
        reads=["read_acknowledge", "read_status", "read_internal_temperature",
               "read_setpoint", "read_low_temperature_limit",
               "read_high_temperature_limit", "read_flow",
               "read_supply_pressure", "read_suction_pressure"],
        trend_reads=["read_internal_temperature", "read_setpoint",
                     "read_supply_pressure", "read_suction_pressure",
                     "read_flow"],
        status_bits=THERMOFLEX_STATUS_BITS,
        status_source="the ThermoFlex library at Dennis-van-Gils/MHT_Tunnel, "
                      "which is working code and not a manual",
        baud=9600,
        addresses=range(1, 101),
        note="Everything on a ThermoFlex beyond the framing and the shared "
             "read commands comes from one open source library and no manual. "
             "The flow and pressure commands and the status bit meanings are "
             "unverified. See REVIEW.md.",
    ),
}


class Reading:
    """One value the chiller reported, with the unit it reported it in.

    value:     the number, already scaled by the precision the chiller stated.
    unit:      the unit name the chiller stated, like "C" or "bar".
    precision: how many decimal places the chiller stated.
    raw:       the signed integer before scaling, kept for the audit trail.
    """

    def __init__(self, value, unit, precision, raw):
        self.value = value
        self.unit = unit
        self.precision = precision
        self.raw = raw

    def __repr__(self):
        return "Reading(%r, %r)" % (self.value, self.unit)


class NcReply:
    """A frame that arrived, unwrapped and checked.

    parse_reply hands one of these back rather than a number or a piece of text.
    A binary protocol has no text stage, and what the data bytes mean depends on
    which command was asked: three bytes are a measurement, five bytes are the
    status bits, and two are a protocol version. So the frame is unwrapped once,
    checked once, and the caller reads the part it wants. See DECISIONS.md.

    lead:    the lead character byte.
    address: the address the chiller echoed back.
    command: the command byte the chiller echoed back.
    data:    the data bytes, without the count and without the checksum.
    raw:     the whole frame, for the log.
    """

    def __init__(self, lead, address, command, data, raw):
        self.lead = lead
        self.address = address
        self.command = command
        self.data = bytes(data)
        self.raw = bytes(raw)

    def __repr__(self):
        return "NcReply(command=0x%02X, data=%s)" % (
            self.command, self.data.hex(" ") if self.data else "none")


def checksum(frame_without_lead_and_checksum):
    """The checksum byte for a frame.

    Quoting both manuals: "Bitwise inversion of the 1 byte sum of bytes
    beginning with the most significant address byte and ending with the byte
    preceding the checksum. (To perform a bitwise inversion, "exclusive OR" the
    one byte sum with FF hex.)"

    So the lead character is not in the sum and neither is the checksum itself.
    Pass everything in between.

    This function is tested against nineteen frames taken out of the two
    manuals with the checksums they print, in tests/test_thermo_chiller.py. A checksum written from a
    description and never checked against a real frame will happily agree with a
    mock that has the same mistake in it, which is the classic way this goes
    wrong.
    """
    return (sum(frame_without_lead_and_checksum) & 0xFF) ^ 0xFF


def reply_size(buffer):
    """How long the reply is, once enough of it has arrived to tell.

    Handed to SerialTransport, which calls it as bytes come in. Returns None
    while it still cannot tell, and the total frame length once it can.

    This protocol has no terminator, because any byte value can appear in a
    payload and so no byte is left over to mean "the end". What it has instead
    is the count of data bytes at index 4. Everything before that is fixed, so
    once five bytes have arrived the whole length is known.
    """
    if len(buffer) < HEADER_LENGTH:
        return None
    return FRAME_OVERHEAD + buffer[COUNT_INDEX]


def split_qualifier(qualifier):
    """Split a qualifier byte into decimal places and a unit name.

    The manual's table lists four values: 10, 20, 11 and 21 hex. Read as two
    nibbles that table is "high nibble is the number of decimal places, low
    nibble is a unit index", which covers all four and the ThermoFlex ones too.

        0x11 -> one decimal place, degrees C
        0x20 -> two decimal places, no unit

    A unit index nothing has a name for comes back as "unit 12" rather than
    raising, because an unknown unit is still worth showing next to a number.
    """
    precision = qualifier >> 4
    index = qualifier & 0x0F
    return precision, UNIT_NAMES.get(index, "unit %d" % index)


def decode_measurement(data):
    """Turn the three data bytes of a measurement into a Reading.

    Quoting the manual: "a qualifier byte is sent first, followed by a two byte
    signed integer (16 bit, MSB sent first)."

    The integer is signed, and that is not a detail. The manual's own worked
    example has FF 97 meaning -105, which is -10.5 degrees. A chiller below zero
    is an ordinary thing. The one open source ThermoFlex library decodes this
    field as unsigned, which is a bug its author would never have hit because a
    ThermoFlex does not go that cold. The manual wins.
    """
    if len(data) != 3:
        raise DeviceError(
            "a measurement is three data bytes, a qualifier and a signed 16 "
            "bit integer, and this reply had %d: %s"
            % (len(data), data.hex(" ") if data else "none")
        )
    precision, unit = split_qualifier(data[0])
    raw = int.from_bytes(data[1:3], byteorder="big", signed=True)
    return Reading(raw / (10.0 ** precision), unit, precision, raw)


def decode_status(data, table):
    """Turn the status data bytes into a dictionary of name to True or False.

    table is a list of eight names per data byte, bit 7 first, so it reads in
    the order the manual prints it. A None in the table is a bit the manual
    marks unused, and it is left out of the answer rather than given a made up
    name.

    The number of data bytes comes from the frame, not from the table, because
    the two families send different numbers of them. A byte the table has no row
    for is ignored, and a row the frame has no byte for is simply not reported.
    """
    flags = {}
    for index, byte in enumerate(data):
        if index >= len(table):
            # The chiller sent more status bytes than this table describes.
            # Nothing here knows what they mean, so nothing here invents a name.
            break
        for bit, name in enumerate(table[index]):
            if name is None:
                continue
            # The table reads bit 7 first, which is how the manual prints it.
            mask = 1 << (7 - bit)
            flags[name] = bool(byte & mask)
    return flags


def build_policy(model):
    """Build the safety gate for one model.

    The commands are listed once and the addresses once, and they are checked
    separately, because the address is part of the frame and not part of what is
    being asked.
    """
    profile = MODELS[model]
    return CommandPolicy(
        "Thermo %s" % profile.name,
        allowed=profile.reads,
        banned=BANNED_COMMANDS,
        targets=profile.addresses,
    )


def serial_settings(model, baud=None):
    """The port settings for one model, ready to pass to open_serial_port.

        from fab_drivers.core.transport import open_serial_port
        port = open_serial_port("COM4", **serial_settings("THERMOFLEX"))

    baud overrides the model default. The RTE family needs that, because an RTE
    110 runs at 9600 and an RTE Digital Plus runs at 19200 and both are RTEs.
    """
    profile = MODELS[model]
    return {
        "baud": baud or profile.baud,
        "bytesize": DATA_BITS,
        "parity": PARITY,
        "stopbits": STOP_BITS,
        "timeout": 1.0,
    }


class ThermoChiller(Device):
    """One Thermo NESLAB or ThermoFlex chiller on a transport.

    model:    "RTE", "RTE_DIGITAL_PLUS" or "THERMOFLEX". It decides which
              commands exist and what the status bits mean, so it has to match
              the instrument in front of you. read_acknowledge tells you
              something is there and answering, but it does not say which model
              it is, so nothing checks this for you.
    address:  the chiller address. Always 1 on RS-232. 1 to 100 on RS-485.
    rs485:    True to use the RS-485 lead character, CC, instead of CA. This is
              about the wire, not the model. Getting it wrong means every frame
              is ignored, which looks like a dead cable.
    pace_s:   how long to wait between queries in the methods that send several.

    Everything else comes from Device: the safety gate, the one second timeout,
    two retries on silence, and the raw frame log.

    The transport this is given has to be built with reply_size, because this
    protocol has no terminator. build_transport below does that for you.
    """

    def __init__(self, transport, model, address=1, rs485=False, name=None,
                 pace_s=0.05, **kwargs):
        if model not in MODELS:
            raise ValueError(
                "%r is not a model this driver knows. The ones it knows are: "
                "%s" % (model, ", ".join(sorted(MODELS)))
            )
        self.profile = MODELS[model]
        self.model = model
        self.address = address
        self.rs485 = rs485
        self.lead = LEAD_RS485 if rs485 else LEAD_RS232
        self.pace_s = pace_s
        Device.__init__(self, transport, build_policy(model),
                        name=name or ("Thermo %s at address %d"
                                      % (self.profile.name, address)),
                        **kwargs)
        # Check the address here rather than letting the first query fail with
        # the same message some minutes into a shift.
        self.policy.check_target(address)

    # ---- the two methods every driver writes ----

    def build_frame(self, command, target=None):
        """Turn a command name into the bytes to put on the wire.

        The command arrives here as a readable name, not a byte. A list of bare
        hex bytes is a list nobody can check by eye, and this is a driver where
        one wrong bit turns a read into a write.

        That is also why there is a second check here. Every write command in
        both manuals has bit 7 set and every read command does not. The allowed
        list is what decides, and this catches the case where somebody edits the
        allowed list without reading PROTOCOL.md first.
        """
        if target is None:
            target = self.address

        entry = COMMANDS_BY_NAME.get(command)
        if entry is None:
            # The policy should have refused this already. Reaching here means
            # the allowed list names something the command table does not have.
            raise ValueError(
                "%r is not a command this driver knows how to build. The ones "
                "it knows are: %s"
                % (command, ", ".join(sorted(COMMANDS_BY_NAME)))
            )

        if entry.byte >= WRITE_BIT:
            raise ValueError(
                "refusing to build a frame for %r, which is command byte "
                "0x%02X. Every command with bit 7 set writes something on this "
                "instrument. Version 1 of this driver reads. If you believe "
                "this command only reads, prove it against the manual's "
                "command table and say so in DECISIONS.md before changing this."
                % (command, entry.byte)
            )

        # Lead character, address as two bytes MSB first, command, then the
        # count of data bytes. A read sends no data, so the count is zero.
        body = [0x00, target & 0xFF, entry.byte, 0x00]
        return bytes([self.lead] + body + [checksum(body)])

    def parse_reply(self, raw):
        """Unwrap a reply frame, check it, and hand back an NcReply.

        Four things are checked here, in this order, because each one explains a
        different failure and the order is from cheapest to most specific.

        1. The length. A short frame means the chiller stopped talking partway
           through, or the port settings are wrong.
        2. The checksum. This is where a bad link is caught, and it is checked
           before anything is read out of the frame, so a corrupted byte never
           becomes a number.
        3. The error command. The chiller says in the frame when it did not like
           the message.
        4. The echoed address. On RS-485 every chiller on the pair hears every
           frame, and somebody else's temperature is a plausible number attached
           to the wrong machine.

        This returns a structure rather than a number or a piece of text,
        because what the data bytes mean depends on which command was asked.
        """
        if len(raw) < FRAME_OVERHEAD:
            raise DeviceError(
                "%s: a reply is at least %d bytes and this one was %d: %s. "
                "Either the chiller stopped partway through, or the baud rate "
                "is wrong."
                % (self.name, FRAME_OVERHEAD, len(raw),
                   raw.hex(" ") if raw else "nothing")
            )

        count = raw[COUNT_INDEX]
        expected_length = FRAME_OVERHEAD + count
        if len(raw) != expected_length:
            raise DeviceError(
                "%s: this reply says it carries %d data bytes, so it should be "
                "%d bytes long, and it is %d: %s"
                % (self.name, count, expected_length, len(raw), raw.hex(" "))
            )

        # Everything except the lead character and the checksum byte.
        body = raw[1:-1]
        want = checksum(body)
        got = raw[-1]
        if got != want:
            raise DeviceError(
                "%s: the checksum did not agree. The frame ends 0x%02X and the "
                "bytes in it add up to 0x%02X. The frame was %s. A checksum "
                "that fails is a link problem, not a busy chiller, so this is "
                "not retried."
                % (self.name, got, want, raw.hex(" "))
            )

        lead = raw[0]
        address = (raw[1] << 8) | raw[2]
        command = raw[3]
        data = raw[HEADER_LENGTH:HEADER_LENGTH + count]

        if command == ERROR_COMMAND:
            # The manual's error replies are two data bytes: a reason, then the
            # command byte the chiller received.
            reason = ERROR_REASONS.get(data[0] if data else None,
                                       "an error code this driver does not know")
            echoed = ("0x%02X" % data[1]) if len(data) > 1 else "not given"
            raise DeviceError(
                "%s: the chiller refused the message. %s. The command it says "
                "it received was %s. The frame was %s."
                % (self.name, reason, echoed, raw.hex(" "))
            )

        if lead != self.lead:
            raise DeviceError(
                "%s: this reply starts 0x%02X and this driver is set up for "
                "0x%02X. CA is RS-232 and CC is RS-485, so the rs485 setting "
                "does not match the wire. The frame was %s."
                % (self.name, lead, self.lead, raw.hex(" "))
            )

        if address != self.address:
            raise DeviceError(
                "%s: this reply came from address %d and the message went to "
                "address %d. On an RS-485 pair every chiller hears every frame, "
                "so this is either a second chiller answering or two hosts "
                "talking at once. The frame was %s."
                % (self.name, address, self.address, raw.hex(" "))
            )

        return NcReply(lead, address, command, data, raw)

    # ---- reading values ----

    def read(self, command_name):
        """Read one measurement. Returns a Reading.

        The unit comes back from the chiller in every reply, so it is checked
        rather than assumed. If a command is expected in degrees C and the
        chiller answers in degrees F, that is an error and not something to
        convert quietly. Two units in one trend column is exactly the failure
        the Granville-Phillips driver had to work around, and here the
        instrument gives us enough to catch it.
        """
        entry = COMMANDS_BY_NAME[command_name]
        reply = self.query(command_name, target=self.address)

        if reply.command != entry.byte:
            raise DeviceError(
                "%s: asked for %s, which is command 0x%02X, and the reply "
                "echoed command 0x%02X"
                % (self.name, command_name, entry.byte, reply.command)
            )

        reading = decode_measurement(reply.data)

        if entry.unit is not None and reading.unit != entry.unit:
            raise DeviceError(
                "%s: %s came back in %s and this driver expects %s. Changing "
                "the units on the front panel changes what every reading "
                "means, so this is refused rather than converted. The frame was "
                "%s." % (self.name, command_name, reading.unit, entry.unit,
                         reply.raw.hex(" "))
            )
        return reading

    def read_temperature(self):
        """The bath or process fluid temperature, in degrees C."""
        return self.read("read_internal_temperature").value

    def read_setpoint(self):
        """The temperature setpoint, in degrees C. Reads it. Does not set it.

        Worth trending next to the temperature. A chiller drifting away from its
        setpoint is the thing a trend is for, and you cannot see the drift
        without both lines.
        """
        return self.read("read_setpoint").value

    def read_status(self):
        """The fault and alarm bits, as a dictionary of name to True or False.

        The names come from whichever table matches this model. On a ThermoFlex
        those names are unverified. See PROTOCOL.md and REVIEW.md.
        """
        reply = self.query("read_status", target=self.address)
        if reply.command != COMMANDS_BY_NAME["read_status"].byte:
            raise DeviceError(
                "%s: asked for the status and the reply echoed command 0x%02X"
                % (self.name, reply.command)
            )
        return decode_status(reply.data, self.profile.status_bits)

    def read_faults(self):
        """Just the faults that are set, as a sorted list of names.

        This is the question a trend actually asks, and it is the one that
        survives the ThermoFlex bit names being unverified. Every bit whose name
        says fault is counted, so "is anything wrong" comes out right even if an
        individual name turns out to be in the wrong place.
        """
        status = self.read_status()
        return sorted(name for name, on in status.items()
                      if on and "fault" in name.lower())

    def read_acknowledge(self):
        """Ask the chiller for its protocol version.

        The safest command on the instrument, and the one to send first at the
        bench. It returns the two version bytes as they arrived, because nothing
        in this project has ever seen what a real one reports.
        """
        reply = self.query("read_acknowledge", target=self.address)
        return reply.data

    def read_all(self):
        """Every measurement this model has, as a dictionary of name to value.

        A reading that failed is None, not a number. A hole in a trend is
        obvious. A wrong number gets averaged in and nobody notices for a week.
        """
        readings = {}
        first = True
        for command_name in self.profile.reads:
            entry = COMMANDS_BY_NAME[command_name]
            if command_name in ("read_acknowledge", "read_status"):
                # Not measurements. read_status has its own method.
                continue
            if not first:
                time.sleep(self.pace_s)
            first = False
            try:
                readings[command_name] = self.read(command_name).value
            except (DeviceError, TransportError):
                # The reason is already in the audit log, which is where you go
                # when a column stops filling in.
                readings[command_name] = None
        return readings

    def trend_sources(self):
        """One reading function per trend column, shaped for Poller.

            poller = Poller(chiller.trend_sources(), interval_s=30,
                            history=history)

        Each function returns a number or None and never raises, which is what
        the poller wants. A None becomes a stale reading and an empty cell in
        the CSV, which the trend page draws as a gap.
        """
        sources = {}
        for command_name in self.profile.trend_reads:
            # The default argument is what pins this command to this function.
            # Without it every function would close over the same variable and
            # they would all read the last command.
            def read_one(command_name=command_name):
                try:
                    return self.read(command_name).value
                except (DeviceError, TransportError):
                    return None

            sources[command_name] = read_one
        return sources

    def describe_sources(self):
        """Say out loud how well sourced this model is.

        Printed by anything that sets a driver up. It exists because the
        ThermoFlex commands are an open source library's word and no manual's,
        and a caveat that only lives in a markdown file is one nobody reads at
        the bench.
        """
        parts = ["Status bit names come from %s." % self.profile.status_source]
        if self.profile.note:
            parts.append(self.profile.note)
        parts.append("See PROTOCOL.md and REVIEW.md before trusting a reading.")
        return " ".join(parts)


def build_transport(serial_port, audit=None, name="chiller"):
    """Wrap an open port in a transport that can read these frames.

    This exists so nobody has to remember to pass reply_size. A transport built
    the ordinary way reads up to a terminator, and this protocol has none, so it
    would sit there until the port timed out and then hand back a frame with the
    next reply's first bytes stuck on the end of it.
    """
    from ...core.transport import SerialTransport
    return SerialTransport(serial_port, audit=audit, name=name,
                           reply_size=reply_size)
