"""A fake serial port, so you can build and test with no hardware attached.

Why this exists
---------------
You cannot keep a production tool tied up while you write code, and the test
suite on GitHub has no serial ports at all. A mock lets the whole stack run on a
desk: the framing, the retries, the audit log, the CSV history, all of it.

This class copies the small part of pyserial's Serial class that the transport
actually uses. If the transport ever needs another method, add it here too, and
the tests keep working.

You give it a responder. That is a function taking the bytes we wrote and
returning the bytes that should come back. Return b"" to act like a device that
stayed silent, which is how you test the retry path.
"""


class MockSerial:
    """Stands in for serial.Serial.

    responder: a function from written bytes to reply bytes. Return b"" for
               silence. If you pass a list instead, each call pops the next
               reply from the front, which is the easy way to script a
               conversation that changes.
    port:      a name, only used in messages.
    """

    def __init__(self, responder, port="mock"):
        self.port = port
        self.is_open = True
        # Everything ever written, so a test can assert on the exact frames.
        self.written = []
        # Everything ever handed back, in the same order.
        self.replies = []
        self._buffer = b""

        if isinstance(responder, (list, tuple)):
            scripted = list(responder)

            def pop_next(_written):
                if not scripted:
                    return b""
                return scripted.pop(0)

            self._responder = pop_next
        else:
            self._responder = responder

    def write(self, data):
        """Accept bytes, and work out what the fake device would reply."""
        if not self.is_open:
            raise IOError("write to a closed mock port")
        self.written.append(bytes(data))
        reply = self._responder(bytes(data)) or b""
        self.replies.append(reply)
        self._buffer += reply
        return len(data)

    def read_until(self, expected=b"\n", size=None):
        """Return buffered bytes up to and including the terminator.

        If the terminator never arrives, return whatever is buffered, which may
        be nothing at all. A real port does the same thing when it times out.
        """
        if not self.is_open:
            raise IOError("read from a closed mock port")
        index = self._buffer.find(expected)
        if index == -1:
            out, self._buffer = self._buffer, b""
            return out
        cut = index + len(expected)
        out, self._buffer = self._buffer[:cut], self._buffer[cut:]
        return out

    def read(self, size=1):
        """Return up to size buffered bytes, the way pyserial's read does.

        If fewer than size bytes are waiting, return what there is. That is what
        a real port does when it times out partway through a reply, and it is
        how the transport tells a short frame from silence.

        This exists for the binary protocols, which have no terminator to read
        up to and carry their own length instead.
        """
        if not self.is_open:
            raise IOError("read from a closed mock port")
        out, self._buffer = self._buffer[:size], self._buffer[size:]
        return out

    def reset_input_buffer(self):
        """Throw away anything not yet read, the way pyserial does."""
        self._buffer = b""

    def close(self):
        self.is_open = False
