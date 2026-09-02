"""The base class every driver builds on.

Why this exists
---------------
The differences between vendors are all in two places. How a message is wrapped
up into a frame, and how a reply is unwrapped. Everything around that is the
same for every device in this library: check the command is allowed, send it,
wait one second, retry twice if nothing comes back, and give up cleanly instead
of hanging.

So a driver subclasses this and writes two small methods, build_frame and
parse_reply. It gets the rest for free, and it gets it the same way every other
driver does.
"""

import time

from .policy import CommandPolicy
from .transport import TransportError


def _describe(command, target):
    """Name a command in a message, including its sub-unit if it has one."""
    if target is None:
        return repr(command)
    return "%r on %r" % (command, target)


class DeviceError(IOError):
    """The device answered, but the answer was not usable."""


class NoReply(DeviceError):
    """The device stayed silent through every attempt."""


class Device:
    """One piece of equipment on the end of a transport.

    transport: a SerialTransport.
    policy:    a CommandPolicy listing the commands this driver may send.
    name:      a plain name used in messages.
    retries:   how many extra attempts to make when a device stays silent. The
               standard for this library is 2, so three attempts in total.
    retry_pause_s: how long to wait before trying again. A device that is busy
               needs a moment. Hammering it immediately usually gets the same
               silence back.
    """

    def __init__(self, transport, policy, name="device", retries=2,
                 retry_pause_s=0.2):
        if not isinstance(policy, CommandPolicy):
            raise TypeError("a device needs a CommandPolicy, so that a command "
                            "that changes machine state cannot be sent by "
                            "accident")
        self.transport = transport
        self.policy = policy
        self.name = name
        self.retries = retries
        self.retry_pause_s = retry_pause_s

    # ---- the two methods a driver must write ----

    def build_frame(self, command, target=None):
        """Turn a command into the exact bytes to put on the wire.

        Every vendor does this differently. The CTI terminal wraps the command in
        a dollar sign, a checksum character and a carriage return. A Lakeshore
        monitor just adds a line ending. Write that here.

        target is the sub-unit this command is aimed at, or None if the device
        has none. A cryopump terminal uses it for the pump address. A driver
        with no sub-units can ignore it.
        """
        raise NotImplementedError("each driver builds its own frames")

    def parse_reply(self, raw):
        """Turn the raw reply bytes into a useful value.

        Check the checksum here if the protocol has one. Check the result code
        here if the protocol has one. Raise DeviceError if the reply is broken,
        because that is a different problem from silence and deserves a different
        message.
        """
        raise NotImplementedError("each driver parses its own replies")

    # ---- what every driver gets for free ----

    def query(self, command, target=None):
        """Send one command and return the parsed reply.

        Raises CommandRefused if the command is not on the allowed list. Raises
        NoReply if the device stayed silent through every attempt. Raises
        DeviceError if a reply arrived but could not be understood.

        A broken reply is not retried. Silence usually means a busy device or a
        dropped frame, and trying again is reasonable. A reply that arrived but
        failed its checksum means something is genuinely wrong with the link or
        the settings, and sending the same command two more times only fills the
        log with the same failure.
        """
        # This is the gate. It runs before the frame exists, so a banned command
        # never becomes bytes. The command and the address are checked
        # separately, so addressing twenty pumps does not mean listing every
        # command twenty times.
        self.policy.check(command)
        self.policy.check_target(target, command)

        frame = self.build_frame(command, target)
        attempts = 1 + self.retries
        audit = getattr(self.transport, "audit", None)

        for attempt in range(1, attempts + 1):
            raw = self.transport.exchange(frame)
            if raw:
                return self.parse_reply(raw)

            if attempt < attempts:
                if audit:
                    audit.note("no reply to %s, attempt %d of %d, trying again"
                               % (_describe(command, target), attempt, attempts))
                time.sleep(self.retry_pause_s)

        if audit:
            audit.note("no reply to %s after %d attempts, marking stale"
                       % (_describe(command, target), attempts))
        raise NoReply(
            "%s did not answer %s after %d attempts. Check the cable, the port "
            "settings, and that nothing else has the port open."
            % (self.name, _describe(command, target), attempts)
        )

    def try_query(self, command, target=None):
        """Like query, but return None instead of raising when it fails.

        Use this in a polling loop, where one unreadable value should not stop
        the other readings. The caller records the None as a gap. Do not use it
        when you need to know why something failed, because the reason is thrown
        away here. It is still written to the audit log.
        """
        try:
            return self.query(command, target)
        except (DeviceError, TransportError):
            return None
