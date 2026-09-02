"""Wire the pipeline together and handle command line arguments.

Run it like this from the project folder:

    python -m alarm_pareto.main --input tests/data/sample_alarm_log.csv --vendor amat

Add --start-time and --end-time to narrow the report to one shift:

    python -m alarm_pareto.main --input log.csv --start-time 22:00 --end-time 06:00

This reads the log, filters to the trailing window, builds the rankings, and
writes an Excel workbook and a PowerPoint deck into the output folder.
"""

import argparse
import sys
from pathlib import Path

from . import aggregate as agg
from . import normalize as nz
from . import parse as parse_mod
from . import render_pptx
from . import render_xlsx
from . import window as window_mod

# The config file that ships with the package. It sits next to this file.
DEFAULT_CONFIG = Path(__file__).parent / "config" / "vendor_columns.json"


def build_arg_parser():
    """Set up the command line options and their defaults."""
    p = argparse.ArgumentParser(
        description="Pareto analysis of a semiconductor tool alarm log."
    )
    p.add_argument("--input", required=True, help="Path to the alarm log file.")
    p.add_argument("--vendor", default="amat", help="Vendor key in the config. Default: amat.")
    p.add_argument("--config", default=str(DEFAULT_CONFIG),
                   help="Path to the vendor column config JSON.")
    p.add_argument("--window-days", type=int, default=30,
                   help="Length of the trailing window in days. Default: 30.")
    p.add_argument("--start-time", default=None,
                   help="Keep only alarms that start at or after this clock time, "
                        "as HH:MM. Use with --end-time to report on one shift. "
                        "Default: no time-of-day filter.")
    p.add_argument("--end-time", default=None,
                   help="Keep only alarms that start before this clock time, as "
                        "HH:MM. A start later than the end wraps past midnight, "
                        "so 22:00 to 06:00 is the night shift.")
    p.add_argument("--top-n", type=int, default=15,
                   help="How many rows before the rest become 'Other'. Default: 15.")
    p.add_argument("--downtime-method", choices=[agg.METHOD_ATTRIBUTED, agg.METHOD_WALLCLOCK],
                   default=agg.METHOD_ATTRIBUTED,
                   help="Which downtime number drives the downtime ranking. Default: attributed.")
    p.add_argument("--output-dir", default="output",
                   help="Folder for the output files. Default: output.")
    return p


def run(args):
    """Run the whole pipeline once and return the paths that were written."""
    # Step 1 and 2: read the file, then rename columns to internal names.
    vendor_config = parse_mod.load_vendor_config(args.config, args.vendor)
    raw = parse_mod.read_log(args.input, vendor_config)
    table, mode = nz.normalize(raw, vendor_config)

    # Step 3: keep only the trailing window.
    windowed, window_start, window_end = window_mod.apply_window(table, args.window_days)
    if windowed.empty:
        raise ValueError(
            "No rows fall inside the %d day window. Check the window length or the file."
            % args.window_days
        )

    # Step 3b: narrow those days to a range of clock hours, if one was asked
    # for. This runs after the trailing window so the window start and end
    # stay tied to the file, not to whichever shift was picked.
    tod_start = window_mod.parse_time_of_day(args.start_time)
    tod_end = window_mod.parse_time_of_day(args.end_time)
    if (tod_start is None) != (tod_end is None):
        raise ValueError(
            "--start-time and --end-time go together. Give both, or neither."
        )
    windowed = window_mod.apply_time_of_day(windowed, tod_start, tod_end)
    if windowed.empty:
        raise ValueError(
            "No rows start between %s and %s inside the %d day window."
            % (args.start_time, args.end_time, args.window_days)
        )

    # Step 4: build the rankings and headline numbers.
    result = agg.aggregate(
        windowed, mode, vendor_config, window_start, window_end,
        window_days=args.window_days, top_n=args.top_n,
        downtime_method=args.downtime_method,
        tod_start=tod_start, tod_end=tod_end,
    )

    # Make sure the output folder exists.
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    xlsx_path = out_dir / "alarm_pareto.xlsx"
    pptx_path = out_dir / "alarm_pareto.pptx"

    # Step 5 and 6: write the workbook and the deck.
    render_xlsx.write_workbook(result, windowed, xlsx_path)
    render_pptx.write_deck(result, pptx_path)

    return {"xlsx": xlsx_path, "pptx": pptx_path, "result": result}


def main(argv=None):
    """Entry point. Parses arguments and prints a short report."""
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        out = run(args)
    except (FileNotFoundError, KeyError, ValueError) as err:
        # These are the expected, user-fixable errors. Print a clean message
        # instead of a long traceback.
        print("Error: %s" % err, file=sys.stderr)
        return 1

    grand = out["result"]["grand"]
    print("Done.")
    print("  Window: %s to %s (%s days)" % (
        grand["window_start"], grand["window_end"], grand["window_days"]))
    print("  Time of day: %s" % grand["time_of_day_label"])
    print("  Total faults: %d" % grand["total_faults"])
    print("  Attributed downtime: %.2f hours" % grand["attributed_downtime_hours"])
    print("  True wall-clock downtime: %.2f hours" % grand["wallclock_downtime_hours"])
    print("  Workbook: %s" % out["xlsx"])
    print("  Deck:     %s" % out["pptx"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
