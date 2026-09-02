"""A fake Lakeshore monitor, so the driver can be built and tested with nothing
attached.

Give one of these to MockSerial as its responder:

    from fab_drivers.core.mock_serial import MockSerial
    fake = LakeshoreResponder("336", {"A": 4.2, "B": 77.35})
    port = MockSerial(fake)

The failure cases matter as much as the good readings, and they are the reason
this file is longer than it looks like it needs to be. The retry logic, the
staleness logic and the status checking are only ever exercised against these.

Four failures are modelled.

1. Silence. The instrument does not answer at all.
2. A reply with no terminator, which is what wrong port settings look like.
3. A sensor that is not connected. This is the interesting one. It does not go
   silent. It answers with a number, and only RDGST? says the number is
   meaningless.
4. A sensor that is out of range, which behaves the same way with a different
   status bit.
"""

from .driver import MODELS, TERMINATOR

# What RDGST? returns for an input that has nothing plugged into it.
#
# This is an assumption. The research file says a nonzero status flags an old
# reading or an over or under range condition, and it does not say which bit an
# unplugged sensor sets. 128 is "sensor units over range", which is what an open
# circuit looks like to the instrument. It is recorded as unverified in
# REVIEW.md. If a bench visit says otherwise, change it here and the tests will
# follow.
STATUS_NOT_CONNECTED = 128

# Temperature over range, for a sensor that is connected and reading past the
# end of its curve.
STATUS_OVER_RANGE = 32

# What KRDG? gives back for an input whose reading is no good. The instrument
# answers with a number rather than an error, which is the whole reason the
# driver has to ask RDGST? as well.
READING_WHEN_BAD = 0.0


def format_reading(value):
    """Format a temperature the way the instrument does.

    A signed fixed width ASCII number, for example "+077.350" or "-012.500".
    The sign is always there, including on a positive number.
    """
    return "%+08.3f" % value


class LakeshoreResponder:
    """Answers like a real Lakeshore 218, 224 or 336.

    model:      which model to imitate. It decides the input names.
    readings:   input name to temperature in kelvin. An input left out of this
                dictionary is treated as having no sensor connected.
    statuses:   input name to the RDGST? value to report, for the inputs where
                you want something other than the default. Use it to fake an out
                of range sensor that is still connected.
    names:      input name to the name a user typed on the front panel.
    silent:     the set of input names to stay completely silent about, so the
                retry path can be tested.
    garbled:    the set of input names to answer without a terminator, so the
                broken reply path can be tested.
    identity:   what *IDN? returns.
    """

    def __init__(self, model, readings=None, statuses=None, names=None,
                 silent=(), garbled=(), identity=None):
        if model not in MODELS:
            raise ValueError(
                "%r is not a model this mock knows. The ones it knows are: %s"
                % (model, ", ".join(sorted(MODELS)))
            )
        self.profile = MODELS[model]
        self.readings = dict(readings or {})
        self.statuses = dict(statuses or {})
        self.names = dict(names or {})
        self.silent = set(silent)
        self.garbled = set(garbled)
        self.identity = identity or (
            "LSCI,MODEL%s,LSA00000,1.7" % self.profile.name.replace("-3062", "")
        )
        # Every command text this fake was asked, so a test can assert on the
        # exact conversation rather than only on the answer.
        self.asked = []

    # ---- what the instrument knows about one input ----

    def status_of(self, sensor_input):
        """The RDGST? value for one input."""
        if sensor_input in self.statuses:
            return self.statuses[sensor_input]
        if sensor_input not in self.readings:
            return STATUS_NOT_CONNECTED
        return 0

    def kelvin_of(self, sensor_input):
        """The KRDG? value for one input.

        An input with a bad status still answers with a number. That is the
        behaviour worth copying, because a driver that trusts this number
        without asking RDGST? will trend a flat zero and nobody will notice for
        a week.
        """
        if self.status_of(sensor_input) != 0:
            return READING_WHEN_BAD
        return self.readings[sensor_input]

    # ---- the responder itself ----

    def __call__(self, written):
        """Take the bytes the driver wrote, give back what the instrument would.

        Returning b"" is silence, which is what a real port gives when nothing
        answers before the timeout.
        """
        text = written.decode("ascii", errors="replace")
        if not text.endswith("\r\n"):
            # A real instrument waits for the terminator that never came, so it
            # never answers. This is what sending the characters backslash and n
            # instead of a real line feed looks like.
            return b""

        text = text[:-2].strip()
        self.asked.append(text)

        parts = text.split(None, 1)
        command = parts[0]
        sensor_input = parts[1].strip() if len(parts) > 1 else None

        if sensor_input in self.silent:
            return b""
        if sensor_input in self.garbled:
            # A reply that arrived and stopped early. This is what the wrong
            # parity does, and it is a different problem from silence, so the
            # driver must not retry it.
            return b"+077.3"

        if command == "*IDN?":
            return self._reply(self.identity)

        if sensor_input is None:
            # A reading query with no input named. A real instrument answers
            # something unhelpful. Silence is close enough and keeps the mock
            # from inventing a format nobody has seen.
            return b""

        if command == "KRDG?":
            return self._reply(self._kelvin_reply(sensor_input))
        if command == "CRDG?":
            return self._reply(format_reading(self.kelvin_of(sensor_input)
                                              - 273.15))
        if command == "SRDG?":
            # Sensor units. A rough stand-in, since the real number depends on
            # what kind of sensor is fitted. The driver only passes it through.
            return self._reply(format_reading(
                self.kelvin_of(sensor_input) / 100.0))
        if command == "RDGST?":
            return self._reply(str(self.status_of(sensor_input)))
        if command == "INNAME?":
            return self._reply(self.names.get(sensor_input, "Input %s"
                                              % sensor_input))

        # An unknown command. A real instrument sets an error bit and stays
        # quiet rather than answering. The policy should have refused it long
        # before this point, so reaching here in a test means the gate leaked.
        return b""

    def _kelvin_reply(self, sensor_input):
        """The KRDG? text, which is one reading or all of them."""
        if (self.profile.batch_all is not None
                and sensor_input == self.profile.batch_all):
            return ",".join(format_reading(self.kelvin_of(name))
                            for name in self.profile.inputs)
        return format_reading(self.kelvin_of(sensor_input))

    def _reply(self, text):
        return text.encode("ascii") + TERMINATOR
