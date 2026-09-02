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


def _chart_svg(points, colour="#1f6feb"):
    """Draw one column as an SVG line chart.

    points is a list of (index, value_or_None), already in time order.
    """
    values = [v for _, v in points if v is not None]
    if not values:
        return ('<p class="nodata">No readings in this window.</p>')

    low, high = min(values), max(values)
    if low == high:
        # A flat line would otherwise divide by zero. Give it room above and
        # below so it sits in the middle of the chart rather than on an edge.
        low, high = low - 1.0, high + 1.0

    plot_width = CHART_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
    plot_height = CHART_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM
    last_index = max(len(points) - 1, 1)

    def sx(index):
        return MARGIN_LEFT + (index / last_index) * plot_width

    def sy(value):
        share = (value - low) / (high - low)
        return MARGIN_TOP + (1.0 - share) * plot_height

    parts = []

    # Three gridlines with their values, so the eye has something to measure by.
    for share in (0.0, 0.5, 1.0):
        value = low + share * (high - low)
        y = sy(value)
        parts.append('<line class="grid" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                     % (MARGIN_LEFT, y, CHART_WIDTH - MARGIN_RIGHT, y))
        parts.append('<text class="ylabel" x="%.1f" y="%.1f">%s</text>'
                     % (MARGIN_LEFT - 8, y + 4, _tidy_number(value)))

    for run in _segments(points):
        if len(run) == 1:
            # A lone reading between two gaps would be an invisible line, so
            # show it as a dot instead.
            x, value = run[0]
            parts.append('<circle class="point" cx="%.1f" cy="%.1f" r="2.5"/>'
                         % (sx(x), sy(value)))
            continue
        coords = " ".join("%.1f,%.1f" % (sx(x), sy(v)) for x, v in run)
        parts.append('<polyline class="line" points="%s"/>' % coords)

    return ('<svg class="chart" viewBox="0 0 %d %d" preserveAspectRatio="none" '
            'role="img">%s</svg>' % (CHART_WIDTH, CHART_HEIGHT, "".join(parts)))


def _tidy_number(value):
    """Show a number without a tail of meaningless decimal places."""
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
    --bg: #ffffff; --panel: #f7f7f7; --line: #1f6feb;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --ink: #e8e8e8; --soft: #a0a0a0; --rule: #3a3a3a;
      --bg: #161616; --panel: #202020; --line: #5aa0ff;
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


def render_trend_page(rows, columns, title, built_at=None):
    """Return the HTML for one device's trend page.

    rows:    the reading rows, oldest first, as read_history returns them.
    columns: which columns to plot, in the order they should appear.
    title:   the heading, usually the device name.
    """
    built_at = built_at or datetime.datetime.now()

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

    charts = []
    for column in columns:
        charts.append('<section><h2>%s</h2>%s</section>'
                      % (html.escape(column), _chart_svg(series[column])))

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
                     days=7, today=None, built_at=None):
    """Read a device's history and write its trend page. Returns the path."""
    rows = read_history(history_folder, name, days=days, today=today)
    page = render_trend_page(rows, columns, title or name, built_at=built_at)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(page, encoding="utf-8")
    return out_path
