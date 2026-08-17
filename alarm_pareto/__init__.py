"""Alarm Log Pareto Tool.

This package reads an alarm log from a semiconductor tool. It filters the log
to a trailing time window. It then ranks faults by how often they happen and by
how much downtime they cause. The results go into an Excel workbook and a
PowerPoint deck.

The pipeline is split into small modules on purpose. Adding a new tool vendor
should be a text edit to the JSON config, not a code change.

Module order in the pipeline:
    parse      -> read the file into a raw table
    normalize  -> rename vendor columns to standard names
    window     -> keep only the trailing time window
    aggregate  -> build the count and downtime rankings
    render_xlsx-> write the Excel workbook
    render_pptx-> write the PowerPoint deck
"""

__version__ = "1.4.0"
