"""Step 2: map vendor column names to standard internal names.

Every vendor names their columns differently. The rest of the tool should not
care about that. So this module renames the vendor columns to a fixed set of
internal names. After this step, every other module sees the same names no
matter which vendor produced the log.

Internal names used everywhere else:
    ts_set      alarm onset timestamp
    ts_clear    alarm clear timestamp (only in paired-interval logs)
    event_type  "set" or "clear" marker (only in event-pairing logs)
    fault_code  vendor fault or alarm code
    description human readable fault text
    equipment   equipment or module identifier
    duration_s  downtime in seconds

This module also figures out the "downtime mode". A log can express downtime in
three different shapes. We detect which one from the columns the config lists.
"""

import numpy as np
import pandas as pd

# The three ways a log can express downtime. Other modules read this to decide
# how to compute downtime.
MODE_DURATION = "duration"          # a duration column already exists
MODE_PAIRED_INTERVAL = "interval"   # each row has both a set and a clear time
MODE_EVENT_PAIRING = "event"        # set and clear are separate rows

# Columns that must be present after normalizing, in every mode.
REQUIRED_ALWAYS = ["ts_set", "fault_code", "description", "equipment"]


def detect_mode(vendor_config):
    """Decide which downtime shape this vendor log uses.

    The decision is based only on which internal names the config maps. This
    keeps the rule simple and predictable.
    """
    mapped = vendor_config.get("columns", {})

    if "duration_s" in mapped:
        return MODE_DURATION
    if "ts_set" in mapped and "ts_clear" in mapped:
        return MODE_PAIRED_INTERVAL
    if "event_type" in mapped:
        return MODE_EVENT_PAIRING

    raise ValueError(
        "Cannot tell how downtime is stored. The config must map one of: "
        "'duration_s', or both 'ts_set' and 'ts_clear', or 'event_type'."
    )


def _seconds_scale(duration_unit):
    """Return how many seconds are in one unit of the duration column.

    We store everything in seconds internally. If the vendor logs minutes or
    hours, we scale to seconds here.
    """
    unit = (duration_unit or "seconds").lower()
    if unit in ("second", "seconds", "s", "sec"):
        return 1.0
    if unit in ("minute", "minutes", "m", "min"):
        return 60.0
    if unit in ("hour", "hours", "h", "hr"):
        return 3600.0
    raise ValueError("Unknown duration_unit '%s'. Use seconds, minutes, or hours." % duration_unit)


def normalize(raw, vendor_config):
    """Rename vendor columns and clean up types.

    raw: the table from parse.read_log.
    vendor_config: the vendor block.

    Returns a tuple (table, mode). The table uses internal names. The mode is
    one of the MODE_* values above.
    """
    mapped = vendor_config.get("columns", {})
    mode = detect_mode(vendor_config)

    # Build the reverse mapping: vendor header -> internal name. Then rename.
    # We only keep the columns the config actually maps. Everything else is
    # dropped, because the rest of the tool does not use it.
    rename_map = {}
    for internal_name, vendor_header in mapped.items():
        if vendor_header not in raw.columns:
            raise KeyError(
                "Config maps internal name '%s' to column '%s', but that column "
                "is not in the file. Columns found: %s"
                % (internal_name, vendor_header, ", ".join(raw.columns))
            )
        rename_map[vendor_header] = internal_name

    table = raw[list(rename_map.keys())].rename(columns=rename_map).copy()

    # Check the always-required columns are present.
    missing = [c for c in REQUIRED_ALWAYS if c not in table.columns]
    if missing:
        raise KeyError("These required internal columns are missing after mapping: %s" % ", ".join(missing))

    # Parse timestamps into real datetime values so we can sort and subtract.
    # pd.to_datetime turns text into datetime. A format string from the config
    # makes parsing exact and fast. If none is given, pandas infers the format.
    ts_format = vendor_config.get("timestamp_format")
    table["ts_set"] = _to_datetime(table["ts_set"], ts_format, "ts_set")
    if "ts_clear" in table.columns:
        table["ts_clear"] = _to_datetime(table["ts_clear"], ts_format, "ts_clear")

    # Convert the duration column to seconds as a number, if present.
    if mode == MODE_DURATION:
        scale = _seconds_scale(vendor_config.get("duration_unit", "seconds"))
        # pd.to_numeric turns text into numbers. errors="coerce" makes bad
        # values become "not a number" instead of crashing. We then treat those
        # as zero downtime, which is the safe choice.
        seconds = pd.to_numeric(table["duration_s"], errors="coerce") * scale
        table["duration_s"] = seconds.fillna(0.0).astype(float)

    # For event-pairing logs, normalize the event marker text to "set"/"clear".
    if mode == MODE_EVENT_PAIRING:
        table["event_type"] = _normalize_event_type(table["event_type"], vendor_config)

    # Sort by onset time. Later steps assume the table is time ordered.
    table = table.sort_values("ts_set", kind="stable").reset_index(drop=True)
    return table, mode


def _to_datetime(series, ts_format, column_label):
    """Convert a text column to datetime and fail loudly if nothing parses."""
    if ts_format:
        parsed = pd.to_datetime(series, format=ts_format, errors="coerce")
    else:
        # No format given. Let pandas infer it. This is slower but flexible.
        parsed = pd.to_datetime(series, errors="coerce")

    # If every value failed to parse, the config or file is wrong. Say so.
    if parsed.notna().sum() == 0:
        raise ValueError(
            "Could not parse any timestamps in column '%s'. Check the "
            "timestamp_format in the config." % column_label
        )
    return parsed


def _normalize_event_type(series, vendor_config):
    """Turn vendor set/clear labels into the plain words 'set' and 'clear'."""
    event_values = vendor_config.get("event_values", {})
    set_label = str(event_values.get("set", "SET"))
    clear_label = str(event_values.get("clear", "CLEAR"))

    # Compare in a case-insensitive way and trim spaces so small file
    # differences do not break the match.
    trimmed = series.astype(str).str.strip().str.upper()
    result = np.where(
        trimmed == set_label.upper(),
        "set",
        np.where(trimmed == clear_label.upper(), "clear", "unknown"),
    )
    return pd.Series(result, index=series.index)
