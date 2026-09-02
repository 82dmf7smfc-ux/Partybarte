"""Write every raw frame to a dated log file.

Why this exists
---------------
When something looks wrong on a tool, the first question is always the same.
What did we actually send, and what came back? A summary cannot answer that. The
exact bytes can.

This writes one line per event, with a timestamp, to a file named for the day.
It never deletes anything. A new day starts a new file, so the files stay a
sensible size on their own and old ones can be archived or removed by hand.

Bytes are written in two forms on the same line. A readable form with the
non-printing characters escaped, and a hex form. The readable form is what you
scan by eye. The hex form is what you trust when the readable form is confusing,
which happens with checksum characters and control bytes.
"""

import datetime
from pathlib import Path


def _hex_of(data):
    """Return bytes as spaced hex pairs, like '24 50 30 31'."""
    return " ".join("%02X" % b for b in data)


def _readable(data):
    """Return bytes as text, with anything unprintable escaped.

    This uses the same escaping Python shows in a repr, minus the surrounding
    quotes. A carriage return shows as \\r, so a line in the log stays a line.
    """
    return repr(data)[2:-1]


class AuditLog:
    """Append raw traffic to one file per day inside a folder.

    folder: where the files go. It is created if it is missing.
    name:   the first part of each file name, usually the device name.

    A file is called <name>_<date>.log, for example cti_terminal_2026-09-02.log.
    """

    def __init__(self, folder, name):
        self.folder = Path(folder)
        self.name = name
        self.folder.mkdir(parents=True, exist_ok=True)

    def path_for(self, when=None):
        """Return the file this event belongs in, based on its date."""
        when = when or datetime.datetime.now()
        return self.folder / ("%s_%s.log" % (self.name, when.strftime("%Y-%m-%d")))

    def _write(self, direction, text, when=None):
        when = when or datetime.datetime.now()
        stamp = when.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        line = "%s  %-4s  %s\n" % (stamp, direction, text)
        # Open, write, close on every line. This is slower than holding the file
        # open, and that is the point. If the program is killed partway through a
        # bad exchange, the log still has everything up to that moment.
        with self.path_for(when).open("a", encoding="utf-8") as f:
            f.write(line)

    def sent(self, data, when=None):
        """Record bytes we put on the wire."""
        self._write("TX", "%-40s | %s" % (_readable(data), _hex_of(data)), when)

    def received(self, data, when=None):
        """Record bytes that came back. Empty means the device stayed silent."""
        if not data:
            self._write("RX", "(silence, nothing arrived before the timeout)", when)
        else:
            self._write("RX", "%-40s | %s" % (_readable(data), _hex_of(data)), when)

    def note(self, message, when=None):
        """Record something that is not traffic, like a retry or a refusal."""
        self._write("NOTE", message, when)
