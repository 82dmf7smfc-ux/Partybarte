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
# hours of those days". It exists so a report can cover one shift. Night shift
# on a fab floor runs past midnight, so the range is allowed to wrap.
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
    "06:00 to 06:00" is a full 24 hours rather than nothing.
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

    The range is half open: the start minute is kept and the end minute is not.
    That is what makes two shifts add up to one day with nothing counted twice.
    A range where the start is later than the end wraps past midnight, so
    22:00 to 06:00 is the night shift.

    Rows are selected on their onset time only, the same rule the trailing
    window uses. An alarm that starts inside the range keeps its whole
    duration, even if it ran on past the end of the range. Downtime is
    therefore "downtime from faults that began in these hours", not "clock
    time spent down during these hours".

    Returns the filtered table.
    """
    if not is_time_of_day_filtered(start_minutes, end_minutes):
        return table.reset_index(drop=True)

    # .dt gets at the datetime parts of a whole column at once.
    minutes = table["ts_set"].dt.hour * 60 + table["ts_set"].dt.minute

    if start_minutes < end_minutes:
        keep = (minutes >= start_minutes) & (minutes < end_minutes)
    else:
        # Wraps past midnight. Keep the evening tail and the morning head.
        keep = (minutes >= start_minutes) | (minutes < end_minutes)

    return table[keep].reset_index(drop=True)
