"""Step 4: build the count and downtime rankings.

This is the heart of the tool. It turns rows of alarms into ranked tables.

Three downtime numbers are produced. They answer three different questions and
must never be mixed.

1. Attributed downtime. Each alarm is credited its own full duration. If ten
   alarms each lasted four hours, the attributed total is forty hours. This is
   good for ranking which fault costs the most. It sums to more than wall clock.

2. True wall-clock downtime. Overlapping alarms are merged first, then summed.
   If two alarms overlap, the shared time is counted once. This answers how much
   time the tool was actually down.

3. In-range downtime. Wall-clock downtime, but every alarm is first cut down to
   the parts that fall inside the reporting range, and alarms are gathered by
   where their downtime lands rather than by when they started. This answers
   how much of the reported time the tool spent down.

Numbers 2 and 3 are the same thing when the report covers a plain window and no
alarm runs off the end of it. They come apart as soon as a shift is chosen. An
alarm that starts at 17:50 and runs four hours contributes all four hours to
number 2 for the day shift, because that is when it started, and contributes
nothing to the night shift. Number 3 splits it the way the clock does: ten
minutes of day shift, three hours fifty of night shift.

The two counting rules differ on purpose:

    number 2   which faults began in these hours, and how long they ran
    number 3   how much of these hours the tool was down

Because number 3 follows the clock and not the onset, it is built from every
alarm in the file, not only the rows that survived the window and shift
filters. An alarm that began before the window opened, or before the shift
started, still put the tool on the floor during the reported time, and number 3
counts that part of it. The clipping in reporting_range.py is what does the
filtering for this number, which is why it does not need the row filters.

The overlap merge is the main correctness risk in the whole tool, so it lives in
one small tested function, merged_seconds.
"""

import pandas as pd

from . import normalize as nz
from . import reporting_range as rr
from . import window as window_mod

# The three grouping levels we report on. The value is the internal column name.
GROUPING_LEVELS = ["fault_code", "description", "equipment"]

# Labels for the three downtime methods, used on sheets and slides.
METHOD_ATTRIBUTED = "attributed"
METHOD_WALLCLOCK = "wallclock"
METHOD_IN_RANGE = "in_range"

# Which column each method ranks on.
METHOD_COLUMNS = {
    METHOD_ATTRIBUTED: "attributed_s",
    METHOD_WALLCLOCK: "wallclock_s",
    METHOD_IN_RANGE: "in_range_s",
}

SECONDS_PER_HOUR = 3600.0


def merged_seconds(intervals):
    """Return total wall-clock seconds covered by a set of time intervals.

    intervals: a list of (start, end) pairs. start and end are timestamps.
    Overlapping intervals are merged so shared time is counted once.

    Example. Alarm A runs 10:00 to 14:00. Alarm B runs 12:00 to 15:00.
    Naive sum is 4h + 3h = 7h. The real down time is 10:00 to 15:00 = 5h.
    This function returns 5h worth of seconds.
    """
    # Drop anything with no real length. end must be after start.
    clean = [(s, e) for (s, e) in intervals if pd.notna(s) and pd.notna(e) and e > s]
    if not clean:
        return 0.0

    # Sort by start time. Merging only works on sorted intervals.
    clean.sort(key=lambda pair: pair[0])

    total = 0.0
    cur_start, cur_end = clean[0]
    for start, end in clean[1:]:
        if start <= cur_end:
            # This interval overlaps or touches the current block. Extend the
            # block if this one reaches further.
            if end > cur_end:
                cur_end = end
        else:
            # A gap. Close the current block and start a new one.
            total += (cur_end - cur_start).total_seconds()
            cur_start, cur_end = start, end

    # Add the final open block.
    total += (cur_end - cur_start).total_seconds()
    return total


def build_occurrences(table, mode, vendor_config):
    """Turn the windowed table into one row per alarm occurrence.

    Every occurrence gets a start time, an end time, and a duration in seconds.
    The grouping columns (fault_code, description, equipment) come along too.

    Returns a DataFrame with columns:
        fault_code, description, equipment, ts_set, ts_end, duration_s
    """
    if mode == nz.MODE_DURATION:
        return _occurrences_from_duration(table)
    if mode == nz.MODE_PAIRED_INTERVAL:
        return _occurrences_from_interval(table)
    if mode == nz.MODE_EVENT_PAIRING:
        return _occurrences_from_events(table, vendor_config)
    raise ValueError("Unknown downtime mode: %s" % mode)


def _occurrences_from_duration(table):
    """Duration mode. Each row is already one occurrence with a duration."""
    out = table[["fault_code", "description", "equipment", "ts_set", "duration_s"]].copy()
    # The end time is the start plus the duration. pd.to_timedelta turns a
    # number of seconds into a length of time we can add to a timestamp.
    out["ts_end"] = out["ts_set"] + pd.to_timedelta(out["duration_s"], unit="s")
    return out[["fault_code", "description", "equipment", "ts_set", "ts_end", "duration_s"]]


def _occurrences_from_interval(table):
    """Paired-interval mode. Each row has both a set and a clear time."""
    out = table[["fault_code", "description", "equipment", "ts_set", "ts_clear"]].copy()
    out = out.rename(columns={"ts_clear": "ts_end"})

    # Duration is end minus start, in seconds. If the clear time is missing, the
    # duration is unknown. We set it to zero so it does not inflate any total.
    delta = out["ts_end"] - out["ts_set"]
    out["duration_s"] = delta.dt.total_seconds()
    out.loc[out["duration_s"].isna() | (out["duration_s"] < 0), "duration_s"] = 0.0
    return out[["fault_code", "description", "equipment", "ts_set", "ts_end", "duration_s"]]


def _occurrences_from_events(table, vendor_config):
    """Event-pairing mode. Set and clear are separate rows.

    We pair each clear with the most recent still-open set that shares the same
    pairing key. The default key is equipment plus fault code. This is the safe
    choice when several faults can be active on one tool at the same time.
    """
    pairing_keys = vendor_config.get("pairing_keys", ["equipment", "fault_code"])

    # open_sets maps a key tuple to a list of open set rows. The list works like
    # a stack. The last item pushed is the first one matched by a clear.
    open_sets = {}
    occurrences = []

    for _, row in table.iterrows():
        key = tuple(row[k] for k in pairing_keys)
        if row["event_type"] == "set":
            open_sets.setdefault(key, []).append(row)
        elif row["event_type"] == "clear":
            stack = open_sets.get(key, [])
            if stack:
                set_row = stack.pop()
                occurrences.append(_make_occurrence(set_row, row["ts_set"]))
            # A clear with no open set is an orphan. We skip it on purpose.
        # Rows marked "unknown" are ignored.

    # Any sets still open never got a clear. We keep them as occurrences with
    # zero duration so they still count toward the occurrence ranking.
    for stack in open_sets.values():
        for set_row in stack:
            occurrences.append(_make_occurrence(set_row, pd.NaT))

    if not occurrences:
        # Return an empty frame with the right columns so later code still works.
        return pd.DataFrame(
            columns=["fault_code", "description", "equipment", "ts_set", "ts_end", "duration_s"]
        )

    out = pd.DataFrame(occurrences)
    return out.sort_values("ts_set", kind="stable").reset_index(drop=True)


def _make_occurrence(set_row, clear_time):
    """Build one occurrence record from a set row and its clear time."""
    if pd.notna(clear_time) and clear_time > set_row["ts_set"]:
        duration = (clear_time - set_row["ts_set"]).total_seconds()
        end = clear_time
    else:
        # No valid clear time. Unknown duration, so credit zero.
        duration = 0.0
        end = set_row["ts_set"]
    return {
        "fault_code": set_row["fault_code"],
        "description": set_row["description"],
        "equipment": set_row["equipment"],
        "ts_set": set_row["ts_set"],
        "ts_end": end,
        "duration_s": duration,
    }


def _rank_table(occ, level, downtime_method, top_n, in_range_by_group=None):
    """Build one ranked table for a single grouping level.

    occ: the occurrences that passed the window and shift filters. These decide
        which groups appear and supply the count and attributed numbers.
    in_range_by_group: in-range seconds per group, computed elsewhere from every
        alarm in the file rather than from occ. See the module docstring for why
        the two use different row sets. None means no in-range number, which
        leaves the column at zero.

    Returns a dict with two DataFrames:
        by_count    sorted by occurrence count, high to low
        by_downtime sorted by the chosen downtime metric, high to low

    Both tables collapse everything past the top_n rows into one "Other" row.
    """
    # Count occurrences per group. size counts rows in each group.
    counts = occ.groupby(level, dropna=False).size().rename("count")

    # Attributed downtime per group. This is a plain sum of durations.
    attributed = occ.groupby(level, dropna=False)["duration_s"].sum().rename("attributed_s")

    # Wall-clock downtime per group. For each group we merge its own intervals.
    wall = {}
    for group_value, part in occ.groupby(level, dropna=False):
        pairs = list(zip(part["ts_set"], part["ts_end"]))
        wall[group_value] = merged_seconds(pairs)
    wallclock = pd.Series(wall, name="wallclock_s")

    # Put the measures side by side, one row per group. rename_axis forces
    # the group column to be named after the level, no matter how pandas labels
    # the index after the join.
    merged = pd.concat([counts, attributed, wallclock], axis=1)
    merged = merged.rename_axis(level).reset_index()
    merged[level] = merged[level].astype(str)

    # In-range downtime per group, looked up by group name. Groups with no
    # in-range time, and every group when no range was supplied, get zero.
    lookup = in_range_by_group or {}
    merged["in_range_s"] = merged[level].map(lambda name: float(lookup.get(name, 0.0)))

    # Add hour versions for easy reading. Seconds stay as the exact value.
    merged["attributed_hours"] = merged["attributed_s"] / SECONDS_PER_HOUR
    merged["wallclock_hours"] = merged["wallclock_s"] / SECONDS_PER_HOUR
    merged["in_range_hours"] = merged["in_range_s"] / SECONDS_PER_HOUR

    by_count = _sorted_with_other(merged, level, "count", top_n, pct_from="count")

    metric_col = METHOD_COLUMNS[downtime_method]
    by_downtime = _sorted_with_other(merged, level, metric_col, top_n, pct_from="downtime")

    return {"by_count": by_count, "by_downtime": by_downtime}


def _sorted_with_other(merged, level, sort_col, top_n, pct_from):
    """Sort a table, keep the top rows, and bucket the rest into 'Other'."""
    ordered = merged.sort_values(sort_col, ascending=False, kind="stable").reset_index(drop=True)

    if len(ordered) > top_n:
        head = ordered.iloc[:top_n].copy()
        tail = ordered.iloc[top_n:]
        # Build a single Other row by summing the tail. The two merged measures,
        # wall-clock and in-range, are summed too. That slightly overstates them
        # if tail groups overlapped each other, but it keeps the tail readable.
        # The headline numbers are computed from the raw intervals and never go
        # near this bucket, so the numbers that matter are safe.
        other = {
            level: "Other",
            "count": int(tail["count"].sum()),
            "attributed_s": float(tail["attributed_s"].sum()),
            "wallclock_s": float(tail["wallclock_s"].sum()),
            "in_range_s": float(tail["in_range_s"].sum()),
            "attributed_hours": float(tail["attributed_hours"].sum()),
            "wallclock_hours": float(tail["wallclock_hours"].sum()),
            "in_range_hours": float(tail["in_range_hours"].sum()),
        }
        result = pd.concat([head, pd.DataFrame([other])], ignore_index=True)
    else:
        result = ordered.copy()

    # Now add percent and cumulative percent columns based on the sort measure.
    if pct_from == "count":
        _add_percent(result, "count", "count_pct", "cum_count_pct")
    else:
        _add_percent(result, sort_col, "downtime_pct", "cum_downtime_pct")

    # Add a 1-based rank column at the front.
    result.insert(0, "rank", range(1, len(result) + 1))
    return result


def _add_percent(df, value_col, pct_col, cum_col):
    """Add a percent-of-total column and a running cumulative percent column."""
    total = df[value_col].sum()
    if total <= 0:
        df[pct_col] = 0.0
        df[cum_col] = 0.0
        return
    df[pct_col] = df[value_col] / total * 100.0
    # cumsum adds up the values from top to bottom as it goes down the rows.
    df[cum_col] = df[pct_col].cumsum()


def aggregate(windowed_table, mode, vendor_config, window_start, window_end,
              window_days=30, top_n=15, downtime_method=METHOD_ATTRIBUTED,
              tod_start=None, tod_end=None, full_table=None):
    """Run the full aggregation and return every table plus the headline numbers.

    windowed_table: the rows that passed the window and shift filters. These
        drive the counts, the attributed downtime, and the wall-clock downtime.
    tod_start, tod_end: the time-of-day bounds in minutes since midnight, or
        None when no shift was chosen. Carried through so the workbook and the
        deck can say which hours the report covers, and used to build the
        reporting range.
    full_table: every row in the file, before the window and shift filters, used
        for the in-range downtime number. That number follows the clock rather
        than the onset, so an alarm that started before the window or before the
        shift still counts for the part that landed inside the report. Pass None
        to fall back to windowed_table, which makes the number a little low
        wherever an alarm straddled the start of the range.

    Returns a dictionary. See the module and README for the shape.
    """
    if downtime_method not in METHOD_COLUMNS:
        raise ValueError(
            "downtime_method must be one of: %s." % ", ".join(sorted(METHOD_COLUMNS))
        )

    occ = build_occurrences(windowed_table, mode, vendor_config)

    # Headline numbers for the summary slide.
    total_faults = int(len(occ))
    total_attributed_s = float(occ["duration_s"].sum()) if total_faults else 0.0
    # Grand wall-clock merges every interval across the whole tool. This is the
    # true "how long was the tool down" number.
    all_pairs = list(zip(occ["ts_set"], occ["ts_end"])) if total_faults else []
    total_wallclock_s = merged_seconds(all_pairs)

    # The third number. Build the blocks of clock time the report covers, then
    # cut every alarm in the file down to the parts that land inside them.
    ranges = rr.build_ranges(window_start, window_end, tod_start, tod_end)
    range_seconds = rr.total_seconds(ranges)
    clock_occ = occ if full_table is None else build_occurrences(full_table, mode, vendor_config)
    total_in_range_s, in_range_by_group = _in_range_totals(clock_occ, ranges)

    levels = {}
    for level in GROUPING_LEVELS:
        if total_faults:
            levels[level] = _rank_table(occ, level, downtime_method, top_n,
                                        in_range_by_group.get(level))
        else:
            empty = pd.DataFrame()
            levels[level] = {"by_count": empty, "by_downtime": empty}

    # Top three offenders by the chosen downtime method, at the fault-code level.
    top_offenders = _top_three(levels["fault_code"]["by_downtime"], "fault_code")

    return {
        "occurrences": occ,
        "reporting_ranges": ranges,
        "grand": {
            "total_faults": total_faults,
            "attributed_downtime_s": total_attributed_s,
            "attributed_downtime_hours": total_attributed_s / SECONDS_PER_HOUR,
            "wallclock_downtime_s": total_wallclock_s,
            "wallclock_downtime_hours": total_wallclock_s / SECONDS_PER_HOUR,
            "in_range_downtime_s": total_in_range_s,
            "in_range_downtime_hours": total_in_range_s / SECONDS_PER_HOUR,
            # How much clock time the report covers, and what share of it the
            # tool spent down. The share is the number people actually quote.
            "range_seconds": range_seconds,
            "range_hours": range_seconds / SECONDS_PER_HOUR,
            "range_blocks": len(ranges),
            "range_description": rr.describe(ranges),
            "in_range_downtime_pct": (
                total_in_range_s / range_seconds * 100.0 if range_seconds > 0 else 0.0
            ),
            "window_start": window_start,
            "window_end": window_end,
            "window_days": window_days,
            "tod_start": tod_start,
            "tod_end": tod_end,
            "time_of_day_label": window_mod.time_of_day_label(tod_start, tod_end),
        },
        "levels": levels,
        "downtime_method": downtime_method,
        "top_n": top_n,
        "top_offenders": top_offenders,
    }


def _in_range_totals(occ, ranges):
    """In-range downtime overall and per group.

    occ: occurrences to measure. Normally every occurrence in the file, because
        this number follows the clock rather than the onset.
    ranges: the reporting range from reporting_range.build_ranges.

    Returns (total_seconds, {level: {group_name: seconds}}).

    Each group is clipped and merged on its own, so a group's number is the
    clock time during which at least one alarm of that group was active inside
    the range. Group numbers therefore do not add up to the total whenever two
    different groups were down at the same moment, exactly as with wall-clock.
    """
    empty_by_level = {level: {} for level in GROUPING_LEVELS}
    if not ranges or occ.empty:
        return 0.0, empty_by_level

    pairs = list(zip(occ["ts_set"], occ["ts_end"]))
    total = merged_seconds(rr.clip_intervals(pairs, ranges))

    by_level = {}
    for level in GROUPING_LEVELS:
        per_group = {}
        for group_value, part in occ.groupby(level, dropna=False):
            group_pairs = list(zip(part["ts_set"], part["ts_end"]))
            seconds = merged_seconds(rr.clip_intervals(group_pairs, ranges))
            if seconds:
                # str because the ranked tables cast their group column to text.
                per_group[str(group_value)] = seconds
        by_level[level] = per_group

    return total, by_level


def _top_three(by_downtime_table, level):
    """Pull the top three rows, skipping the 'Other' bucket if present."""
    if by_downtime_table.empty:
        return []
    real = by_downtime_table[by_downtime_table[level] != "Other"]
    picks = []
    for _, row in real.head(3).iterrows():
        picks.append(
            {
                "name": row[level],
                "count": int(row["count"]),
                "attributed_hours": float(row["attributed_hours"]),
                "wallclock_hours": float(row["wallclock_hours"]),
                "in_range_hours": float(row["in_range_hours"]),
            }
        )
    return picks
