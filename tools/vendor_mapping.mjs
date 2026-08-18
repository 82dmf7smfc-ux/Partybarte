// Turn a vendor block from the Python tool's config into the column mapping the
// browser tool uses.
//
// Why this exists. The parity check needs to tell the browser tool which column
// holds what. That information already lives in
// alarm_pareto/config/vendor_columns.json. Writing it out a second time here
// would mean the check could pass while the config it is meant to represent had
// drifted. Reading the real config removes that whole class of mistake.
//
// The browser tool does not read this file at runtime. It guesses columns and
// lets the user correct them in the page. This is for the check only.

import { readFileSync } from "node:fs";
import { join } from "node:path";
import { ROOT } from "./browser_core.mjs";

const CONFIG_PATH = join(ROOT, "alarm_pareto", "config", "vendor_columns.json");

// How many seconds are in one unit of a duration column. This mirrors
// _seconds_scale in alarm_pareto/normalize.py.
const SECONDS_PER_UNIT = {
  second: 1, seconds: 1, s: 1, sec: 1,
  minute: 60, minutes: 60, m: 60, min: 60,
  hour: 3600, hours: 3600, h: 3600, hr: 3600
};

/** Read one vendor block out of the shared config. */
export function loadVendorConfig(vendor, configPath = CONFIG_PATH) {
  const all = JSON.parse(readFileSync(configPath, "utf8"));
  if (!Object.prototype.hasOwnProperty.call(all, vendor)) {
    const real = Object.keys(all).filter((k) => !k.startsWith("_"));
    throw new Error(
      `Vendor '${vendor}' is not in ${configPath}. Available vendors: ${real.join(", ")}`
    );
  }
  return all[vendor];
}

/**
 * Build the browser tool's mapping from a vendor block.
 *
 * Throws if the vendor uses a downtime shape the browser tool cannot read, so
 * a silently wrong comparison is impossible.
 */
export function browserMapping(vendor, configPath = CONFIG_PATH) {
  const config = loadVendorConfig(vendor, configPath);
  const columns = config.columns || {};

  for (const required of ["ts_set", "fault_code", "description", "equipment"]) {
    if (!columns[required]) {
      throw new Error(
        `Vendor '${vendor}' does not map '${required}'. The parity check needs ` +
        `all four of ts_set, fault_code, description and equipment.`
      );
    }
  }

  const mapping = {
    ts_set: columns.ts_set,
    fault_code: columns.fault_code,
    description: columns.description,
    equipment: columns.equipment,
    downMode: "none",
    durCol: "",
    durScale: 1,
    stateCol: "",
    setVal: "SET",
    clearVal: "CLEAR"
  };

  // The same three shapes detect_mode picks between in normalize.py, in the
  // same order, so both tools decide the same way.
  if (columns.duration_s) {
    const unit = String(config.duration_unit || "seconds").toLowerCase();
    const scale = SECONDS_PER_UNIT[unit];
    if (scale === undefined) {
      throw new Error(
        `Vendor '${vendor}' has duration_unit '${config.duration_unit}'. ` +
        `Use seconds, minutes, or hours.`
      );
    }
    mapping.downMode = "duration";
    mapping.durCol = columns.duration_s;
    mapping.durScale = scale;
    return mapping;
  }

  if (columns.ts_set && columns.ts_clear) {
    throw new Error(
      `Vendor '${vendor}' uses paired intervals, where one row carries both a ` +
      `set time and a clear time. The browser tool has no mode for that, so ` +
      `there is nothing to compare. This is a known difference between the two ` +
      `tools and it is written down in ROADMAP.md.`
    );
  }

  if (columns.event_type) {
    const values = config.event_values || {};
    mapping.downMode = "events";
    mapping.stateCol = columns.event_type;
    mapping.setVal = String(values.set || "SET").toUpperCase();
    mapping.clearVal = String(values.clear || "CLEAR").toUpperCase();
    return mapping;
  }

  throw new Error(
    `Vendor '${vendor}' does not say how downtime is stored. The config must ` +
    `map one of duration_s, or both ts_set and ts_clear, or event_type.`
  );
}
