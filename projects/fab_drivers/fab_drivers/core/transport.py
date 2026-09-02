"""Own the serial port. Send one frame, wait for one reply.

Why this exists
---------------
Two programs talking on the same port at the same time produce replies that
arrive out of order and frames that interleave. On a fab tool that looks like a
device fault, and people go hunting for a hardware problem that is not there.

So the rule for this whole library is: exactly one process opens a port, and
that process does one exchange at a time. This class is where that rule lives.

It also writes every frame to the audit log, in both directions, before anything
else gets a chance to fail. If an exchange goes wrong, the log already has the
bytes.
"""

import threading

from .audit import AuditLog


class TransportError(IOError):
    """Something went wrong talking to the port."""


class PortBusy(TransportError):
    """This process already has that port open somewhere else."""


# Every port name this process currently holds. The rule is one owner per port,
# and this is how we notice when code accidentally tries to open a second one.
# It cannot see other processes on the machine. It catches the mistake that
# actually happens, which is one program opening the same port twice.
_open_ports = set()
_open_ports_lock = threading.Lock()


class SerialTransport:
    """One serial port, one exchange at a time.

    serial_port: an open pyserial Serial object, or a MockSerial. This class
                 does not open the port itself. That keeps it testable, and it
                 means the caller decides the settings, which differ a lot
                 between vendors. Use open_serial_port below for a real one.
    audit:       an AuditLog, or None to skip logging. Real use should always
                 pass one.
    terminator:  the byte or bytes that end a reply, usually b"\\r" or b"\\n".
                 Ignored when reply_size is given.
    name:        a plain name for messages and for the busy check.
    reply_size:  how to tell when a reply that has no terminator is complete.
                 Leave it None for a text protocol, which is the common case,
                 and the reply is read up to the terminator as before.

                 A binary protocol cannot use a terminator. Any byte value can
                 appear in the payload, so there is no byte left over to mean
                 "the frame ends here". The Thermo chiller protocol is the first
                 one in this library like that, and the AE Bus and Modbus
                 drivers later on will be too.

                 What those protocols have instead is a length somewhere near
                 the front of the frame. So a driver passes a function here.
                 It is given the bytes that have arrived so far and returns the
                 total length of the frame once it can work it out, or None to
                 mean "I still cannot tell, give me one more byte".

                 The transport then reads exactly that many bytes and stops. It
                 never guesses. A device that stops halfway through a frame
                 gives back a short reply, and the driver notices when it checks
                 the checksum.
    max_reply_bytes: a stop so a device that will not stop talking cannot hang
                 the loop. Only used when reply_size is given.
    """

    def __init__(self, serial_port, audit=None, terminator=b"\r", name="port",
                 reply_size=None, max_reply_bytes=512):
        self.serial = serial_port
        self.audit = audit
        self.terminator = terminator
        self.name = name
        self.reply_size = reply_size
        self.max_reply_bytes = max_reply_bytes
        # One exchange at a time, even if a future version polls from a thread
        # while the UI asks for something.
        self._lock = threading.Lock()

    def exchange(self, frame):
        """Write one frame, return the raw reply bytes.

        Returns b"" if the device stayed silent until the port timed out.
        Silence is a normal thing to get back, not a crash. The layer above
        decides whether to retry.
        """
        if not isinstance(frame, (bytes, bytearray)):
            raise TypeError("a frame must be bytes, got %s" % type(frame).__name__)

        with self._lock:
            # Anything still sitting in the buffer belongs to a previous, failed
            # exchange. Reading it now would pair the wrong reply with this
            # command, which is worse than getting nothing.
            self.serial.reset_input_buffer()

            if self.audit:
                self.audit.sent(frame)
            self.serial.write(frame)

            if self.reply_size is None:
                reply = self.serial.read_until(self.terminator)
            else:
                reply = self._read_sized()
            reply = bytes(reply or b"")
            if self.audit:
                self.audit.received(reply)
            return reply

    def _read_sized(self):
        """Read a reply whose length is written inside it.

        This is the path for a binary protocol with no terminator. It reads one
        byte at a time until reply_size can say how long the whole frame is,
        then asks for exactly the rest of it in one go.

        Reading one byte at a time sounds slow and is not. The bytes are already
        on their way, so each read returns immediately, and only the last one
        waits. It matters that this stops at the length the frame declares: read
        one byte more and the next exchange gets somebody else's first byte, and
        every reply after that is off by one.
        """
        buffer = b""
        while True:
            total = self.reply_size(buffer)
            if total is None:
                # Cannot tell yet. Ask for one more byte and look again.
                if len(buffer) >= self.max_reply_bytes:
                    # Something is talking and never stopping. Give the caller
                    # what arrived and let it fail the checksum, rather than
                    # sitting here forever.
                    return buffer
                wanted = 1
            elif len(buffer) >= total:
                return buffer
            else:
                wanted = total - len(buffer)

            chunk = self.serial.read(wanted)
            if not chunk:
                # The port timed out. A short frame is not silence, and the
                # driver needs to be able to tell the difference, so hand back
                # what did arrive.
                return buffer
            buffer += chunk

    def close(self):
        """Close the port and give up ownership of the name."""
        try:
            self.serial.close()
        finally:
            release_port(self.name)


def claim_port(name):
    """Record that this process now owns a port name."""
    with _open_ports_lock:
        if name in _open_ports:
            raise PortBusy(
                "this program already has %s open. One process owns one port, "
                "and one port has one owner. Reuse the transport you already "
                "made instead of opening a second one." % name
            )
        _open_ports.add(name)


def release_port(name):
    """Forget a port name, so it can be opened again."""
    with _open_ports_lock:
        _open_ports.discard(name)


def open_serial_port(port, baud=9600, bytesize=8, parity="N", stopbits=1,
                     timeout=1.0):
    """Open a real serial port with pyserial and return the Serial object.

    The defaults are the common case, 8 data bits, no parity, one stop bit. Some
    equipment is not the common case. The CTI On-Board terminal, for example,
    wants 7 data bits with even parity. Pass what the manual says, not what looks
    familiar.

    timeout is in seconds and defaults to 1, which is the standard for this
    library. A device that has not answered in a second is not going to.

    pyserial is imported here rather than at the top of the file on purpose. The
    core layer can then be tested with the mock on a machine that has no pyserial
    installed, which is what the CI runner is.
    """
    try:
        import serial
    except ImportError:
        raise TransportError(
            "pyserial is not installed. It is pinned in this project's "
            "requirements.txt. On an offline machine install it from the wheel "
            "IT provided."
        )

    sizes = {5: serial.FIVEBITS, 6: serial.SIXBITS, 7: serial.SEVENBITS,
             8: serial.EIGHTBITS}
    parities = {"N": serial.PARITY_NONE, "E": serial.PARITY_EVEN,
                "O": serial.PARITY_ODD}
    stops = {1: serial.STOPBITS_ONE, 2: serial.STOPBITS_TWO}

    if bytesize not in sizes:
        raise ValueError("bytesize must be one of %s" % sorted(sizes))
    if parity not in parities:
        raise ValueError("parity must be N, E or O")
    if stopbits not in stops:
        raise ValueError("stopbits must be 1 or 2")

    claim_port(port)
    try:
        return serial.Serial(port, baud, bytesize=sizes[bytesize],
                             parity=parities[parity], stopbits=stops[stopbits],
                             timeout=timeout)
    except Exception:
        # If opening failed we do not own the port after all.
        release_port(port)
        raise
