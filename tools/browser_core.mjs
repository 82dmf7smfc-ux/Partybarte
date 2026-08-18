// Load the analysis code out of alarm_pareto.html and make it callable here.
//
// Why this exists. The browser tool and the Python tool must give the same
// numbers for the same log. Nothing checked that before. This file lets a test
// run the real shipped browser code, so the check cannot drift out of date.
//
// How it works. We read the single <script> block out of the HTML, give it a
// small stand-in for the browser page, and run it. Nothing is copied or
// rewritten. If someone edits the math in the HTML, this picks up the edit.
//
// This runs on plain Node. It needs no packages and makes no network call.

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

const HERE = dirname(fileURLToPath(import.meta.url));
export const ROOT = join(HERE, "..");
export const HTML_PATH = join(ROOT, "alarm_pareto.html");

// A stand-in for the parts of a browser page the script touches while it loads.
// Every element answers to whatever the script asks of it and does nothing.
function makeFakeDocument() {
  const element = {
    value: "",
    innerHTML: "",
    style: {},
    files: [],
    addEventListener() {},
    appendChild() {},
    removeChild() {},
    setAttribute() {},
    click() {},
    querySelectorAll() { return []; }
  };
  return {
    getElementById() { return element; },
    createElement() { return element; },
    querySelectorAll() { return []; },
    addEventListener() {},
    body: element
  };
}

/** Return the text inside the one <script> block in the HTML file. */
export function extractScript(htmlPath = HTML_PATH) {
  const html = readFileSync(htmlPath, "utf8");
  const blocks = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)];
  if (blocks.length !== 1) {
    throw new Error(
      "Expected exactly one <script> block in " + htmlPath +
      ", found " + blocks.length + ". The browser tool must stay one file " +
      "with one script block so the parity check can read it."
    );
  }
  return blocks[0][1];
}

/**
 * Run the browser script and hand back its functions and variables.
 * The returned object is the script's global scope, so core.mergedSeconds,
 * core.rankLevel, core.SAMPLE_CSV and the rest are all reachable.
 */
export function loadBrowserCore(htmlPath = HTML_PATH) {
  const sandbox = {
    document: makeFakeDocument(),
    window: {},
    console,
    Date,
    Math,
    JSON,
    parseFloat,
    parseInt,
    isNaN,
    String,
    Number,
    Object,
    Array,
    URL: { createObjectURL() { return ""; }, revokeObjectURL() {} },
    Blob: function () {},
    FileReader: function () {}
  };
  sandbox.window = sandbox;
  const context = vm.createContext(sandbox);
  // "use strict" at the top of the script would hide its function declarations
  // from us, so we run the body without it and keep the declarations visible.
  const body = extractScript(htmlPath).replace(/^\s*"use strict";/, "");
  vm.runInContext(body, context, { filename: "alarm_pareto.html<script>" });
  return context;
}
