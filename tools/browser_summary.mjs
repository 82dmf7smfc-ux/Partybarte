// Run the browser tool's analysis over a log file and print the numbers as JSON.
//
// The output uses the same shape as tests/data/expected_summary.json, so the
// browser tool and the Python tool can be checked against one golden file.
//
// Usage:
//   node tools/browser_summary.mjs [path-to-csv] [window-days] [top-n]
//
// With no arguments it uses the project's sample log and a 30 day window.

import { readFileSync } from "node:fs";
import { join } from "node:path";
import { loadBrowserCore, ROOT } from "./browser_core.mjs";

// The column mapping for the sample log. These are the same names the "amat"
// block in alarm_pareto/config/vendor_columns.json uses, so both tools read the
// file the same way.
const SAMPLE_MAPPING = {
  ts_set: "EventTime",
  fault_code: "AlarmID",
  description: "AlarmText",
  equipment: "ChamberID",
  downMode: "duration",
  durCol: "DownSeconds",
  durScale: 1,
  stateCol: "",
  setVal: "SET",
  clearVal: "CLEAR"
};

const LEVELS = ["fault_code", "description", "equipment"];

// A top-N big enough that nothing is folded into an "Other" bucket. The golden
// file lists every group, so the comparison must see every group.
const NO_COLLAPSE = 100000;

export function summarize(csvText, windowDays = 30, mapping = SAMPLE_MAPPING) {
  const core = loadBrowserCore();

  const parsed = core.parseDelimited(csvText);
  const built = core.buildOccurrences(parsed.rows, mapping);
  const win = core.applyWindow(built.occ, windowDays);
  const kept = win.kept;

  const summary = {
    window: {
      window_days: windowDays,
      window_start: core.fmt(win.start),
      window_end: core.fmt(win.end),
      windowed_row_count: kept.length,
      raw_row_count: parsed.rows.length
    },
    grand: {
      total_faults: kept.length,
      attributed_downtime_s: round(kept.reduce((s, o) => s + o.durSec, 0)),
      wallclock_downtime_s: round(core.mergedSeconds(kept.map((o) => [o.start, o.end])))
    }
  };

  for (const level of LEVELS) {
    // Going through rankLevel means the shipped ranking code is exercised, not
    // just the grouping. Sorting order does not matter here, only the totals.
    const ranked = core.rankLevel(kept, level, "attributed", NO_COLLAPSE);
    const count = {};
    const attributed_s = {};
    const wallclock_s = {};
    for (const row of ranked.byCount) {
      count[row.key] = row.count;
      attributed_s[row.key] = round(row.attributed_s);
      wallclock_s[row.key] = round(row.wallclock_s);
    }
    summary[level] = { count, attributed_s, wallclock_s };
  }

  return summary;
}

// Seconds are whole numbers in practice. Rounding keeps floating point noise
// from showing up as a false mismatch against the golden file.
function round(n) {
  return Math.round(n * 1e6) / 1e6;
}

/** Return the sample log text that is baked into the HTML file. */
export function builtInSample() {
  return loadBrowserCore().SAMPLE_CSV;
}

const isMain = process.argv[1] && process.argv[1].endsWith("browser_summary.mjs");
if (isMain) {
  const csvPath = process.argv[2] || join(ROOT, "tests", "data", "sample_alarm_log.csv");
  const windowDays = Number(process.argv[3] || 30);
  const text = readFileSync(csvPath, "utf8");
  process.stdout.write(JSON.stringify(summarize(text, windowDays), null, 2) + "\n");
}
