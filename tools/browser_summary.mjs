// Run the browser tool's analysis over a log file and print the numbers as JSON.
//
// The output uses the same shape as tests/data/expected_summary.json, so the
// browser tool and the Python tool can be checked against one golden file.
//
// Usage:
//   node tools/browser_summary.mjs [path-to-csv] [window-days] [vendor]
//
// With no arguments it uses the project's sample log, a 30 day window, and the
// "amat" vendor block from alarm_pareto/config/vendor_columns.json.

import { readFileSync } from "node:fs";
import { join } from "node:path";
import { loadBrowserCore, ROOT } from "./browser_core.mjs";
import { browserMapping } from "./vendor_mapping.mjs";

const LEVELS = ["fault_code", "description", "equipment"];

// A top-N big enough that nothing is folded into an "Other" bucket. Used for
// the per-group totals, where the golden file lists every group.
const NO_COLLAPSE = 100000;

// The ranking block is checked at a deliberately small top-N so the "Other"
// bucket is exercised. That bucket is real code that users hit at the default
// of 15 whenever a tool has more than 15 distinct faults, and comparing only
// the uncollapsed totals would never touch it.
const RANKING_TOP_N = 2;

export function summarize(csvText, windowDays = 30, mapping = browserMapping("amat"), method = "attributed") {
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

  // The ranking. Order, percent and cumulative percent all matter here. A
  // Pareto chart is read top to bottom, and the cumulative line is the whole
  // point of it, so comparing group totals alone would miss the thing users
  // actually look at.
  const ranking = { top_n: RANKING_TOP_N, method };
  for (const level of LEVELS) {
    const ranked = core.rankLevel(kept, level, method, RANKING_TOP_N);
    ranking[level] = {
      by_count: ranked.byCount.map(rankedRow),
      by_downtime: ranked.byDown.map(rankedRow)
    };
  }
  summary.ranking = ranking;

  return summary;
}

/** Flatten one ranked row into the shape the golden files use. */
function rankedRow(row) {
  return {
    rank: row.rank,
    key: row.key,
    count: row.count,
    attributed_s: round(row.attributed_s),
    wallclock_s: round(row.wallclock_s),
    pct: round6(row.pct),
    cum: round6(row.cum)
  };
}

// Percentages are compared to six decimal places. That is far tighter than
// anything a chart shows, and loose enough that the last bit of floating point
// does not cause a false alarm.
function round6(n) {
  return Math.round(n * 1e6) / 1e6;
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
  const vendor = process.argv[4] || "amat";
  const text = readFileSync(csvPath, "utf8");
  const summary = summarize(text, windowDays, browserMapping(vendor));
  process.stdout.write(JSON.stringify(summary, null, 2) + "\n");
}
