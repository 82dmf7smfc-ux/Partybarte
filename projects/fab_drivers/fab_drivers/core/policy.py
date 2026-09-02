"""Decide which commands a driver is allowed to send.

Why this exists
---------------
These tools connect to production equipment. Some commands only read a value.
Others change what the machine is doing. A regen start on a cryopump is a
multi-hour machine event. A port lockout command can cut the tool's own software
off from its pumps.

Version 1 of every driver in this library is read-only. The safe way to hold
that line is not to remember it. It is to make the wrong command impossible to
send. A driver lists the commands it is allowed to use. Anything not on that
list is refused here, before a single byte reaches the port.

This runs before the frame is built, so a banned command never becomes bytes.
"""


class CommandRefused(Exception):
    """Raised when a command is not on the allowed list.

    Catching this in a driver would defeat the point. Let it stop the program.
    """


class CommandPolicy:
    """The list of commands one device is allowed to receive.

    device_name: a plain name used in error messages, like "Lakeshore 336".
    allowed:     the commands this driver may send. Read commands only in v1.
    banned:      commands that are known to be dangerous on this device. These
                 are refused with a louder message that says why. A command does
                 not need to be listed here to be refused. Anything missing from
                 'allowed' is refused too. This list exists so the reason is
                 recorded next to the command, where the next person will read
                 it.
    targets:     which sub-units this command may be aimed at, or None if the
                 device has none. Many devices are really a box with several
                 things behind it. A cryopump terminal has up to twenty pumps. A
                 gauge controller has several sensors. The address is not part
                 of the command, and mixing the two makes the allowed list
                 explode: twenty addresses and eight commands would be one
                 hundred and sixty entries to keep correct, which nobody will.
                 So the command is checked against the allowed list, and the
                 address is checked against this, separately.
    """

    def __init__(self, device_name, allowed, banned=None, targets=None,
                 untargeted=None):
        self.device_name = device_name
        # A set makes the check fast and makes duplicates harmless.
        self.allowed = set(allowed)
        # Banned entries map a command to the reason it must never be sent.
        self.banned = dict(banned or {})
        # None means this device has no sub-units to address.
        self.targets = None if targets is None else set(targets)
        # Commands that are aimed at the box itself rather than at one of its
        # sub-units, even though the device has sub-units. A Lakeshore monitor
        # is the example: KRDG? asks one sensor input, but *IDN? asks the
        # instrument who it is, and there is no input to name. Without this the
        # only ways out were to invent an address meaning "the box", or to let
        # every command be sent with no address, which would stop the check
        # catching a missing one.
        self.untargeted = set(untargeted or ())

        # A command in both lists is a mistake in the driver, not a runtime
        # problem. Catch it as early as possible, when the policy is built.
        overlap = self.allowed & set(self.banned)
        if overlap:
            raise ValueError(
                "%s: these commands are both allowed and banned: %s"
                % (device_name, ", ".join(sorted(overlap)))
            )

        # An untargeted command that is not allowed at all is a typo in the
        # driver. Catching it here beats finding it when a sweep fails.
        unknown = self.untargeted - self.allowed
        if unknown:
            raise ValueError(
                "%s: these are listed as untargeted but are not on the allowed "
                "list: %s" % (device_name, ", ".join(sorted(unknown)))
            )

    def check(self, command):
        """Let the command through, or raise CommandRefused.

        Returns the command unchanged so a caller can write:
            command = policy.check(command)
        """
        if command in self.banned:
            raise CommandRefused(
                "%s: command %r is banned. %s"
                % (self.device_name, command, self.banned[command])
            )
        if command not in self.allowed:
            raise CommandRefused(
                "%s: command %r is not on the read-only allowed list. If this "
                "command only reads a value, add it to the driver's allowed "
                "list and say so in DECISIONS.md. If it changes what the "
                "machine is doing, it does not belong in this version."
                % (self.device_name, command)
            )
        return command

    def check_target(self, target, command=None):
        """Let the sub-unit address through, or raise CommandRefused.

        A typo in an address is not a safety problem the way a control command
        is. It is still worth catching here, because the alternative is a frame
        going out to a pump that does not exist and a confusing reply coming
        back that someone has to work out.

        command is optional, and is only used to spot the commands that are
        aimed at the box itself rather than at one of its sub-units.
        """
        if command is not None and command in self.untargeted:
            if target is not None:
                raise CommandRefused(
                    "%s: command %r is aimed at the instrument itself, not at "
                    "one of its sub-units, but a target of %r was given"
                    % (self.device_name, command, target)
                )
            return target

        if self.targets is None:
            if target is not None:
                raise CommandRefused(
                    "%s: this device has no sub-units, so there is nothing to "
                    "address, but a target of %r was given"
                    % (self.device_name, target)
                )
            return target

        if target not in self.targets:
            raise CommandRefused(
                "%s: %r is not one of this device's sub-units. The ones it has "
                "are: %s" % (self.device_name, target,
                             ", ".join(str(t) for t in sorted(self.targets)))
            )
        return target

    def is_allowed(self, command):
        """Answer the same question without raising. Useful in tests and menus."""
        return command in self.allowed and command not in self.banned
