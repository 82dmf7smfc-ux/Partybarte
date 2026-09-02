"""Granville-Phillips 275, 375, 350 and 356 gauge modules and controllers.

Read PROTOCOL.md in this folder before changing the driver. It says where every
fact came from and how strongly it is held, which matters here because no
Granville-Phillips manual could be opened on this machine. Every site hosting
one was refused by the network egress policy.
"""

from .driver import (
    GaugeChannel,
    GranvillePhillipsGauge,
    MODELS,
    NO_READING,
    UNITS,
    build_policy,
    format_address,
    serial_settings,
)
from .mock import GranvillePhillipsResponder, format_pressure
from .trend import (
    history_columns,
    pressure_scales,
    write_granville_phillips_trend_page,
)

__all__ = [
    "GaugeChannel",
    "GranvillePhillipsGauge",
    "GranvillePhillipsResponder",
    "MODELS",
    "NO_READING",
    "UNITS",
    "build_policy",
    "format_address",
    "format_pressure",
    "history_columns",
    "pressure_scales",
    "serial_settings",
    "write_granville_phillips_trend_page",
]
