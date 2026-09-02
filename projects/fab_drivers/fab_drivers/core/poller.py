"""Read a set of values on a gentle repeating loop.

Why this exists
---------------
Polling a tool harder does not get you better data. It gets you a busier device
and a bigger chance of colliding with the tool's own software. These are trend
tools. A reading every ten or thirty seconds is plenty to watch a cold head cool
down or a foreline creep up over a shift.

This keeps the last good value for every reading, along with when it was taken.
If a reading fails, the old value stays visible but is marked stale, with its
age. That is more useful than a blank, because a number from forty seconds ago
still tells you roughly where you are, as long as the screen is honest about it.
"""

import time

# The floor on how often a sweep may run. The library standard is a full sweep no
# more often than every ten seconds. A driver may ask for slower. It may not ask
# for faster without changing this on purpose, in a change someone reviews.
MINIMUM_INTERVAL_S = 10.0


class Reading:
    """One value, and how much you should trust it.

    value:  the last value read, or None if it has never been read.
    at:     the time.time() when that value was read, or None.
    stale:  True if the most recent attempt failed. The value is then the last
            good one, which may be old.
    error:  a short description of the last failure, or None.
    """

    def __init__(self, name):
        self.name = name
        self.value = None
        self.at = None
        self.stale = True
        self.error = "never read"

    def record(self, value, when=None):
        self.value = value
        self.at = when if when is not None else time.time()
        self.stale = False
        self.error = None

    def mark_stale(self, error):
        self.stale = True
        self.error = error
        # The value and its timestamp are left alone on purpose. The point of a
        # stale reading is that you can still see the last good number and work
        # out how old it is.

    def age_s(self, now=None):
        """How many seconds ago the value was read, or None if never."""
        if self.at is None:
            return None
        now = now if now is not None else time.time()
        return now - self.at

    def __repr__(self):
        state = "stale" if self.stale else "fresh"
        return "<Reading %s=%r %s>" % (self.name, self.value, state)


class Poller:
    """Sweep a set of named readings on a timer.

    sources: a dictionary of name to a function that takes no arguments and
             returns a value. A function that raises, or returns None, marks
             that reading stale. Device.try_query fits this shape directly.
    interval_s: seconds between sweeps. Raised to MINIMUM_INTERVAL_S if lower.
    history: an optional HistoryWriter. If given, each sweep appends one row.
    """

    def __init__(self, sources, interval_s=30.0, history=None):
        if not sources:
            raise ValueError("a poller needs at least one reading to take")
        self.sources = dict(sources)
        self.interval_s = max(float(interval_s), MINIMUM_INTERVAL_S)
        self.history = history
        self.readings = {name: Reading(name) for name in self.sources}

    def sweep(self):
        """Read everything once. Returns the readings dictionary.

        One failing reading never stops the others. That matters when four pumps
        share a terminal and one of them is powered down.
        """
        for name, read in self.sources.items():
            reading = self.readings[name]
            try:
                value = read()
            except Exception as problem:
                # A driver should not raise here, because try_query swallows the
                # normal failures. If something else does, one bad reading still
                # must not take the whole sweep down.
                reading.mark_stale("%s: %s" % (type(problem).__name__, problem))
                continue

            if value is None:
                reading.mark_stale("no reply")
            else:
                reading.record(value)

        if self.history is not None:
            # A stale reading writes an empty cell, not the old value. The trend
            # file must only ever hold numbers that were really measured at the
            # time on the row.
            row = {name: (None if r.stale else r.value)
                   for name, r in self.readings.items()}
            self.history.append(row)

        return self.readings

    def run_forever(self, sweeps=None, sleep=time.sleep):
        """Sweep, wait, repeat.

        sweeps: stop after this many sweeps. None means run until interrupted.
                The tests pass a small number here. Real use leaves it None.
        sleep:  the function used to wait. The tests pass a fake one so they do
                not actually sit there for thirty seconds.
        """
        done = 0
        while sweeps is None or done < sweeps:
            self.sweep()
            done += 1
            if sweeps is None or done < sweeps:
                sleep(self.interval_s)
        return self.readings
