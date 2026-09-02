"""Step 1: read the alarm log file into a raw table.

This module does one job. It opens the file and returns the rows as they are.
It does not rename columns. It does not parse dates. Those jobs belong to
normalize.py. Keeping the steps separate makes each one easy to test.
"""

import json
from pathlib import Path

import pandas as pd


def load_vendor_config(config_path, vendor):
    """Load one vendor block from the JSON config file.

    config_path: path to vendor_columns.json.
    vendor: the key of the block to use, for example "amat".

    Returns the vendor block as a plain dictionary.
    """
    config_path = Path(config_path)
    # json.loads turns the file text into Python dicts and lists.
    all_vendors = json.loads(config_path.read_text(encoding="utf-8"))

    if vendor not in all_vendors:
        # Show the caller which vendor names do exist. Names that start with an
        # underscore are help text, not real vendors, so we hide them.
        real = [k for k in all_vendors if not k.startswith("_")]
        raise KeyError(
            "Vendor '%s' is not in the config. Available vendors: %s"
            % (vendor, ", ".join(real))
        )
    return all_vendors[vendor]


def read_log(input_path, vendor_config):
    """Read the alarm log file into a pandas DataFrame.

    A DataFrame is just a table. Each column has a name. Each row is one record.

    input_path: path to the CSV or delimited text file.
    vendor_config: the vendor block from load_vendor_config.

    Returns the raw table with the original vendor column names.
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError("Input file not found: %s" % input_path)

    # The delimiter tells pandas how columns are separated. A comma is the
    # default. A tab file would use "\t". This comes from the config so a new
    # file format does not need a code change.
    delimiter = vendor_config.get("delimiter", ",")

    # dtype=str reads every column as text first. We do this on purpose. It
    # stops pandas from guessing types and mangling things like fault codes
    # that look like numbers. normalize.py converts the columns it needs.
    # keep_default_na=False stops pandas from turning the text "NA" into an
    # empty value, which matters for real equipment names.
    raw = pd.read_csv(
        input_path,
        sep=delimiter,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8",
    )

    if raw.empty:
        raise ValueError("The input file has no data rows: %s" % input_path)

    return raw
