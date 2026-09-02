"""Thermo NESLAB and ThermoFlex chillers, on the NC serial protocol.

Read PROTOCOL.md in this folder before changing the driver. Two Thermo NESLAB
manuals were read directly for it, which is a first for this project, so most of
the protocol here is quoted from a manual. What is not is the ThermoFlex
specific part, which rests on one open source library and is listed in
REVIEW.md.

This is the first binary protocol in the library. It has no terminator, and a
frame is found by the length written inside it. That is why the shared transport
grew a reply_size hook, and it is why a transport for this device has to be
built with build_transport rather than the ordinary way.
"""

from .driver import (
    COMMANDS,
    COMMANDS_BY_NAME,
    LEAD_RS232,
    LEAD_RS485,
    MODELS,
    NcReply,
    Reading,
    RTE_STATUS_BITS,
    THERMOFLEX_STATUS_BITS,
    ThermoChiller,
    UNIT_NAMES,
    build_policy,
    build_transport,
    checksum,
    decode_measurement,
    decode_status,
    reply_size,
    serial_settings,
    split_qualifier,
)
from .mock import ThermoChillerResponder, encode_measurement, mock_checksum
from .trend import (
    column_for,
    history_columns,
    setpoint_overlay,
    write_thermo_chiller_trend_page,
)

__all__ = [
    "COMMANDS",
    "COMMANDS_BY_NAME",
    "LEAD_RS232",
    "LEAD_RS485",
    "MODELS",
    "NcReply",
    "RTE_STATUS_BITS",
    "Reading",
    "THERMOFLEX_STATUS_BITS",
    "ThermoChiller",
    "ThermoChillerResponder",
    "UNIT_NAMES",
    "build_policy",
    "build_transport",
    "checksum",
    "column_for",
    "decode_measurement",
    "decode_status",
    "encode_measurement",
    "history_columns",
    "mock_checksum",
    "reply_size",
    "serial_settings",
    "setpoint_overlay",
    "split_qualifier",
    "write_thermo_chiller_trend_page",
]
