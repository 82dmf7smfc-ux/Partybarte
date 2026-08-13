"""Step 3: keep only the trailing time window.

The report covers the last N days of alarms. The end of that window is the
latest timestamp in the file, not today's date. This matters. If a log was
pulled last month, we still want the last 30 days of that log, not an empty
result because today is later.
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
