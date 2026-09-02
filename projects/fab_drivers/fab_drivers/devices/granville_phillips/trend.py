"""Build the trend page for a Granville-Phillips gauge.

This is a thin wrapper around the shared generator in core/trend_page.py. It
exists so a driver says what to plot in one place, rather than every caller
having to remember which gauges a 350 has and that pressure needs a log axis.

Do not write a page here. Ten drivers each inventing a page gives ten pages that
behave differently. The log axis this device needed went into the shared
generator for that reason, so the MKS and Pfeiffer drivers get it too.
"""

from ...core.trend_page import LOG, write_trend_page
from .driver import MODELS


def history_columns(model, units):
    """The CSV columns for one model, in gauge order.

    The unit is in every column name, because these instruments do not report
    which unit they are set to and a file with no unit in it is a file whose
    numbers cannot be checked later. A column reads "CGA Convectron A (torr)".
    """
    columns = []
    for channel in MODELS[model].channels:
        columns.append("%s %s (%s)" % (channel.key, channel.label, units))
    return columns


def pressure_scales(columns):
    """Put every pressure column on a log axis.

    Pressure runs from atmosphere down to 1e-9 torr. On a linear axis every
    reading below about 1 torr sits flat on the bottom of the chart, so the
    pumpdown that matters is invisible. This is the whole reason the shared
    generator learned about scales.
    """
    return {column: LOG for column in columns}


def write_granville_phillips_trend_page(history_folder, name, out_path, model,
                                        units, title=None, days=7, today=None,
                                        built_at=None):
    """Read a gauge's daily CSV files and write its trend page.

    history_folder and name are the ones the HistoryWriter was built with.
    model decides which columns are plotted. units is the one the instrument is
    set to, which the caller has to know because the instrument will not say.
    Returns the path written.
    """
    columns = history_columns(model, units)
    return write_trend_page(
        history_folder,
        name,
        columns,
        out_path,
        title=title or ("Granville-Phillips %s pressure, %s" % (model, units)),
        days=days,
        today=today,
        built_at=built_at,
        scales=pressure_scales(columns),
    )
