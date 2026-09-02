"""Write readings to daily CSV files so they can be trended.

Why this exists
---------------
A number on a screen tells you the value now. A column of numbers over three
weeks tells you the cold head is losing ground. The second one is what catches a
problem before it stops the tool.

One file per day keeps each file small enough to open in Excel. The columns are
fixed when the writer is made, and the header is written once at the top of each
new file, so a day's file always stands on its own.

The column list is deliberately not automatic. If a driver quietly added a column
one day, every file after that would have a different shape, and the trend model
built on top would break. Changing columns should be a decision someone writes
down, not a side effect.
"""

import csv
import datetime
from pathlib import Path


class HistoryWriter:
    """Append rows to one CSV file per day.

    folder:  where the files go. It is created if it is missing.
    name:    the first part of each file name, usually the device name.
    columns: the column names, in the order they appear in the file. The first
             column is always the timestamp, added for you. Do not include it.

    A file is called <name>_<date>.csv, for example lakeshore_2026-09-02.csv.
    """

    TIMESTAMP_COLUMN = "timestamp"

    def __init__(self, folder, name, columns):
        if not columns:
            raise ValueError("a history writer needs at least one column")
        if self.TIMESTAMP_COLUMN in columns:
            raise ValueError(
                "do not list %r yourself, it is always the first column"
                % self.TIMESTAMP_COLUMN
            )
        self.folder = Path(folder)
        self.name = name
        self.columns = list(columns)
        self.header = [self.TIMESTAMP_COLUMN] + self.columns
        self.folder.mkdir(parents=True, exist_ok=True)

    def path_for(self, when=None):
        """Return the file this row belongs in, based on its date."""
        when = when or datetime.datetime.now()
        return self.folder / ("%s_%s.csv" % (self.name, when.strftime("%Y-%m-%d")))

    def append(self, values, when=None):
        """Write one row.

        values: a dictionary of column name to value. A column that is missing,
                or set to None, is written as an empty cell. That is on purpose.
                A reading that failed must leave a hole in the trend, not a zero.
                A zero looks like a real measurement and would quietly bend any
                average built on top of it.
        """
        when = when or datetime.datetime.now()

        unknown = set(values) - set(self.columns)
        if unknown:
            raise ValueError(
                "these are not columns of this file: %s. The columns are: %s"
                % (", ".join(sorted(unknown)), ", ".join(self.columns))
            )

        path = self.path_for(when)
        is_new = not path.exists()
        row = [when.strftime("%Y-%m-%d %H:%M:%S")]
        for column in self.columns:
            value = values.get(column)
            row.append("" if value is None else value)

        # newline="" is what the csv module asks for. Without it, Windows writes
        # a blank line between every row.
        with path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if is_new:
                writer.writerow(self.header)
            writer.writerow(row)
        return path
