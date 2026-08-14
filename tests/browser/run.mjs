// Headless test harness for the browser tool (alarm_pareto.html).
//
// The browser tool has no build step, so we test it by driving a real headless
// Chromium and calling into it. It checks the pure data layer on window.AP and a
// couple of full-page flows. It uses only Node built-ins (the WebSocket that
// ships with Node 22 and the CDP protocol), so there is nothing to install.
//
// Chromium is found from CHROME_BIN, or by scanning /opt/pw-browsers, or in the
// usual system locations. In CI, the workflow sets CHROME_BIN.
//
// Run: node tests/browser/run.mjs   (exits non-zero if any check fails)

import { spawn } from "node:child_process";
import { readFileSync, readdirSync, existsSync, statSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve, join } from "node:path";
import http from "node:http";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, "..", "..");
const HTML_PATH = resolve(REPO, "alarm_pareto.html");
const FIX = join(HERE, "fixtures");
const PORT_NUM = 9401;

const p5000 = readFileSync(join(FIX, "p5000_sample.txt"), "utf8");
const csv = readFileSync(join(FIX, "delimited_sample.csv"), "utf8");

// --- Find a Chromium binary ------------------------------------------------
function findChrome() {
  if (process.env.CHROME_BIN && existsSync(process.env.CHROME_BIN)) return process.env.CHROME_BIN;
  // Scan the Playwright browser cache used in the dev sandbox.
  var pw = "/opt/pw-browsers";
  if (existsSync(pw)) {
    var dirs = readdirSync(pw).filter(function (d) { return /chromium/.test(d); });
    for (var i = 0; i < dirs.length; i++) {
      var a = join(pw, dirs[i], "chrome-linux", "headless_shell");
      var b = join(pw, dirs[i], "chrome-linux", "chrome");
      if (existsSync(a)) return a;
      if (existsSync(b)) return b;
    }
  }
  var common = [
    "/usr/bin/google-chrome", "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium", "/usr/bin/chromium-browser",
    "/snap/bin/chromium"
  ];
  for (var j = 0; j < common.length; j++) if (existsSync(common[j])) return common[j];
  throw new Error("No Chromium found. Set CHROME_BIN to a Chrome/Chromium binary.");
}

// --- Tiny assertion framework ----------------------------------------------
var passed = 0, failed = 0;
function check(name, cond, detail) {
  if (cond) { passed += 1; console.log("  ok   " + name); }
  else { failed += 1; console.log("  FAIL " + name + (detail !== undefined ? "  (" + JSON.stringify(detail) + ")" : "")); }
}
function eq(name, got, want) { check(name, got === want, { got: got, want: want }); }

// --- CDP plumbing ----------------------------------------------------------
const chrome = findChrome();
console.log("Chromium: " + chrome);
console.log("Page:     " + HTML_PATH);
const proc = spawn(chrome, [
  "--headless", "--disable-gpu", "--no-sandbox",
  "--remote-debugging-port=" + PORT_NUM, "--remote-allow-origins=*",
  "file://" + HTML_PATH
]);
proc.on("error", function (e) { console.error("Failed to launch Chromium: " + e.message); process.exit(2); });

function getJSON(path) {
  return new Promise(function (res, rej) {
    http.get({ host: "127.0.0.1", port: PORT_NUM, path: path }, function (r) {
      var d = ""; r.on("data", function (c) { d += c; }); r.on("end", function () { res(JSON.parse(d)); });
    }).on("error", rej);
  });
}
async function waitTarget() {
  for (var i = 0; i < 80; i++) {
    try {
      var list = await getJSON("/json");
      var page = list.find(function (t) { return t.type === "page" && t.webSocketDebuggerUrl; });
      if (page) return page;
    } catch (e) {}
    await new Promise(function (r) { setTimeout(r, 150); });
  }
  throw new Error("Chromium debugger target never appeared");
}

async function main() {
  const page = await waitTarget();
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise(function (r) { ws.onopen = r; });
  var id = 0; var pending = new Map();
  ws.onmessage = function (e) { var m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } };
  function send(method, params) {
    return new Promise(function (res) { var i = ++id; pending.set(i, res); ws.send(JSON.stringify({ id: i, method: method, params: params || {} })); });
  }
  async function ev(expr) {
    var r = await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true });
    if (r.result && r.result.exceptionDetails) throw new Error("Page error: " + JSON.stringify(r.result.exceptionDetails));
    return r.result.result.value;
  }

  await send("Runtime.enable");
  await new Promise(function (r) { setTimeout(r, 400); });
  await ev("window.__p = " + JSON.stringify(p5000) + "; window.__csv = " + JSON.stringify(csv) + "; true");

  // 1. window.AP exists and is populated.
  var apKeys = await ev("Object.keys(window.AP || {}).length");
  check("window.AP exposed", apKeys > 10, { keys: apKeys });

  // 2. 2-digit year handling.
  var yr = await ev("[AP.expandYear(26), AP.expandYear(68), AP.expandYear(69), AP.expandYear(99)]");
  check("expandYear pivot", yr[0] === 2026 && yr[1] === 2068 && yr[2] === 1969 && yr[3] === 1999, yr);
  var pd = await ev("(function(){var d=AP.parseDate('08/07/26 12:50:16');return [d.getFullYear(),d.getMonth(),d.getDate(),d.getHours()];})()");
  check("parseDate MM/DD/YY", pd[0] === 2026 && pd[1] === 7 && pd[2] === 7 && pd[3] === 12, pd);

  // 3. Format detection.
  eq("detectFormat p5000", await ev("AP.detectFormat(window.__p)"), "p5000");
  eq("detectFormat delimited", await ev("AP.detectFormat(window.__csv)"), "delimited");

  // 4. P5000 parser output.
  var pk = await ev("(function(){AP.resetDebug();var r=AP.parseP5000Block(window.__p,'fix');var codes=AP.getDebug().order.slice();var internal=r.rows.filter(function(x){return x.c4.indexOf('total number=')>=0;})[0];var cont=r.rows.filter(function(x){return x.c2==='736';})[0];var unreg=codes.filter(function(c){return !AP.DEBUG_CODES[c];});return {labels:r.columns.map(function(c){return c.label;}),rowCount:r.rows.length,firstChamber:r.rows[0].c5,internalDesc:internal?internal.c4:null,contDesc:cont?cont.c4:null,codes:codes,unregistered:unreg};})()");
  check("P5000 columns", pk.labels.join(",") === "Date,Time,Event Number,Event Type,Description,Chamber", pk.labels);
  eq("P5000 row count", pk.rowCount, 12);
  eq("P5000 chamber extracted", pk.firstChamber, "S4EXT");
  check("P5000 keeps inner spaces", pk.internalDesc && pk.internalDesc.indexOf("<L1>   log") >= 0, pk.internalDesc);
  check("P5000 rejoins continuation", pk.contDesc && /wrapped by the editor$/.test(pk.contDesc), pk.contDesc);
  check("P5000 debug has ROW-NOMATCH", pk.codes.indexOf("ROW-NOMATCH") >= 0, pk.codes);
  check("P5000 debug has ROW-CONT", pk.codes.indexOf("ROW-CONT") >= 0, pk.codes);
  check("all debug codes are registered", pk.unregistered.length === 0, pk.unregistered);

  // 5. Chamber extraction rules.
  var ch = await ev("[AP.extractChamber('chamber <S4EXT> abcd'), AP.extractChamber('port <S1EXT> x'), AP.extractChamber('wafer <S1> of lot <S3>'), AP.extractChamber('no tag here')]");
  check("extractChamber rules", ch[0] === "S4EXT" && ch[1] === "S1EXT" && ch[2] === "" && ch[3] === "", ch);

  // 6. Full-page P5000 flow: load, auto-map, analyze.
  var flow = await ev("(function(){document.getElementById('formatSel').value='auto';loadTexts([window.__p],1);function role(lbl){for(var i=0;i<STATE.columns.length;i++){if(STATE.columns[i].label===lbl){var s=document.getElementById('colid_'+STATE.columns[i].key);return s?s.value:'?';}}return '?';}document.getElementById('downMode').value='none';runAnalysis();var R=STATE.lastResult;return {rows:STATE.rows.length,sevRole:role('Event Type'),chamberRole:role('Chamber'),total:R.totalFaults,topFault:R.levels.fault_code.byCount[0].key,topModule:R.levels.equipment.byCount[0].key};})()");
  eq("full flow: rows parsed", flow.rows, 12);
  eq("full flow: Event Type -> severity", flow.sevRole, "severity");
  eq("full flow: Chamber -> equipment", flow.chamberRole, "equipment");
  eq("full flow: kept after severity filter", flow.total, 8);
  eq("full flow: top fault", flow.topFault, "494");
  eq("full flow: top module", flow.topModule, "S4EXT");

  // 6b. Message categorization.
  var cat = await ev("(function(){"
    + "var a=AP.categorize('chamber <S4EXT> ... has reached the pm trigger time');"
    + "var b=AP.categorize('chamber <S4EXT> chamber minimum gas flow error');"
    + "var c=AP.categorize('some brand new message 12345 <Z9>');"
    + "var rules=AP.parseCatRules(['pm trigger => Custom PM']);"
    + "var d=AP.categorize('has reached the pm trigger time', rules);"
    + "var bad=[]; AP.resetDebug(); AP.parseCatRules(['(unclosed => Oops']); var codes=AP.getDebug().order.slice();"
    + "return {pm:a, gas:b, novel:c, override:d, norm:AP.normCategory('Chamber <S4EXT> step <L2> at 12:00'), badRuleCode:codes.indexOf('CAT-BADRULE')>=0};"
    + "})()");
  check("categorize built-in PM", cat.pm.matched === true && cat.pm.category === "PM trigger reached", cat.pm);
  check("categorize built-in gas flow", cat.gas.matched === true && cat.gas.category === "Gas flow error", cat.gas);
  check("categorize unmatched falls back", cat.novel.matched === false && cat.novel.category.indexOf("#") >= 0, cat.novel);
  check("categorize user rule wins", cat.override.matched === true && cat.override.category === "Custom PM", cat.override);
  check("normCategory collapses tags and numbers", cat.norm === "chamber <*> step <*> at #:#", cat.norm);
  check("parseCatRules bad regex -> CAT-BADRULE", cat.badRuleCode === true, cat);

  // 6c. Category is a Pareto level, and the P5000 sample rolls up correctly.
  var lvl = await ev("(function(){"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__p],1);"
    + "document.getElementById('downMode').value='none';runAnalysis();"
    + "var R=STATE.lastResult;"
    + "var hasCat=!!R.levels.category;"
    + "var top=hasCat?R.levels.category.byCount[0]:null;"
    + "var tabs=Array.prototype.map.call(document.querySelectorAll('#levelTabs button'),function(b){return b.textContent;});"
    + "return {hasCat:hasCat, topKey:top?top.key:null, topCount:top?top.count:null, tabs:tabs};"
    + "})()");
  check("Category is a level", lvl.hasCat, lvl);
  check("Category tab present", lvl.tabs.indexOf("Category") >= 0, lvl.tabs);
  check("Category top is PM trigger reached", lvl.topKey === "PM trigger reached", lvl);
  eq("Category top count (5 PM warnings kept)", lvl.topCount, 5);

  // 6d. Analytics: analyzeStats on a deterministic fixture.
  // 10 events over Jan 1-5 2026: 6 on day 1 (a burst), 1 each on days 2-5.
  // Chambers A (7) and B (3); categories PM (6) and Gas (4).
  var st = await ev("(function(){"
    + "function mk(da,ho,eq,cat){return {start:new Date(2026,0,da,ho,0,0),equipment:eq,category:cat,fault_code:cat,severity:'FAULT',durSec:0};}"
    + "var occ=[mk(1,0,'A','PM'),mk(1,1,'A','PM'),mk(1,2,'A','PM'),mk(1,3,'A','PM'),mk(1,4,'B','Gas'),mk(1,5,'B','Gas'),mk(2,0,'A','PM'),mk(3,0,'A','Gas'),mk(4,0,'B','Gas'),mk(5,0,'A','PM')];"
    + "var S=AP.analyzeStats(occ,new Date(2026,0,1),new Date(2026,0,5));"
    + "return {total:S.total,perDay:S.perDay,busyDay:S.busiestDay.day,busyCount:S.busiestDay.count,mtbf:S.mtbfSec,burst:S.burstFactor,catTop80:S.concentration.category.top80,catTopKey:S.concentration.category.topKey,catTopShare:S.concentration.category.topShare,eq0:S.perChamber[0].key,eq0n:S.perChamber[0].count,eq0share:S.perChamber[0].share,days:S.byDay.length};"
    + "})()");
  eq("stats: total", st.total, 10);
  eq("stats: events per day", st.perDay, 2.5);
  eq("stats: busiest day", st.busyDay, "2026-01-01");
  eq("stats: busiest day count", st.busyCount, 6);
  eq("stats: mean gap seconds", st.mtbf, 38400);
  check("stats: burst factor ~2.4", Math.abs(st.burst - 2.4) < 1e-9, st.burst);
  eq("stats: category top-80 count", st.catTop80, 2);
  eq("stats: top category key", st.catTopKey, "PM");
  check("stats: top category share 0.6", Math.abs(st.catTopShare - 0.6) < 1e-9, st.catTopShare);
  eq("stats: top chamber key", st.eq0, "A");
  eq("stats: top chamber count", st.eq0n, 7);
  eq("stats: byDay length", st.days, 5);

  // 6e. Insights card renders on the P5000 sample.
  var ins = await ev("(function(){"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__p],1);"
    + "document.getElementById('downMode').value='none';runAnalysis();"
    + "var vis=document.getElementById('insightsCard').style.display!=='none';"
    + "var tiles=document.querySelectorAll('#insightCards .stat').length;"
    + "var bars=document.querySelectorAll('#perDayChart svg rect').length;"
    + "var chamberRows=document.querySelectorAll('#chamberTable tr').length;"
    + "return {vis:vis,tiles:tiles,bars:bars,chamberRows:chamberRows,hasStats:!!STATE.lastResult.stats};"
    + "})()");
  check("insights: card visible", ins.vis, ins);
  check("insights: stat tiles rendered", ins.tiles >= 4, ins);
  check("insights: day bars rendered", ins.bars >= 1, ins);
  check("insights: chamber table has rows", ins.chamberRows >= 2, ins);

  // 7. Regression: the delimited path still works.
  var reg = await ev("(function(){document.getElementById('formatSel').value='auto';loadTexts([SAMPLE_CSV],1);return {rows:STATE.rows.length,hasAlarmId:STATE.columns.some(function(c){return c.label==='AlarmID';})};})()");
  eq("regression: built-in CSV rows", reg.rows, 15);
  check("regression: CSV headers read", reg.hasAlarmId, reg);

  ws.close();
  proc.kill("SIGKILL");

  console.log("\n" + passed + " passed, " + failed + " failed");
  process.exit(failed ? 1 : 0);
}

main().catch(function (e) {
  console.error("Harness error: " + (e && e.stack ? e.stack : e));
  try { proc.kill("SIGKILL"); } catch (x) {}
  process.exit(2);
});
