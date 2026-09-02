"""Read pressure from Granville-Phillips gauge modules and controllers.

Read PROTOCOL.md next to this file before changing anything here. It says where
every fact came from and how strongly it is held, which matters a great deal
here because no Granville-Phillips manual could be opened on this machine.

The short version. A message is a start character, a two digit address in
hexadecimal, a command, and a carriage return. There is no checksum. A good
reply starts with a star, an error reply starts with a question mark, and both
echo the address.

    #01RD<CR>   ->   *01 9.34E-06<CR>

The address is in the frame, not in the command, because on RS-485 the same pair
carries messages for several modules. It is checked separately by CommandPolicy,
and the reply's echoed address is checked against it again on the way back.
"""

import time

from ...core.device import Device, DeviceError
from ...core.policy import CommandPolicy
from ...core.transport import TransportError

# Both directions. One byte, 0x0D. There is no line feed.
TERMINATOR = b"\r"

# The character that opens every message to the instrument.
START_CHARACTER = "#"

# A reply beginning with this one carried an answer.
GOOD_MARKER = "*"

# A reply beginning with this one carried an error instead.
ERROR_MARKER = "?"

# What the instrument reports when it has no reading to give. Documented as the
# value returned for the first three to five seconds after power up, and it is
# what a gauge that is not measuring reports as well.
#
# Anything at or above this is treated as no reading. Atmosphere is about 760
# torr, so there is no real pressure anywhere near 1e9 and no chance of throwing
# away a genuine measurement by rounding the test off.
NO_READING = 9.99e9
NO_READING_FLOOR = 1e9

# The units these instruments can be configured for. The driver cannot ask which
# one is set, so the caller has to say. See PROTOCOL.md.
UNITS = ("torr", "mbar", "pascal")


class GaugeChannel:
    """One gauge behind one address.

    key:      the short name used in a reading dictionary and a CSV column.
    command:  the whole read command, including the selector if the model has
              one. "RD" on a single gauge module, "RD A" on a 350.
    label:    a plain description, used in the trend page column name.
    """

    def __init__(self, key, command, label):
        self.key = key
        self.command = command
        self.label = label


class ModelProfile:
    """What one model needs that the others do not.

    name:      the model number, as it is written on the front.
    channels:  the gauges behind one address, in the order they are read.
    extras:    read commands that are not a gauge, like degas status.
    addresses: the addresses this model's switch can be set to.
    baud:      the port speed. The other settings are the same on all four.
    sourced:   True when a manual or read source describes this model's channel
               list. False means the channel list is an assumption, and the
               driver says so out loud in describe_sources().
    """

    def __init__(self, name, channels, addresses, baud=9600, extras=(),
                 sourced=True, note=""):
        self.name = name
        self.channels = list(channels)
        self.extras = list(extras)
        self.addresses = list(addresses)
        self.baud = baud
        self.sourced = sourced
        self.note = note


# Eight data bits, no parity, one stop bit, on every model. That is what an
# ordinary USB to serial adapter defaults to, which makes these easier to get
# talking than the Lakeshore instruments. Sourced for the 375 and the 350 and
# assumed for the other two. See PROTOCOL.md.
DATA_BITS = 8
PARITY = "N"
STOP_BITS = 1

MODELS = {
    # Mini-Convectron module. One Convectron gauge behind one address, so the
    # read command carries no selector.
    "275": ModelProfile(
        "275",
        [GaugeChannel("CG", "RD", "Convectron")],
        addresses=range(0, 16),
        note="Baud rate is assumed to be 9600. The manual's baud section could "
             "not be read.",
    ),

    # Convectron controller. It has more than one channel and nothing found here
    # says how to select one, so it gets the single gauge form and a warning.
    "375": ModelProfile(
        "375",
        [GaugeChannel("CG", "RD", "Convectron")],
        addresses=range(0, 32),
        sourced=False,
        note="The 375 is a multi-channel controller and no source found here "
             "says how to ask it for a particular channel. This driver sends a "
             "bare RD and reads whatever answers. Check which channel that is "
             "against the manual before trusting it.",
    ),

    # Ion gauge controller. Two ion gauges and two Convectron gauges behind one
    # address, each with its own selector.
    "350": ModelProfile(
        "350",
        [GaugeChannel("IG1", "RD 1", "Ion gauge 1"),
         GaugeChannel("IG2", "RD 2", "Ion gauge 2"),
         GaugeChannel("CGA", "RD A", "Convectron A"),
         GaugeChannel("CGB", "RD B", "Convectron B")],
        addresses=range(0, 32),
        extras=["DGS", "PC S"],
    ),

    # Micro-Ion Plus module. One gauge behind one address.
    "356": ModelProfile(
        "356",
        [GaugeChannel("IG", "RD", "Micro-Ion")],
        addresses=range(0, 16),
        note="Baud rate is assumed to be 9600. The manual's baud section could "
             "not be read.",
    ),
}

# Refused before a frame is built, with the reason attached. The reasons matter
# more than the list, because anything missing from the allowed list is refused
# anyway. PROTOCOL.md says which of these mnemonics is sourced and which is
# assumed.
BANNED_COMMANDS = {
    "F1 0": "Turns ion gauge filament 1 off. That blinds whatever interlock is "
            "watching that gauge, and nothing on the tool says why.",
    "F1 1": "Turns ion gauge filament 1 on. A filament switched on at too high "
            "a pressure burns out in seconds.",
    "F2 0": "Turns ion gauge filament 2 off. Same reason as F1 0.",
    "F2 1": "Turns ion gauge filament 2 on. Same reason as F1 1.",
    "DG0 OFF": "Stops degas. Degas is a real machine event and stopping one "
               "partway leaves the gauge in a state nobody chose.",
    "DG1 ON": "Starts degas. It bakes the gauge grid at high power for minutes, "
              "and the gauge does not measure while it runs.",
    "SE0": "Sets the ion gauge emission current. It changes the gauge's "
           "sensitivity, so every later reading means something different.",
    "SE1": "Sets the ion gauge emission current. Same reason as SE0.",
    "SA": "Sets the module address offset. On a shared RS-485 pair that "
          "renumbers a gauge, and every other host talking to it loses it with "
          "no error anywhere.",
    "SW": "Commits settings to the module's nonvolatile memory, so whatever was "
          "wrong stays wrong through a power cycle.",
    "SZ": "Sets the gauge zero. A Convectron zeroed at the wrong pressure is "
          "wrong for ever afterwards and still looks entirely plausible.",
    "SS": "Sets the gauge span, which is the other half of the calibration.",
    "SUT": "Sets the pressure units to torr. Changing units changes what every "
           "reading means, including the readings on the tool's own screen.",
    "SUM": "Sets the pressure units to mbar. Same reason as SUT.",
    "SUP": "Sets the pressure units to pascal. Same reason as SUT.",
}


def build_policy(model):
    """Build the safety gate for one model.

    The commands are listed once and the addresses once. They are checked
    separately, because the address is part of the frame and not part of the
    command. Folding one into the other would mean listing every command against
    every address, which is a list nobody keeps correct.
    """
    profile = MODELS[model]
    allowed = [channel.command for channel in profile.channels]
    allowed.extend(profile.extras)
    return CommandPolicy(
        "Granville-Phillips %s" % profile.name,
        allowed=allowed,
        banned=BANNED_COMMANDS,
        targets=profile.addresses,
    )


def serial_settings(model):
    """The port settings for one model, ready to pass to open_serial_port.

    Use it like this:

        from fab_drivers.core.transport import open_serial_port
        port = open_serial_port("COM4", **serial_settings("275"))
    """
    profile = MODELS[model]
    return {
        "baud": profile.baud,
        "bytesize": DATA_BITS,
        "parity": PARITY,
        "stopbits": STOP_BITS,
        "timeout": 1.0,
    }


def format_address(address):
    """The two characters that carry an address in a frame.

    Hexadecimal, upper case, always two characters. Address 10 is "0A", not
    "10". Getting this wrong sends a frame to a module that is not the one you
    meant, and on a shared pair that module will answer.
    """
    return "%02X" % address


class GranvillePhillipsGauge(Device):
    """One Granville-Phillips gauge module or controller on a transport.

    model:   "275", "375", "350" or "356". It decides which gauges are behind
             one address and what the read commands are, so it has to match the
             instrument in front of you. There is no identity query on these
             instruments, so nothing checks this for you.
    address: the module address, as set on its switch. It goes in every frame.
    units:   "torr", "mbar" or "pascal". There is no default on purpose. These
             instruments do not report which unit they are set to, and this
             driver could find no query that asks. So the caller states it, and
             it goes in the trend column name. A default would have produced a
             file whose units changed halfway through with nothing saying so.
    pace_s:  how long to wait between queries in the methods that send several.

    Everything else comes from Device: the safety gate, the one second timeout,
    two retries on silence, and the raw frame log.
    """

    def __init__(self, transport, model, address=1, units=None, name=None,
                 pace_s=0.05, **kwargs):
        if model not in MODELS:
            raise ValueError(
                "%r is not a model this driver knows. The ones it knows are: "
                "%s" % (model, ", ".join(sorted(MODELS)))
            )
        if units not in UNITS:
            raise ValueError(
                "say which pressure unit this instrument is set to, one of %s. "
                "There is no default, because these instruments do not report "
                "their own units and a wrong guess makes a trend file that "
                "looks right and is not." % ", ".join(UNITS)
            )
        self.profile = MODELS[model]
        self.model = model
        self.address = address
        self.units = units
        self.pace_s = pace_s
        Device.__init__(self, transport, build_policy(model),
                        name=name or ("Granville-Phillips %s at address %s"
                                      % (self.profile.name,
                                         format_address(address))),
                        **kwargs)
        # Check the address once, here, rather than letting the first query fail
        # with the same message some minutes into a shift.
        self.policy.check_target(address)

    # ---- the two methods every driver writes ----

    def build_frame(self, command, target=None):
        """Turn a command into the bytes to put on the wire.

        The start character, the address as two hexadecimal characters, the
        command, then a carriage return. No checksum and no line feed.

        target is the module address. It is separate from the command on
        purpose: on RS-485 one pair carries messages for several modules, and
        the address says which one is being spoken to. It is not part of what is
        being asked.
        """
        if target is None:
            # Every message on this protocol is addressed. A frame with no
            # address is not a thing this driver sends.
            target = self.address
        text = "%s%s%s" % (START_CHARACTER, format_address(target), command)
        return text.encode("ascii") + TERMINATOR

    def parse_reply(self, raw):
        """Unwrap a reply and hand back the payload text.

        Three things are checked here, and the order matters. The terminator,
        because a reply without one means the port settings are wrong. The
        marker character, because an error reply is a different problem from a
        bad one. Then the echoed address, because on a shared pair a reply from
        the wrong module is a plausible pressure attached to the wrong gauge.
        """
        if not raw.endswith(TERMINATOR):
            raise DeviceError(
                "%s: reply did not end with a carriage return: %r. The usual "
                "cause is the wrong port settings, or another device on the "
                "same pair talking over this one." % (self.name, raw)
            )

        text = raw[:-len(TERMINATOR)].decode("ascii", errors="replace")
        if not text:
            raise DeviceError(
                "%s: the reply was a bare terminator with nothing in front of "
                "it" % self.name
            )

        marker, rest = text[0], text[1:]
        if marker == ERROR_MARKER:
            raise DeviceError(
                "%s: the instrument refused the message and answered %r. "
                "SYNTX_ER means it did not recognise the character string it "
                "was sent." % (self.name, text)
            )
        if marker != GOOD_MARKER:
            raise DeviceError(
                "%s: a reply starts with %r or %r, and this one started with "
                "%r: %r" % (self.name, GOOD_MARKER, ERROR_MARKER, marker, text)
            )

        # The address the instrument echoed back, then a space, then the answer.
        echoed, _, payload = rest.partition(" ")
        expected = format_address(self.address)
        if echoed.upper() != expected:
            raise DeviceError(
                "%s: this reply came from address %r, and the message went to "
                "address %r. On an RS-485 pair every module hears every frame, "
                "so this is either a second module answering or two hosts "
                "talking at once. The reply was %r."
                % (self.name, echoed, expected, text)
            )

        return payload.strip()

    # ---- reading values ----

    def read_pressure(self, channel_key=None):
        """Read one gauge. Returns a pair: the pressure, and why it is missing.

        The pressure is None when the instrument had nothing to give, and the
        second half of the pair then says so in plain words.

        This is the shape to use, rather than a bare number, for the same reason
        the Lakeshore driver checks RDGST? alongside every temperature. A gauge
        that is off does not go silent. It answers with a number, 9.99E+09, and
        a driver that trends that number ruins the chart it was built to draw.
        """
        channel = self.channel(channel_key)
        text = self.query(channel.command, target=self.address)

        try:
            value = float(text)
        except ValueError:
            raise DeviceError(
                "%s: expected a pressure back from %s, got %r"
                % (self.name, channel.command, text)
            )

        if value >= NO_READING_FLOOR:
            return None, ("the gauge reported %s, which means it has no reading "
                          "yet. It is starting up, switched off, or not "
                          "measuring." % text)
        if value <= 0:
            # Not documented anywhere found, and not plottable on a log axis
            # either. Treat it as no reading rather than pass it on.
            return None, ("the gauge reported %s, and a pressure cannot be zero "
                          "or negative" % text)
        return value, ""

    def channel(self, channel_key=None):
        """Find one gauge by its short name.

        A model with one gauge does not need to be told which one, so the key
        may be left out there.
        """
        if channel_key is None:
            if len(self.profile.channels) != 1:
                raise ValueError(
                    "a %s has %d gauges behind one address, so say which one. "
                    "They are: %s"
                    % (self.profile.name, len(self.profile.channels),
                       ", ".join(c.key for c in self.profile.channels))
                )
            return self.profile.channels[0]

        for channel in self.profile.channels:
            if channel.key == channel_key:
                return channel
        raise ValueError(
            "%r is not a gauge on a %s. The ones it has are: %s"
            % (channel_key, self.profile.name,
               ", ".join(c.key for c in self.profile.channels))
        )

    def read_all_pressures(self):
        """Every gauge, as a dictionary of key to pressure or None.

        A gauge with no reading is None, not a number. A hole is obvious. A
        wrong number gets averaged into a trend and nobody notices for a week.
        """
        readings = {}
        for index, channel in enumerate(self.profile.channels):
            if index:
                time.sleep(self.pace_s)
            value, _ = self.read_pressure(channel.key)
            readings[channel.key] = value
        return readings

    def read_degas_status(self):
        """Whether degas is running. Only the 350 has this command.

        Worth reading next to a pressure, because a gauge that is degassing is
        not measuring and its number means nothing.
        """
        return self.query("DGS", target=self.address)

    def read_setpoint_status(self):
        """Which process control relays have tripped. The 350 only.

        This reads the relay states. It does not read or change the pressures
        they are set at.
        """
        return self.query("PC S", target=self.address)

    def pressure_sources(self):
        """One reading function per gauge, shaped for Poller.

        Use it like this:

            poller = Poller(gauge.pressure_sources(), interval_s=30,
                            history=history)

        Each function returns a pressure or None, and never raises, which is
        what the poller wants. A None becomes a stale reading and an empty cell
        in the CSV, which the trend page then draws as a gap.
        """
        sources = {}
        for channel in self.profile.channels:
            # The default argument is what pins this channel to this function.
            # Without it every function in the dictionary would close over the
            # same variable and they would all read the last gauge.
            def read_one(channel=channel):
                try:
                    value, _ = self.read_pressure(channel.key)
                    return value
                except (DeviceError, TransportError):
                    # The poller records this as stale. The reason is already in
                    # the audit log, which is where you go when a column stops
                    # filling in.
                    return None

            sources[channel.key] = read_one
        return sources

    def describe_sources(self):
        """Say out loud how well sourced this model is.

        Printed by anything that sets a driver up. It exists because the 375's
        channel handling is an assumption, and an assumption that only lives in
        a markdown file is one nobody reads at the bench.
        """
        if self.profile.sourced and not self.profile.note:
            return ""
        parts = []
        if not self.profile.sourced:
            parts.append("This model is not fully sourced.")
        if self.profile.note:
            parts.append(self.profile.note)
        parts.append("See PROTOCOL.md and REVIEW.md before trusting a reading.")
        return " ".join(parts)
