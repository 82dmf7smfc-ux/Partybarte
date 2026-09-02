"""Step 3: keep only the trailing time window.

The report covers the last N days of alarms. The end of that window is the
latest timestamp in the file, not today's date. This matters. If a log was
pulled last month, we still want the last 30 days of that log, not an empty
result because today is later.

This module also holds the time-of-day filter. The trailing window picks the
days; the time-of-day filter narrows those days to a range of clock hours, so a
report can cover one shift.
"""

import pandas as pd


def latest_timestamp(table):
    """Return the newest onset time in the table."""
    return table["ts_set"].max()


def apply_window(table, window_days=30):
    """Keep rows whose onset time falls in the trailing window.

    table: the normalized table.
    window_days: how many days back to keep. Default is 30.

    Returns a tuple (filtered_table, window_start, window_end).
    The window is [window_end - window_days, window_end], end inclusive.
    """
    if window_days <= 0:
        raise ValueError("window_days must be a positive number. Got %s." % window_days)

    window_end = latest_timestamp(table)
    if pd.isna(window_end):
        raise ValueError("No valid timestamps in the data, so no window can be built.")

    # pd.Timedelta is a length of time. Subtracting it from a datetime moves
    # backward by that much. This is how we get the start of the window.
    window_start = window_end - pd.Timedelta(days=window_days)

    # Keep rows where the onset time is inside the window. The '&' means "and".
    # Each comparison must be wrapped in parentheses in pandas.
    keep = (table["ts_set"] >= window_start) & (table["ts_set"] <= window_end)
    filtered = table[keep].reset_index(drop=True)

    return filtered, window_start, window_end


# ---------------------------------------------------------------------------
# Time-of-day filter.
#
# The trailing window above answers "which days". This part answers "which
# hours of those days". It exists so a report can cover one shift.
#
# The hard part is the night shift, so it is worth being precise about it.
#
# A night shift runs 18:00 on one day to 06:00 on the next day. Written as a
# pair of clock times, the start (18:00) is LATER than the end (06:00). That is
# not a mistake and it is not an error to reject. It is how a shift that spans
# midnight looks when you strip the dates off it. The filter treats a start
# later than an end as "wrap past midnight" and keeps two pieces of the clock:
# the evening tail from the start up to midnight, and the morning head from
# midnight up to the end.
#
#   00:00      06:00                        18:00      24:00
#     |----------|----------------------------|----------|
#      <-- keep -->                            <-- keep -->
#      morning head                            evening tail
#
# Because every row is judged on its own clock time, the filter does not need
# to know or care which calendar date a shift began on. Rows from 2026-02-20
# 22:00 and 2026-02-21 03:00 are both night-shift rows and both survive, even
# though they fall on different dates. Over a thirty day window this selects
# every night-shift row from all thirty nights, which is what a shift Pareto
# needs: rank the faults that happen on nights, across the whole window.
#
# What it deliberately does NOT do is group the rows by which individual night
# they belonged to. "Rank faults on night shift" is answered. "Which single
# night was worst" is a different question and would need a shift-date column.
# ---------------------------------------------------------------------------

# Minutes in a full day. A time of "24:00" parses to this and means "end of
# day". Keeping it separate from 0 is what lets "06:00 to 24:00" work.
MINUTES_PER_DAY = 24 * 60


def parse_time_of_day(text):
    """Turn a clock time into minutes since midnight.

    Accepts "HH:MM", "HH:MM:SS", or a bare hour like "6" or "06". The value
    "24:00" is allowed and means the end of the day.

    Returns an integer from 0 to 1440.
    """
    if text is None:
        return None
    raw = str(text).strip()
    if not raw:
        return None

    parts = raw.split(":")
    if len(parts) > 3:
        raise ValueError("Time of day must look like HH:MM. Got %r." % text)

    try:
        numbers = [int(p) for p in parts]
    except ValueError:
        raise ValueError("Time of day must look like HH:MM. Got %r." % text)

    hour = numbers[0]
    minute = numbers[1] if len(numbers) > 1 else 0
    second = numbers[2] if len(numbers) > 2 else 0

    if not 0 <= minute < 60 or not 0 <= second < 60:
        raise ValueError("Minutes and seconds must be 0 to 59. Got %r." % text)
    if hour == 24 and (minute or second):
        raise ValueError("24:00 is the latest time allowed. Got %r." % text)
    if not 0 <= hour <= 24:
        raise ValueError("Hours must be 0 to 24. Got %r." % text)

    # Seconds are rounded down. The filter works at minute resolution because
    # shift boundaries are always whole minutes.
    return hour * 60 + minute


def format_time_of_day(minutes):
    """Turn minutes since midnight back into an "HH:MM" string."""
    if minutes is None:
        return None
    return "%02d:%02d" % (minutes // 60, minutes % 60)


def time_of_day_label(start_minutes, end_minutes):
    """A short human label for the time-of-day range, for sheets and slides."""
    if not is_time_of_day_filtered(start_minutes, end_minutes):
        return "All hours"
    label = "%s to %s" % (format_time_of_day(start_minutes),
                          format_time_of_day(end_minutes))
    if start_minutes > end_minutes:
        label += " (crosses midnight)"
    return label


def is_time_of_day_filtered(start_minutes, end_minutes):
    """True when the range actually removes part of the day.

    Either bound missing means no filter. Equal bounds mean the whole day, so
    "06:00 to 06:00" is a full 24 hours rather than nothing. Reading equal
    bounds as an empty range would be the other choice, but an empty range is
    never what anyone wants from a report, and "00:00 to 00:00" plainly reads
    as a whole day.

    Note that a start later than an end is NOT caught here. That is the night
    shift, and it is a real filter that apply_time_of_day handles by wrapping.
    """
    if start_minutes is None or end_minutes is None:
        return False
    if start_minutes == end_minutes:
        return False
    if start_minutes == 0 and end_minutes == MINUTES_PER_DAY:
        return False
    return True


def apply_time_of_day(table, start_minutes, end_minutes):
    """Keep rows whose onset time falls inside the given hours of the day.

    table: the table, already trimmed to the trailing window.
    start_minutes, end_minutes: minutes since midnight, from parse_time_of_day.

    Three rules govern this function.

    1. The range is half open. The start minute is kept, the end minute is not.
       So 06:00 to 18:00 keeps an alarm at exactly 06:00 and drops one at
       exactly 18:00. This is what makes a day shift and a night shift add up
       to a whole day with no row counted twice and no row lost.

    2. A start later than the end wraps past midnight. 18:00 to 06:00 is the
       night shift, running from 18:00 on one day to 06:00 on the next. Rows
       are matched on clock time alone, so rows from two different calendar
       dates land in the same night shift, and every night in the window is
       included. See the block comment above for the full picture.

    3. Rows are chosen on their onset time only, exactly the rule the trailing
       window already uses. An alarm that starts inside the range keeps its
       whole duration even if it ran on past the end of the range. So the
       downtime number means "downtime from faults that began in these hours",
       not "clock time the tool spent down during these hours". Clipping
       durations at the shift boundary would be a third downtime number, and
       this tool keeps exactly two on purpose.

    Returns the filtered table, re-indexed from zero. The table passed in is
    not modified.
    """
    if not is_time_of_day_filtered(start_minutes, end_minutes):
        return table.reset_index(drop=True)

    # .dt reaches into the datetime parts of a whole column at once, so this
    # gives one minutes-since-midnight number per row. Seconds are ignored,
    # which rounds each row down to its minute. A row at 05:59:59 is minute
    # 359, safely inside a range that ends at 06:00.
    minutes = table["ts_set"].dt.hour * 60 + table["ts_set"].dt.minute

    if start_minutes < end_minutes:
        # The plain case. One unbroken stretch of clock, inside a single day.
        # Day shift, 06:00 to 18:00, is minutes 360 through 1079.
        keep = (minutes >= start_minutes) & (minutes < end_minutes)
    else:
        # The wrapping case, which is the night shift. The kept clock time is
        # in two pieces, so this is an "or", not an "and". Night shift, 18:00
        # to 06:00, is minutes 1080 through 1439 (the evening tail, before
        # midnight) plus minutes 0 through 359 (the morning head, after
        # midnight). An "and" here would keep nothing at all, because no single
        # minute can be both at or after 18:00 and before 06:00.
        keep = (minutes >= start_minutes) | (minutes < end_minutes)

    # keep is a column of True and False, one per row. Indexing the table with
    # it returns only the True rows. reset_index renumbers them from zero so
    # the caller gets a clean table rather than one with gaps in its numbering.
    return table[keep].reset_index(drop=True)
