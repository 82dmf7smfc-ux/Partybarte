"""Build the trend page for a Lakeshore monitor.

This is a thin wrapper around the shared generator in core/trend_page.py. It
exists so a driver says what to plot in one place, rather than every caller
having to remember which columns a 336 has.

Do not write a page here. Ten drivers each inventing a page gives ten pages that
behave differently. If the shared generator cannot do something this device
needs, improve the generator so every driver gets it.
"""

from ...core.trend_page import write_trend_page
from .driver import MODELS


def history_columns(model, names=None):
    """The CSV columns for one model, in input order.

    names is an optional dictionary of input name to the name somebody typed on
    the front panel, as INNAME? returns it. When it is given, a column is called
    "A Cold head" rather than "A". The input letter stays on the front so the
    column still says which socket the reading came from, which is what you need
    when you are standing at the instrument with a cable in your hand.
    """
    names = names or {}
    columns = []
    for sensor_input in MODELS[model].inputs:
        label = names.get(sensor_input, "").strip()
        columns.append("%s %s" % (sensor_input, label) if label
                       else sensor_input)
    return columns


def write_lakeshore_trend_page(history_folder, name, out_path, model,
                               names=None, title=None, days=7, today=None,
                               built_at=None):
    """Read a monitor's daily CSV files and write its trend page.

    history_folder and name are the ones the HistoryWriter was built with.
    model decides which columns are plotted. Returns the path written.
    """
    columns = history_columns(model, names)
    return write_trend_page(
        history_folder,
        name,
        columns,
        out_path,
        title=title or ("Lakeshore %s temperatures, kelvin" % model),
        days=days,
        today=today,
        built_at=built_at,
    )
