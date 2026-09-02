"""A fake Granville-Phillips gauge, so the driver can be built and tested with
nothing attached.

Give one of these to MockSerial as its responder:

    from fab_drivers.core.mock_serial import MockSerial
    fake = GranvillePhillipsResponder("275", address=1, pressures={"CG": 2.4e-3})
    port = MockSerial(fake)

The failure cases matter as much as the good readings, and they are why this
file is longer than it looks like it needs to be. The retry logic, the staleness
logic and the address checking are only ever exercised against these.

Five failures are modelled.

1. Silence. The module does not answer at all, which is what a wrong address, a
   dead cable or a module with no power all look like.
2. A reply with no terminator, which is what wrong port settings look like.
3. A syntax error reply, which is what the instrument sends back when it does
   not recognise the message.
4. A reply from the wrong address. This is the RS-485 one. Every module on the
   pair hears every frame, so a second module answering, or two hosts talking at
   once, puts somebody else's pressure in front of you. It still looks like a
   pressure, which is what makes it dangerous.
5. A gauge that is off or still starting up. Like the Lakeshore sensors, it does
   not go silent. It answers with a number, 9.99E+09, and only knowing what that
   number means saves the trend.
"""

from .driver import MODELS, NO_READING, TERMINATOR, format_address

# What the instrument answers when it has no reading. Documented as the value
# returned for the first few seconds after power up, and reported as what a
# gauge that is not measuring gives as well.
READING_WHEN_OFF = NO_READING

# The error text the instrument sends when it cannot parse a message.
SYNTAX_ERROR = "SYNTX_ER"


def format_pressure(value):
    """Format a pressure the way the instrument does.

    Three significant figures in scientific notation, for example "9.34E-06".
    """
    return "%.2E" % value


class GranvillePhillipsResponder:
    """Answers like a real Granville-Phillips gauge module or controller.

    model:      "275", "375", "350" or "356". It decides which gauges exist.
    address:    the address this fake module is set to. A frame sent to any
                other address is ignored completely, the way a real module on a
                shared pair ignores one.
    pressures:  gauge key to pressure. A gauge left out of this dictionary is
                treated as switched off, and answers 9.99E+09.
    silent:     gauge keys to stay completely silent about, so the retry path
                can be tested.
    garbled:    gauge keys to answer without a terminator, so the broken reply
                path can be tested.
    wrong_address: gauge keys to answer with somebody else's address in the
                reply, so the address check can be tested.
    degas:      what DGS returns.
    setpoints:  what PC S returns.
    """

    def __init__(self, model, address=1, pressures=None, silent=(), garbled=(),
                 wrong_address=(), degas="0", setpoints="0000"):
        if model not in MODELS:
            raise ValueError(
                "%r is not a model this mock knows. The ones it knows are: %s"
                % (model, ", ".join(sorted(MODELS)))
            )
        self.profile = MODELS[model]
        self.address = address
        self.pressures = dict(pressures or {})
        self.silent = set(silent)
        self.garbled = set(garbled)
        self.wrong_address = set(wrong_address)
        self.degas = degas
        self.setpoints = setpoints
        # Every message text this fake was asked, so a test can assert on the
        # exact conversation rather than only on the answer.
        self.asked = []

    # ---- what the instrument knows about one gauge ----

    def pressure_of(self, channel_key):
        """The RD value for one gauge.

        A gauge that is off still answers with a number. That is the behaviour
        worth copying, because a driver that trusts this number will plot 9.99e9
        next to 1e-6 and flatten the chart it was built to draw.
        """
        if channel_key not in self.pressures:
            return READING_WHEN_OFF
        return self.pressures[channel_key]

    def channel_for(self, command):
        """Which gauge a read command is asking about, or None."""
        for channel in self.profile.channels:
            if channel.command == command:
                return channel
        return None

    # ---- the responder itself ----

    def __call__(self, written):
        """Take the bytes the driver wrote, give back what the module would.

        Returning b"" is silence, which is what a real port gives when nothing
        answers before the timeout.
        """
        text = written.decode("ascii", errors="replace")
        if not text.endswith("\r"):
            # A real module waits for the terminator that never came, so it
            # never answers. This is what sending the characters backslash and r
            # as text looks like.
            return b""

        text = text[:-1]
        self.asked.append(text)

        if not text.startswith("#"):
            # No start character. A real module is waiting for one and has no
            # idea a message happened.
            return b""

        addressed = text[1:3]
        command = text[3:]

        if addressed.upper() != format_address(self.address):
            # Not for this module. On a shared pair it hears the frame and says
            # nothing, which is the whole point of addressing.
            return b""

        channel = self.channel_for(command)
        key = channel.key if channel else None

        if key is not None and key in self.silent:
            return b""
        if key is not None and key in self.garbled:
            # A reply that arrived and stopped early. Different from silence, so
            # the driver must not retry it.
            return b"*01 9.34E-0"
        if key is not None and key in self.wrong_address:
            # Somebody else's module answering. The number is perfectly
            # plausible, which is exactly why the driver has to check.
            other = 0 if self.address != 0 else 1
            return self._reply(format_pressure(1.0e-7), address=other)

        if channel is not None:
            return self._reply(format_pressure(self.pressure_of(key)))
        if command == "DGS" and "DGS" in self.profile.extras:
            return self._reply(self.degas)
        if command == "PC S" and "PC S" in self.profile.extras:
            return self._reply(self.setpoints)

        # Anything else. The instrument does not recognise it and says so. The
        # policy should have refused it long before this point, so reaching here
        # in a test means the safety gate leaked.
        return self._error(SYNTAX_ERROR)

    def _reply(self, payload, address=None):
        """A good reply: a star, the address, a space, the payload."""
        if address is None:
            address = self.address
        text = "*%s %s" % (format_address(address), payload)
        return text.encode("ascii") + TERMINATOR

    def _error(self, payload):
        """An error reply: a question mark instead of a star."""
        text = "?%s %s" % (format_address(self.address), payload)
        return text.encode("ascii") + TERMINATOR
