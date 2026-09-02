"""Read temperatures from a Lakeshore 218, 224 or 336 monitor.

Read PROTOCOL.md next to this file before changing anything here. It says where
every fact came from and how strongly it is held.

The short version. All three models speak the same ASCII commands, ended with a
carriage return and a line feed. There is no checksum and no address prefix. A
command that reads one sensor is the command, a space, then the input name.

    KRDG? A<CR><LF>   ->   +077.350<CR><LF>

What differs between the models is the port settings and what the inputs are
called. That is a table, not three separate drivers, so this is one class with a
model setting.
"""

import time

from ...core.device import Device, DeviceError
from ...core.policy import CommandPolicy
from ...core.transport import TransportError

# Both directions. The bytes are 0x0D 0x0A.
TERMINATOR = b"\r\n"

# The commands version 1 may send. Every one of them only reads.
READ_COMMANDS = ["*IDN?", "KRDG?", "CRDG?", "SRDG?", "RDGST?", "INNAME?"]

# Commands aimed at the instrument itself rather than at one of its inputs.
# *IDN? asks the box who it is, and there is no sensor to name.
UNTARGETED_COMMANDS = ["*IDN?"]

# Refused before a frame is built, with the reason attached. The reasons matter
# more than the list. Anything missing from READ_COMMANDS is refused anyway.
BANNED_COMMANDS = {
    "*RST": "Resets the instrument to defaults. On an instrument in service "
            "that throws away the sensor setup, and every later reading is "
            "nonsense. Power cycle it or fix the port settings instead.",
    "*CLS": "Clears the status registers. Often suggested as a harmless wake "
            "up. It destroys state the tool's own software may be waiting to "
            "read. Version 1 reads. It does not clear things.",
    "SETP": "Writes a control setpoint. On a 336 that changes what the heater "
            "is doing to the cryostat.",
    "RANGE": "Sets the heater range on a 336, including off. Turning a heater "
             "off during a controlled warm up is a real machine event.",
    "MOUT": "Sets a manual heater output percentage. Same reason as RANGE.",
    "INTYPE": "Changes what kind of sensor an input is configured for. Every "
              "later temperature is then wrong, and nothing says so.",
    "INCRV": "Assigns a calibration curve to an input. Same silent wrongness.",
    "CRVDEL": "Deletes a user calibration curve, which may exist nowhere else.",
    "DFLT": "Restores factory defaults.",
    "ALARM": "Configures alarms. The instrument may be wired to something that "
             "acts on them.",
    "RELAY": "Drives the relay outputs directly.",
}


class ModelProfile:
    """What one model needs that the others do not.

    inputs:    the sensor input names, as they are written in a command.
    baud:      the port speed. The other settings are the same on all three.
    batch_all: the input name that means "every input at once", or None if this
               driver does not use one on this model. Only the 218 has a
               verified example of it.
    """

    def __init__(self, name, inputs, baud, batch_all=None):
        self.name = name
        self.inputs = list(inputs)
        self.baud = baud
        self.batch_all = batch_all


# Seven data bits and odd parity on all three, with no flow control. That is
# unusual and it is the thing most often got wrong, because nearly every USB to
# serial adapter defaults to eight bits and no parity. Wrong parity looks
# exactly like a dead cable.
DATA_BITS = 7
PARITY = "O"
STOP_BITS = 1

MODELS = {
    # RS-232C on a DE-9 socket. 9600 is the default and the maximum. The
    # instrument can also be set to 300 or 1200, which is worth knowing when
    # somebody has changed it and nothing answers.
    "218": ModelProfile("218", [str(n) for n in range(1, 9)], 9600,
                        batch_all="0"),

    # No DE-9 socket. The USB port enumerates as a virtual COM port, so the
    # ordinary serial transport reaches it. Twelve inputs.
    "224": ModelProfile(
        "224",
        ["A", "B"] + ["C%d" % n for n in range(1, 6)]
                   + ["D%d" % n for n in range(1, 6)],
        57600),

    # Same as the 224 for our purposes, with four inputs.
    "336": ModelProfile("336", ["A", "B", "C", "D"], 57600),

    # A 336 with the 3062 option fitted, which expands input D into D1 to D5.
    # Nobody has confirmed the naming on a real instrument with that card.
    "336-3062": ModelProfile(
        "336-3062",
        ["A", "B", "C"] + ["D%d" % n for n in range(1, 6)],
        57600),
}

# The bits RDGST? sets. Zero means the reading is good.
READING_STATUS_BITS = [
    (1, "invalid reading"),
    (16, "temperature under range"),
    (32, "temperature over range"),
    (64, "sensor units zero"),
    (128, "sensor units over range"),
]


def describe_status(status):
    """Turn an RDGST? number into words. Returns "" when the reading is good."""
    if status == 0:
        return ""
    reasons = [text for bit, text in READING_STATUS_BITS if status & bit]
    if not reasons:
        # A bit we do not have a name for. Say the number rather than pretend
        # the reading is fine.
        return "reading status %d" % status
    return ", ".join(reasons)


def serial_settings(model):
    """The port settings for one model, ready to pass to open_serial_port.

    Use it like this:

        from fab_drivers.core.transport import open_serial_port
        port = open_serial_port("COM3", **serial_settings("336"))
    """
    profile = MODELS[model]
    return {
        "baud": profile.baud,
        "bytesize": DATA_BITS,
        "parity": PARITY,
        "stopbits": STOP_BITS,
        "timeout": 1.0,
    }


def build_policy(model):
    """Build the safety gate for one model.

    The commands are listed once and the inputs once. They are checked
    separately, so a 224 with twelve inputs still needs six allowed entries
    rather than seventy two.
    """
    profile = MODELS[model]
    targets = list(profile.inputs)
    if profile.batch_all is not None:
        targets.append(profile.batch_all)
    return CommandPolicy(
        "Lakeshore %s" % profile.name,
        allowed=READ_COMMANDS,
        banned=BANNED_COMMANDS,
        targets=targets,
        untargeted=UNTARGETED_COMMANDS,
    )


class LakeshoreMonitor(Device):
    """One Lakeshore 218, 224 or 336 on the end of a transport.

    model:  "218", "224", "336" or "336-3062". It decides the input names and
            the port speed, so it has to match the instrument in front of you.
    pace_s: how long to wait between queries in the methods that send several.
            Working implementations use about 50 milliseconds. Do not send
            queries back to back, especially to a 218 at 9600 baud.

    Everything else comes from Device: the safety gate, the one second timeout,
    two retries on silence, and the raw frame log.
    """

    def __init__(self, transport, model, name=None, pace_s=0.05, **kwargs):
        if model not in MODELS:
            raise ValueError(
                "%r is not a model this driver knows. The ones it knows are: "
                "%s" % (model, ", ".join(sorted(MODELS)))
            )
        self.profile = MODELS[model]
        self.model = model
        self.pace_s = pace_s
        Device.__init__(self, transport, build_policy(model),
                        name=name or ("Lakeshore %s" % self.profile.name),
                        **kwargs)

    # ---- the two methods every driver writes ----

    def build_frame(self, command, target=None):
        """Turn a command into the bytes to put on the wire.

        No checksum, no address prefix, no start character. The command, then
        the input name if there is one, then a carriage return and a line feed.
        """
        text = command if target is None else "%s %s" % (command, target)
        return text.encode("ascii") + TERMINATOR

    def parse_reply(self, raw):
        """Strip the terminator and hand back the text.

        The reply is checked for its terminator here. A reply that arrives
        without one is a broken reply rather than silence, and the base class
        treats the two differently on purpose: silence is retried, a broken
        reply is not. Retrying a broken reply just writes the same failure to
        the log three times, because the cause is usually the port settings.
        """
        if not raw.endswith(TERMINATOR):
            raise DeviceError(
                "%s: reply did not end with a carriage return and a line feed: "
                "%r. The usual cause is the wrong port settings. These "
                "instruments want 7 data bits with odd parity, which is not "
                "what a USB to serial adapter defaults to." % (self.name, raw)
            )

        text = raw[:-len(TERMINATOR)].decode("ascii", errors="replace").strip()
        if not text:
            raise DeviceError(
                "%s: the reply was a bare terminator with nothing in front of "
                "it" % self.name
            )
        return text

    # ---- reading values ----

    def identify(self):
        """Ask the instrument who it is.

        Returns the whole identity string, for example
        "LSCI,MODEL218S,1234567,1.7". Read it once when connecting and check it
        against the model this driver was built for. A 218 driver pointed at a
        336 will address inputs that do not exist.
        """
        return self.query("*IDN?")

    def _read_number(self, command, sensor_input):
        """Send one reading query and turn the reply into a number."""
        text = self.query(command, target=sensor_input)
        try:
            return float(text)
        except ValueError:
            raise DeviceError(
                "%s: expected a number back from %s on input %s, got %r"
                % (self.name, command, sensor_input, text)
            )

    def read_kelvin(self, sensor_input):
        """Temperature in kelvin. The main reading."""
        return self._read_number("KRDG?", sensor_input)

    def read_celsius(self, sensor_input):
        """Temperature in celsius."""
        return self._read_number("CRDG?", sensor_input)

    def read_sensor_units(self, sensor_input):
        """The raw sensor reading, in volts or ohms depending on the sensor.

        Worth having when a temperature looks wrong, because it says whether
        the sensor itself is reading anything at all.
        """
        return self._read_number("SRDG?", sensor_input)

    def read_status(self, sensor_input):
        """Reading status as a number. Zero means the reading is good."""
        text = self.query("RDGST?", target=sensor_input)
        try:
            return int(text)
        except ValueError:
            raise DeviceError(
                "%s: expected a number back from RDGST? on input %s, got %r"
                % (self.name, sensor_input, text)
            )

    def read_input_name(self, sensor_input):
        """The name somebody typed on the front panel for that input.

        Read it once at start up so a trend column can say "Cold head" instead
        of "A".
        """
        return self.query("INNAME?", target=sensor_input)

    def read_checked_kelvin(self, sensor_input):
        """Temperature in kelvin, or None if the instrument says do not trust it.

        This is the one to use in a polling loop, and the reason is the thing
        most likely to catch somebody out with these instruments. A sensor that
        is unplugged, shorted or out of range does not go silent. It answers
        with a number. Only RDGST? says the number means nothing.

        Returns a pair: the temperature or None, and a plain description of what
        is wrong when it is None.
        """
        status = self.read_status(sensor_input)
        if status != 0:
            return None, describe_status(status)

        time.sleep(self.pace_s)
        return self.read_kelvin(sensor_input), ""

    def read_all_kelvin(self):
        """Every input, as a dictionary of input name to temperature or None.

        On a 218 this is one query, because KRDG? 0 returns all eight readings
        on one comma separated line and that form has a worked example behind
        it. On the other models it asks each input in turn, pausing between
        queries.

        A reading the instrument flags is None, not a number. A wrong number is
        worse than a hole, because a hole is obvious and a wrong number gets
        averaged into a trend.
        """
        if self.profile.batch_all is not None:
            return self._read_all_at_once()

        readings = {}
        for index, sensor_input in enumerate(self.profile.inputs):
            if index:
                time.sleep(self.pace_s)
            value, _ = self.read_checked_kelvin(sensor_input)
            readings[sensor_input] = value
        return readings

    def _read_all_at_once(self):
        """Read every input with one query, then check each one's status.

        The batch query does not carry status, so the statuses still have to be
        asked for one at a time. It is still fewer round trips than reading
        eight temperatures separately, and on a 218 at 9600 baud that counts.
        """
        text = self.query("KRDG?", target=self.profile.batch_all)
        parts = [part.strip() for part in text.split(",")]

        if len(parts) != len(self.profile.inputs):
            raise DeviceError(
                "%s: asked for every input and got %d readings back, expected "
                "%d. The reply was %r. Check the model setting matches the "
                "instrument." % (self.name, len(parts),
                                 len(self.profile.inputs), text)
            )

        readings = {}
        for sensor_input, part in zip(self.profile.inputs, parts):
            time.sleep(self.pace_s)
            if self.read_status(sensor_input) != 0:
                readings[sensor_input] = None
                continue
            try:
                readings[sensor_input] = float(part)
            except ValueError:
                raise DeviceError(
                    "%s: input %s came back as %r, which is not a number"
                    % (self.name, sensor_input, part)
                )
        return readings

    def kelvin_sources(self):
        """One reading function per input, shaped for Poller.

        Use it like this:

            poller = Poller(monitor.kelvin_sources(), interval_s=30,
                            history=history)

        Each function returns a temperature or None, and never raises, which is
        what the poller wants. A None becomes a stale reading and an empty cell
        in the CSV.
        """
        sources = {}
        for sensor_input in self.profile.inputs:
            # The default argument is what pins the input name to this
            # function. Without it every function in the dictionary would
            # close over the same variable and they would all read the last
            # input.
            def read_one(sensor_input=sensor_input):
                try:
                    value, _ = self.read_checked_kelvin(sensor_input)
                    return value
                except (DeviceError, TransportError):
                    # The poller records this as stale. The reason is already
                    # in the audit log, which is where you go when a column
                    # stops filling in.
                    return None

            sources[sensor_input] = read_one
        return sources
