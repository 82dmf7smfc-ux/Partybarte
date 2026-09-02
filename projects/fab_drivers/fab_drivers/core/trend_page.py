"""Build one self-contained trend page for one device.

Why this exists
---------------
Every driver gets its own trend page. Ten drivers each inventing a page would
produce ten pages that look different and behave differently, and nine of them
would be copied from whichever one was written first, mistakes included. So the
page is built here, once, and a driver only says what to plot.

The page is a single HTML file with everything inside it. The readings are
written into the file as data when it is built. Nothing is fetched when it is
opened. That matters twice over. These machines have no internet, and a browser
opening a file from disk refuses to load a second file next to it anyway, so a
page that tried to read the CSV at view time would simply show nothing.

One file also means you can email it, or drop it on a share, and it still works.

Gaps stay gaps. Where a reading failed, the CSV has an empty cell, and the line
on the chart breaks rather than joining across the hole. Drawing straight
through a gap would invent readings that were never taken, which is the same
mistake as writing the last value into the CSV, one layer further on.
"""

import csv
import datetime
import html
import math
from pathlib import Path

# The chart is drawn as an SVG with these proportions. The page scales it to
# whatever width the window has, so these are ratios more than pixels.
CHART_WIDTH = 900
CHART_HEIGHT = 220
MARGIN_LEFT = 64
MARGIN_RIGHT = 16
MARGIN_TOP = 12
MARGIN_BOTTOM = 28


def read_history(folder, name, days=7, today=None):
    """Read the last few daily CSV files for one device into rows.

    Returns a list of dictionaries, oldest first, one per row in the files. A
    missing day is simply not there. An empty cell stays an empty string, and
    is turned into a gap later.
    """
    folder = Path(folder)
    today = today or datetime.date.today()
    rows = []
    for step in range(days - 1, -1, -1):
        day = today - datetime.timedelta(days=step)
        path = folder / ("%s_%s.csv" % (name, day.strftime("%Y-%m-%d")))
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as f:
            rows.extend(list(csv.DictReader(f)))
    return rows


def _to_number(text):
    """Turn a cell into a number, or None if it is a gap or not a number."""
    if text is None:
        return None
    text = text.strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        # A column of text, like a status word, is not something to plot. The
        # summary table still shows it.
        return None


def _segments(points):
    """Split points into runs with no gap in them.

    points is a list of (x, value_or_None). Each run becomes its own line on the
    chart, so a gap leaves a break instead of a straight line across it.
    """
    runs = []
    current = []
    for x, value in points:
        if value is None:
            if current:
                runs.append(current)
                current = []
        else:
            current.append((x, value))
    if current:
        runs.append(current)
    return runs


LINEAR = "linear"
LOG = "log"

# The scales a column may be drawn on. A driver names one per column.
SCALES = (LINEAR, LOG)


def _positive_only(points):
    """Turn every value that a log axis cannot show into a gap.

    A log axis has no place to put zero or a negative number, because neither
    has a logarithm. This matters here rather than in theory: a pressure gauge
    that is switched off, or unplugged, may well report exactly zero.

    Returns the cleaned points and how many readings were dropped. The count is
    printed under the chart. A reading that quietly disappears is the thing this
    library is trying hardest not to do.
    """
    cleaned = []
    dropped = 0
    for x, value in points:
        if value is not None and value <= 0:
            cleaned.append((x, None))
            dropped += 1
        else:
            cleaned.append((x, value))
    return cleaned, dropped


def _decade_bounds(low, high):
    """The whole decades that just contain low and high.

    Snapping the axis to whole decades is what makes a log chart readable. Every
    gridline is then a power of ten, and the eye counts decades instead of
    reading numbers.
    """
    bottom = math.floor(math.log10(low))
    top = math.ceil(math.log10(high))
    if top == bottom:
        # A reading sitting exactly on a power of ten, or a flat line. Give it a
        # decade of room so it is not drawn along the edge of the chart.
        bottom, top = bottom - 1, top + 1
    return bottom, top


def _decade_label(exponent):
    """Label one gridline on a log axis, as 1E-06 rather than 0.000001."""
    return "1E%+03d" % exponent


def _chart_svg(series, scale=LINEAR):
    """Draw one chart, holding one line or two.

    series is a list of point lists. Each point list is a list of
    (index, value_or_None), already in time order. The first one is the main
    reading and the second, if there is one, is drawn over it on the same axes
    in another colour and dashed.

    Two lines on one chart is what makes a setpoint useful. A reading and the
    setpoint it is supposed to be holding, on separate charts with separate
    axes, cannot be compared by eye: each chart scales to its own values, so a
    flat setpoint and a drifting temperature both look like they fill the
    chart. On one pair of axes the gap between them is the whole point.

    scale is LINEAR or LOG, and applies to every line on the chart, because
    they share an axis. Pressure needs LOG, because it runs from atmosphere
    down to 1e-9 torr, and on a linear axis every reading below about 1 torr
    sits flat on the bottom of the chart. The pumpdown that matters is then
    invisible.
    """
    if scale not in SCALES:
        raise ValueError("a column is drawn on one of %s, not %r"
                         % (", ".join(SCALES), scale))

    dropped = 0
    if scale == LOG:
        cleaned = []
        for points in series:
            kept, lost = _positive_only(points)
            cleaned.append(kept)
            dropped += lost
        series = cleaned

    values = [v for points in series for _, v in points if v is not None]
    if not values:
        if dropped:
            return ('<p class="nodata">No readings in this window that a log '
                    'axis can show. %d were zero or negative.</p>' % dropped)
        return '<p class="nodata">No readings in this window.</p>'

    low, high = min(values), max(values)

    if scale == LOG:
        bottom, top = _decade_bounds(low, high)
        axis_low, axis_high = float(bottom), float(top)
    else:
        if low == high:
            # A flat line would otherwise divide by zero. Give it room above and
            # below so it sits in the middle of the chart rather than on an edge.
            low, high = low - 1.0, high + 1.0
        axis_low, axis_high = low, high

    plot_width = CHART_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
    plot_height = CHART_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM
    last_index = max(max(len(points) for points in series) - 1, 1)

    def place(value):
        """Where a value sits on the axis. 0 is the bottom, 1 is the top."""
        if scale == LOG:
            value = math.log10(value)
        return (value - axis_low) / (axis_high - axis_low)

    def sx(index):
        return MARGIN_LEFT + (index / last_index) * plot_width

    def sy(value):
        return MARGIN_TOP + (1.0 - place(value)) * plot_height

    parts = []

    if scale == LOG:
        # One gridline per decade. Nine decades of pressure would give nine
        # labels stacked on each other, so the labels are thinned out when there
        # are many. The line still goes at every decade.
        decades = list(range(int(axis_low), int(axis_high) + 1))
        step = 1 + len(decades) // 8
        for exponent in decades:
            y = sy(10.0 ** exponent)
            parts.append('<line class="grid" x1="%.1f" y1="%.1f" x2="%.1f" '
                         'y2="%.1f"/>'
                         % (MARGIN_LEFT, y, CHART_WIDTH - MARGIN_RIGHT, y))
            # Counted down from the top decade, so the labels come out evenly
            # spaced and the top of the axis always has one. Counting up from
            # the bottom instead leaves the top line bare, or puts two labels
            # next to each other at the top, which reads as a mistake.
            if (decades[-1] - exponent) % step == 0:
                parts.append('<text class="ylabel" x="%.1f" y="%.1f">%s</text>'
                             % (MARGIN_LEFT - 8, y + 4,
                                _decade_label(exponent)))
    else:
        # Three gridlines with their values, so the eye has something to
        # measure by.
        for share in (0.0, 0.5, 1.0):
            value = axis_low + share * (axis_high - axis_low)
            y = sy(value)
            parts.append('<line class="grid" x1="%.1f" y1="%.1f" x2="%.1f" '
                         'y2="%.1f"/>'
                         % (MARGIN_LEFT, y, CHART_WIDTH - MARGIN_RIGHT, y))
            parts.append('<text class="ylabel" x="%.1f" y="%.1f">%s</text>'
                         % (MARGIN_LEFT - 8, y + 4, _tidy_number(value)))

    for order, points in enumerate(series):
        # The first line is plain, and every one after it is dashed and in the
        # second colour. Only two are expected. More than two on one axis stops
        # being readable, which is why nothing offers it.
        extra = "" if order == 0 else " alt"
        for run in _segments(points):
            if len(run) == 1:
                # A lone reading between two gaps would be an invisible line,
                # so show it as a dot instead.
                x, value = run[0]
                parts.append('<circle class="point%s" cx="%.1f" cy="%.1f" '
                             'r="2.5"/>' % (extra, sx(x), sy(value)))
                continue
            coords = " ".join("%.1f,%.1f" % (sx(x), sy(v)) for x, v in run)
            parts.append('<polyline class="line%s" points="%s"/>'
                         % (extra, coords))

    return ('<svg class="chart" viewBox="0 0 %d %d" preserveAspectRatio="none" '
            'role="img">%s</svg>' % (CHART_WIDTH, CHART_HEIGHT, "".join(parts)))


def _count_non_positive(points):
    """How many readings a log axis has to drop."""
    return sum(1 for _, value in points if value is not None and value <= 0)


def _chart_note(scale, dropped, has_readings):
    """The line printed under one chart, or "" when there is nothing to say."""
    notes = []
    if scale == LOG and has_readings:
        # A column with nothing in it has no axis, so saying it is logarithmic
        # is noise on the page.
        notes.append("Log scale. One gridline per decade.")
    if dropped:
        notes.append("%d reading%s zero or negative, shown as gaps, because a "
                     "log axis cannot place them."
                     % (dropped, " was" if dropped == 1 else "s were"))
    return " ".join(notes)


# Outside this band a plain decimal is either all zeroes or all digits, so the
# summary table switches to scientific notation. A reading of 1e-9 torr must not
# print as 0.00, and it did until three of these drivers started reading
# pressure.
SMALL_NUMBER = 0.01
LARGE_NUMBER = 100000.0


def _tidy_number(value):
    """Show a number without a tail of meaningless decimal places."""
    size = abs(value)
    if size != 0 and (size < SMALL_NUMBER or size >= LARGE_NUMBER):
        return "%.2E" % value
    if value == int(value):
        return "%d" % int(value)
    return "%.2f" % value


def _summarise(points):
    """Latest, lowest and highest for one column, for the table at the top."""
    values = [v for _, v in points if v is not None]
    if not values:
        return {"latest": "no data", "low": "", "high": "", "count": 0}
    return {
        "latest": _tidy_number(values[-1]),
        "low": _tidy_number(min(values)),
        "high": _tidy_number(max(values)),
        "count": len(values),
    }


PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
  :root {
    --ink: #1a1a1a; --soft: #666; --rule: #d8d8d8;
    --bg: #ffffff; --panel: #f7f7f7; --line: #1f6feb; --line2: #b8860b;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --ink: #e8e8e8; --soft: #a0a0a0; --rule: #3a3a3a;
      --bg: #161616; --panel: #202020; --line: #5aa0ff; --line2: #e0b040;
    }
  }
  body { margin: 0; padding: 24px; background: var(--bg); color: var(--ink);
         font: 14px/1.5 "Segoe UI", system-ui, sans-serif; }
  h1 { font-size: 20px; margin: 0 0 4px; }
  .meta { color: var(--soft); margin-bottom: 20px; }
  table { border-collapse: collapse; margin-bottom: 28px; }
  th, td { text-align: left; padding: 6px 16px 6px 0; border-bottom: 1px solid var(--rule); }
  th { color: var(--soft); font-weight: 600; }
  section { margin-bottom: 28px; }
  h2 { font-size: 15px; margin: 0 0 6px; }
  .chart { width: 100%; height: 220px; background: var(--panel); border: 1px solid var(--rule); }
  .line { fill: none; stroke: var(--line); stroke-width: 1.6; }
  .point { fill: var(--line); }
  /* The second line on a chart that has two, drawn dashed as well as in
     another colour. A reader who cannot tell the two colours apart can still
     tell the two lines apart, and so can a black and white printout. */
  .line.alt { stroke: var(--line2); stroke-dasharray: 5 3; }
  .point.alt { fill: var(--line2); }
  .legend { color: var(--soft); font-size: 12px; margin: 0 0 6px; }
  .key { display: inline-block; width: 22px; border-top: 2px solid var(--line);
         margin: 0 6px 4px 0; vertical-align: middle; }
  .key.alt { border-top: 2px dashed var(--line2); }
  .legend span + .key { margin-left: 18px; }
  .grid { stroke: var(--rule); stroke-width: 1; }
  .ylabel { fill: var(--soft); font-size: 11px; text-anchor: end; }
  .nodata { color: var(--soft); font-style: italic; }
  .span { color: var(--soft); font-size: 12px; margin-top: 4px; }
  footer { color: var(--soft); font-size: 12px; border-top: 1px solid var(--rule);
           padding-top: 12px; margin-top: 24px; }
</style>
</head>
<body>
<h1>__TITLE__</h1>
<div class="meta">Built __BUILT__ from __ROWS__ readings. __SPAN__</div>
__SUMMARY__
__CHARTS__
<footer>
This page holds its own data and works with no network. A break in a line is a
reading that failed, not a reading of zero.
</footer>
</body>
</html>
"""


def render_trend_page(rows, columns, title, built_at=None, scales=None,
                      overlays=None):
    """Return the HTML for one device's trend page.

    rows:    the reading rows, oldest first, as read_history returns them.
    columns: which columns to plot, in the order they should appear.
    title:   the heading, usually the device name.
    scales:  an optional dictionary of column name to LINEAR or LOG. A column
             that is not named is drawn on a linear axis, which is what a
             temperature or a flow rate wants. Pressure wants LOG, because it
             runs over nine decades and a linear axis hides all of it below
             about 1 torr. The choice belongs to the driver, because only the
             driver knows what the column holds.
    overlays: an optional dictionary of column name to the column drawn over
             it on the same axes. Use it for a reading and the setpoint it is
             supposed to be holding.

             This exists because separate charts cannot answer the question a
             setpoint is for. Each chart scales to its own values, so a
             setpoint that never moves fills its chart exactly as much as a
             temperature that has drifted five degrees, and the gap between
             them, which is the only thing worth looking at, is nowhere on the
             page. On shared axes it is the first thing you see.

             The overlaid column still gets its own row in the summary table.
             It does not get a chart of its own, because it already has one.
    """
    built_at = built_at or datetime.datetime.now()
    scales = dict(scales or {})
    overlays = dict(overlays or {})

    unknown = set(scales) - set(columns)
    if unknown:
        # A misspelled column name would otherwise leave the chart on a linear
        # axis with nothing saying so, which is exactly the silent wrongness
        # this whole library is built to avoid.
        raise ValueError(
            "these columns were given a scale but are not being plotted: %s. "
            "The columns are: %s"
            % (", ".join(sorted(unknown)), ", ".join(columns)))

    # Same reasoning. A misspelled name here would silently drop the second
    # line off a chart and leave a page that looks finished.
    named = set(overlays) | set(overlays.values())
    unknown = named - set(columns)
    if unknown:
        raise ValueError(
            "these columns were named in overlays but are not being plotted: "
            "%s. The columns are: %s"
            % (", ".join(sorted(unknown)), ", ".join(columns)))

    # A column cannot be drawn over something and also have something drawn
    # over it. Two lines on one axis is readable and three is not, and a chain
    # of overlays is a way of asking for three without noticing.
    both = set(overlays) & set(overlays.values())
    if both:
        raise ValueError(
            "these columns are both overlaid and overlaid on: %s. A chart "
            "holds two lines, not a chain of them." % ", ".join(sorted(both)))

    series = {}
    for column in columns:
        series[column] = [(index, _to_number(row.get(column)))
                          for index, row in enumerate(rows)]

    summary_rows = []
    for column in columns:
        facts = _summarise(series[column])
        summary_rows.append(
            "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
            % (html.escape(column), facts["latest"], facts["low"], facts["high"],
               facts["count"]))
    summary = ('<table><tr><th>Reading</th><th>Latest</th><th>Lowest</th>'
               '<th>Highest</th><th>Points</th></tr>%s</table>'
               % "".join(summary_rows))

    # A column drawn over another one has no chart of its own, because it is
    # already on that one.
    drawn_elsewhere = set(overlays.values())

    charts = []
    for column in columns:
        if column in drawn_elsewhere:
            continue
        scale = scales.get(column, LINEAR)
        companion = overlays.get(column)
        lines = [series[column]]
        if companion:
            lines.append(series[companion])

        dropped = sum(_count_non_positive(line) for line in lines) \
            if scale == LOG else 0
        plotted = [value for line in lines for _, value in line
                   if value is not None and (scale == LINEAR or value > 0)]
        note = _chart_note(scale, dropped, bool(plotted))

        if companion:
            heading = "%s and %s" % (column, companion)
            legend = ('<p class="legend"><i class="key"></i><span>%s</span>'
                      '<i class="key alt"></i><span>%s</span></p>'
                      % (html.escape(column), html.escape(companion)))
        else:
            heading = column
            legend = ""

        charts.append(
            '<section><h2>%s</h2>%s%s%s</section>'
            % (html.escape(heading), legend,
               _chart_svg(lines, scale=scale),
               ('<p class="span">%s</p>' % html.escape(note)) if note else ""))

    if rows:
        first = rows[0].get("timestamp", "")
        last = rows[-1].get("timestamp", "")
        span = "Covering %s to %s." % (html.escape(first), html.escape(last))
    else:
        span = "No readings found for this window."

    page = PAGE_TEMPLATE
    page = page.replace("__TITLE__", html.escape(title))
    page = page.replace("__BUILT__", built_at.strftime("%Y-%m-%d %H:%M:%S"))
    page = page.replace("__ROWS__", str(len(rows)))
    page = page.replace("__SPAN__", span)
    page = page.replace("__SUMMARY__", summary)
    page = page.replace("__CHARTS__", "".join(charts))
    return page


def write_trend_page(history_folder, name, columns, out_path, title=None,
                     days=7, today=None, built_at=None, scales=None,
                     overlays=None):
    """Read a device's history and write its trend page. Returns the path.

    scales and overlays are passed straight through to render_trend_page. See
    it for what each one is and when a column needs one.
    """
    rows = read_history(history_folder, name, days=days, today=today)
    page = render_trend_page(rows, columns, title or name, built_at=built_at,
                             scales=scales, overlays=overlays)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(page, encoding="utf-8")
    return out_path
