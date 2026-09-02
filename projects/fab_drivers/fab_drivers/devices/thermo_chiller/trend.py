"""Build the trend page for a Thermo chiller.

This is a thin wrapper around the shared generator in core/trend_page.py. It
exists so a driver says what to plot in one place, rather than every caller
having to remember which readings a ThermoFlex has that an RTE does not.

Do not write a page here. Ten drivers each inventing a page gives ten pages that
behave differently.

Everything on this device goes on a linear axis, which is the generator's
default, so this file passes no scales at all. The log axis the pressure gauges
needed is still there in the shared generator for whoever needs it next. See
pressure_scales in the Granville-Phillips trend module for how a driver asks for
one.

That is worth a sentence, because a chiller does have pressures on it. A pump
supply pressure runs from about zero to a handful of bar. It is a linear
quantity over a narrow range, unlike a vacuum gauge reading that crosses ten
decades, so a log axis would only make it harder to read.

What this device did need from the shared generator was a second line on one
chart, so the temperature and the setpoint it is holding sit on the same axes.
That went into the generator rather than in here, so the Watlow heater zones and
anything else with a setpoint get it too. See setpoint_overlay below.
"""

from ...core.trend_page import write_trend_page
from .driver import COMMANDS_BY_NAME, MODELS


def history_columns(model, units=None):
    """The CSV columns for one model, in trend order.

    A column reads "Bath temperature (C)". The unit is in the name because a
    file whose numbers have no unit is a file nobody can check later.

    Unlike the Granville-Phillips gauges, this instrument states its unit in
    every reply and the driver refuses a reading in the wrong one. So these unit
    names are checked against the instrument every time a value is read, rather
    than being the caller's promise. units overrides them if you need to.
    """
    units = dict(units or {})
    columns = []
    for command_name in MODELS[model].trend_reads:
        entry = COMMANDS_BY_NAME[command_name]
        unit = units.get(command_name, entry.unit or _default_unit(command_name))
        columns.append("%s (%s)" % (entry.label, unit))
    return columns


# The units the readings without a fixed one come back in. The driver does not
# pin these, because a chiller can be set to PSI or to bar and it says which in
# every reply. These are only what the column is named, and the name is checked
# against reality by column_units below.
_UNSET_UNITS = {
    "read_flow": "LPM",
    "read_supply_pressure": "bar",
    "read_suction_pressure": "bar",
    "read_low_flow_limit": "LPM",
    "read_high_flow_limit": "LPM",
    "read_low_pressure_limit": "bar",
    "read_high_pressure_limit": "bar",
}


def _default_unit(command_name):
    """What to call the unit of a reading the driver does not pin."""
    return _UNSET_UNITS.get(command_name, "")


def column_for(command_name, units=None):
    """The CSV column name for one reading.

    The poller keys its readings by command name and the history file wants
    column names, so something has to map between them. Doing it here means the
    two cannot drift apart.
    """
    units = dict(units or {})
    entry = COMMANDS_BY_NAME[command_name]
    unit = units.get(command_name, entry.unit or _default_unit(command_name))
    return "%s (%s)" % (entry.label, unit)


def setpoint_overlay(model, units=None):
    """Draw the setpoint over the bath temperature, on the same axes.

    This is the one thing a chiller trend is really for. A chiller that has
    drifted away from its setpoint is a chiller with a fouled condenser, a
    failing pump or a load it cannot hold, and it is a fault you want to see
    days before somebody notices a process moving.

    On separate charts you cannot see it. Each chart scales itself to its own
    readings, so a setpoint that has not moved all week fills its chart from
    top to bottom exactly as much as a temperature that has climbed five
    degrees. The two lines both look flat, or both look dramatic, and the gap
    between them is nowhere on the page. On shared axes the gap is the first
    thing the eye lands on.

    This was checked by generating a page and looking at it, which is the only
    way this kind of thing gets caught.
    """
    columns = history_columns(model, units)
    temperature = column_for("read_internal_temperature", units)
    setpoint = column_for("read_setpoint", units)
    if temperature not in columns or setpoint not in columns:
        return {}
    return {temperature: setpoint}


def write_thermo_chiller_trend_page(history_folder, name, out_path, model,
                                    title=None, days=7, today=None,
                                    built_at=None, units=None):
    """Read a chiller's daily CSV files and write its trend page.

    history_folder and name are the ones the HistoryWriter was built with.
    model decides which columns are plotted. Returns the path written.

    The setpoint is drawn over the temperature, on one pair of axes. See
    setpoint_overlay for why that matters more than it sounds like it does.
    """
    columns = history_columns(model, units)
    return write_trend_page(
        history_folder,
        name,
        columns,
        out_path,
        title=title or ("Thermo %s chiller" % MODELS[model].name),
        days=days,
        today=today,
        built_at=built_at,
        overlays=setpoint_overlay(model, units),
    )
