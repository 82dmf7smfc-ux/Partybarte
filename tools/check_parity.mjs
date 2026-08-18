// Check that the browser tool agrees with the golden files, and that its
// built-in sample still matches the sample log used by the Python tests.
//
// This is the guard against the biggest risk in the project. The same analysis
// is written twice, once in Python and once in JavaScript. They must give the
// same numbers. The Python tests check Python against the golden files. This
// checks the browser tool against the same files, so one set of hand-worked
// numbers governs both tools.
//
// Run it with:
//   node tools/check_parity.mjs
//
// It prints what it checked and exits non-zero if anything disagrees. It needs
// no packages and makes no network call.

import { readFileSync } from "node:fs";
import { join } from "node:path";
import { ROOT } from "./browser_core.mjs";
import { summarize, builtInSample } from "./browser_summary.mjs";

const DATA = join(ROOT, "tests", "data");

// Keys in a golden file that are notes for a human, not values to compare.
const IGNORED_KEYS = new Set(["_note", "_by_hand"]);

// The two logs we check, and how the browser tool should be told to read them.
// The first is the duration case, where the log already says how long each
// alarm lasted. The second is the set and clear case, where each alarm appears
// as two rows that have to be paired.
const SCENARIOS = [
  {
    name: "duration log",
    csv: join(DATA, "sample_alarm_log.csv"),
    golden: join(DATA, "expected_summary.json"),
    mapping: {
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
    }
  },
  {
    name: "set and clear log",
    csv: join(DATA, "sample_setclear_log.csv"),
    golden: join(DATA, "expected_setclear.json"),
    mapping: {
      ts_set: "EventTime",
      fault_code: "AlarmID",
      description: "AlarmText",
      equipment: "ChamberID",
      downMode: "events",
      durCol: "",
      durScale: 1,
      stateCol: "EventState",
      setVal: "SET",
      clearVal: "CLEAR"
    }
  }
];

const problems = [];
let checks = 0;

/** Walk both objects together and record every value that does not match. */
function compare(actual, expected, path) {
  for (const key of Object.keys(expected)) {
    if (IGNORED_KEYS.has(key)) continue;
    const where = path ? path + "." + key : key;
    const exp = expected[key];
    const act = actual === undefined ? undefined : actual[key];

    if (exp !== null && typeof exp === "object" && !Array.isArray(exp)) {
      if (act === undefined) {
        problems.push(`${where}: the browser tool produced nothing here`);
        continue;
      }
      compare(act, exp, where);
      continue;
    }

    checks += 1;
    if (act === undefined) {
      problems.push(`${where}: expected ${JSON.stringify(exp)}, browser tool produced nothing`);
    } else if (!same(act, exp)) {
      problems.push(`${where}: expected ${JSON.stringify(exp)}, browser tool gave ${JSON.stringify(act)}`);
    }
  }
}

// Numbers are compared with a hair of tolerance. Everything else must be equal.
function same(a, b) {
  if (typeof a === "number" && typeof b === "number") return Math.abs(a - b) < 1e-6;
  return a === b;
}

// ---------------------------------------------------------------------------
// Check 1. The sample log baked into the HTML must match the sample log file.
// If these drift apart, the two tools are quietly analysing different data.
// ---------------------------------------------------------------------------
const normalize = (s) => s.replace(/\r\n/g, "\n").trim();
const fileSample = readFileSync(join(DATA, "sample_alarm_log.csv"), "utf8");

checks += 1;
if (normalize(fileSample) !== normalize(builtInSample())) {
  problems.push(
    "The SAMPLE_CSV baked into alarm_pareto.html no longer matches " +
    "tests/data/sample_alarm_log.csv. Update whichever one is out of date."
  );
}

// ---------------------------------------------------------------------------
// Check 2. Every scenario's numbers must match its golden file.
// ---------------------------------------------------------------------------
for (const scenario of SCENARIOS) {
  const expected = JSON.parse(readFileSync(scenario.golden, "utf8"));
  const text = readFileSync(scenario.csv, "utf8");
  const actual = summarize(text, expected.window.window_days, scenario.mapping);
  compare(actual, expected, scenario.name);
}

// ---------------------------------------------------------------------------
// Report.
// ---------------------------------------------------------------------------
if (problems.length) {
  console.error("Parity check FAILED. The browser tool disagrees with the golden numbers.\n");
  for (const p of problems) console.error("  - " + p);
  console.error(
    "\nWhat to do. If you changed the analysis on purpose, change it in both " +
    "tools, confirm the new numbers by hand, then update the golden file in " +
    "tests/data. If you did not mean to change the analysis, this is a real bug."
  );
  process.exit(1);
}

const names = SCENARIOS.map((s) => s.name).join(" and ");
console.log(`Parity check passed. ${checks} values agree across the ${names}.`);
