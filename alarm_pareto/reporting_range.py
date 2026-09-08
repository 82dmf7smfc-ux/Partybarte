"""The reporting range: the stretches of clock time a report actually covers.

The other two downtime numbers ask about faults. This module exists to support
the third one, which asks about the clock.

Once a report is narrowed to the last thirty days and to the night shift, the
time it covers is no longer one unbroken block. It is thirty separate blocks,
one per night, each running 18:00 on one day to 06:00 on the next:

    window_start                                            window_end
        |                                                        |
        |  [night 1]      [night 2]      [night 3]   ...          |
        |  18:00-06:00    18:00-06:00    18:00-06:00              |
        +--------------------------------------------------------+

That list of blocks is the reporting range. Clipping an alarm against it is
what turns "this alarm ran four hours" into "this alarm was down for two hours
of night shift", which is the question the third downtime number answers.

With no time-of-day filter the reporting range is simply the whole window, one
block, and clipping only trims alarms that ran off the end of the window.

Two properties are worth stating because the rest of the tool relies on them.
The blocks are returned sorted and never overlap each other, so their lengths
can simply be added up. And the blocks are built from the window and the shift
alone, never from the alarms, so the range is the same no matter what the data
does.
"""

import bisect

import pandas as pd

from . import window as window_mod


def build_ranges(window_start, window_end, tod_start=None, tod_end=None):
    """Return the stretches of time the report covers, as (start, end) pairs.

    window_start, window_end: the ends of the trailing window.
    tod_start, tod_end: the time-of-day bounds in minutes since midnight, or
        None for no time-of-day filter.

    With no time-of-day filter this is one block, the window itself. With one,
    it is a block per day, each clipped to the window so the first and last
    blocks do not stick out past the ends of the report.

    Blocks come back sorted by start time and never overlap.
    """
    if window_end < window_start:
        raise ValueError("The window ends before it starts.")

    if not window_mod.is_time_of_day_filtered(tod_start, tod_end):
        # No shift chosen, so the range is the whole window in one piece.
        return [(window_start, window_end)] if window_end > window_start else []

    start_offset = pd.Timedelta(minutes=tod_start)
    end_offset = pd.Timedelta(minutes=tod_end)
    # A shift whose start is later than its end runs into the next day, so its
    # end offset is measured from the following midnight.
    if tod_start > tod_end:
        end_offset += pd.Timedelta(days=1)

    # Start a day early. A night shift that began before the window opened can
    # still have part of itself inside the window, and that part counts.
    first_midnight = window_start.normalize() - pd.Timedelta(days=1)
    last_midnight = window_end.normalize()

    ranges = []
    midnight = first_midnight
    while midnight <= last_midnight:
        block_start = midnight + start_offset
        block_end = midnight + end_offset

        # Trim the block to the window. A block wholly outside it disappears.
        clipped_start = max(block_start, window_start)
        clipped_end = min(block_end, window_end)
        if clipped_end > clipped_start:
            ranges.append((clipped_start, clipped_end))

        midnight += pd.Timedelta(days=1)

    return ranges


def total_seconds(ranges):
    """How many seconds of clock time the reporting range covers.

    The blocks never overlap, so this is a plain sum. This is the denominator
    for "the tool was down for X percent of night shift".
    """
    return float(sum((end - start).total_seconds() for start, end in ranges))


def clip_intervals(intervals, ranges):
    """Cut a list of alarm intervals down to the parts inside the range.

    intervals: (start, end) pairs, one per alarm occurrence.
    ranges: the reporting range from build_ranges.

    One alarm can produce several clipped pieces. A fault that runs from 05:00
    Monday to 20:00 Monday, against a night shift, leaves two pieces: 05:00 to
    06:00, and 18:00 to 20:00. Both are returned. An alarm that falls entirely
    outside the range produces nothing.

    Pieces come back in no particular order. Every caller either sums them or
    passes them to merged_seconds, which sorts for itself.
    """
    if not ranges:
        return []

    # The blocks are sorted and disjoint, so a binary search finds the first one
    # that could possibly overlap a given alarm. Without this, a year of night
    # shifts against a million alarms would be hundreds of millions of pointless
    # comparisons.
    range_starts = [start for start, _ in ranges]

    pieces = []
    for alarm_start, alarm_end in intervals:
        if pd.isna(alarm_start) or pd.isna(alarm_end) or alarm_end <= alarm_start:
            # No length, or no usable end time. Nothing to clip.
            continue

        # Find the last block that starts at or before this alarm ends, then
        # walk backwards and forwards from there over the blocks that touch it.
        # bisect_right gives the first block starting after the alarm ends, so
        # every block from there on is too late to matter.
        stop = bisect.bisect_right(range_starts, alarm_end)
        index = stop - 1
        while index >= 0:
            block_start, block_end = ranges[index]
            if block_end <= alarm_start:
                # This block finishes before the alarm begins. Because the
                # blocks are sorted, every earlier one does too.
                break
            piece_start = max(alarm_start, block_start)
            piece_end = min(alarm_end, block_end)
            if piece_end > piece_start:
                pieces.append((piece_start, piece_end))
            index -= 1

    return pieces


def describe(ranges):
    """A short human sentence about the range, for sheets and slides."""
    if not ranges:
        return "No time covered"
    hours = total_seconds(ranges) / 3600.0
    if len(ranges) == 1:
        return "%.1f hours of clock time, in one continuous block" % hours
    return "%.1f hours of clock time, in %d blocks" % (hours, len(ranges))
