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
  var pk = await ev("(function(){AP.resetDebug();var r=AP.parseP5000Block(window.__p,'fix');var codes=AP.getDebug().order.slice();var internal=r.rows.filter(function(x){return x.c4.indexOf('total number=')>=0;})[0];var cont=r.rows.filter(function(x){return x.c2==='736';})[0];var unreg=codes.filter(function(c){return !AP.DEBUG_CODES[c];});return {labels:r.columns.map(function(c){return c.label;}),rowCount:r.rows.length,firstChamber:r.rows[0].c5,firstTool:r.rows[0].c6,tool:r.tool,kind:r.kind,internalDesc:internal?internal.c4:null,contDesc:cont?cont.c4:null,codes:codes,unregistered:unreg};})()");
  check("P5000 columns", pk.labels.join(",") === "Date,Time,Event Number,Event Type,Description,Chamber,Tool", pk.labels);
  eq("P5000 row count", pk.rowCount, 12);
  eq("P5000 chamber extracted", pk.firstChamber, "S4EXT");
  eq("P5000 tool detected", pk.tool, "dep1");
  eq("P5000 tool kind", pk.kind, "dep");
  eq("P5000 tool column tagged on row", pk.firstTool, "dep1");
  check("P5000 keeps inner spaces", pk.internalDesc && pk.internalDesc.indexOf("<L1>   log") >= 0, pk.internalDesc);
  check("P5000 rejoins continuation", pk.contDesc && /wrapped by the editor$/.test(pk.contDesc), pk.contDesc);
  check("P5000 debug has ROW-NOMATCH", pk.codes.indexOf("ROW-NOMATCH") >= 0, pk.codes);
  check("P5000 debug has ROW-CONT", pk.codes.indexOf("ROW-CONT") >= 0, pk.codes);
  check("all debug codes are registered", pk.unregistered.length === 0, pk.unregistered);

  // 5. Chamber extraction rules.
  var ch = await ev("[AP.extractChamber('chamber <S4EXT> abcd'), AP.extractChamber('port <S1EXT> x'), AP.extractChamber('wafer <S1> of lot <S3>'), AP.extractChamber('no tag here')]");
  check("extractChamber rules", ch[0] === "S4EXT" && ch[1] === "S1EXT" && ch[2] === "" && ch[3] === "", ch);

  // 6. Full-page P5000 flow: load, auto-map, analyze.
  var flow = await ev("(function(){document.getElementById('formatSel').value='auto';loadTexts([window.__p],1);function role(lbl){for(var i=0;i<STATE.columns.length;i++){if(STATE.columns[i].label===lbl){var s=document.getElementById('colid_'+STATE.columns[i].key);return s?s.value:'?';}}return '?';}document.getElementById('downMode').value='none';runAnalysis();var R=STATE.lastResult;return {rows:STATE.rows.length,sevRole:role('Event Type'),chamberRole:role('Chamber'),toolRole:role('Tool'),total:R.totalFaults,topFault:R.levels.fault_code.byCount[0].key,topModule:R.levels.equipment.byCount[0].key,topTool:R.levels.tool?R.levels.tool.byCount[0].key:null};})()");
  eq("full flow: rows parsed", flow.rows, 12);
  eq("full flow: Event Type -> severity", flow.sevRole, "severity");
  eq("full flow: Chamber -> equipment", flow.chamberRole, "equipment");
  eq("full flow: Tool -> tool", flow.toolRole, "tool");
  eq("full flow: kept after severity filter", flow.total, 8);
  eq("full flow: top fault", flow.topFault, "494");
  eq("full flow: top module", flow.topModule, "S4EXT");
  eq("full flow: Tool level top is dep1", flow.topTool, "dep1");

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

  // 6b-etch. The etch4 vocabulary rules, including ordering (lot before wafer).
  var ecat = await ev("(function(){function c(s){return AP.categorize(s).category;}return {"
    + "lot:c('chamber <S4EXT> lot processing complete for cassette <L1>'),"
    + "wafer:c('processing complete for wafer <S1> of lot <S3>'),"
    + "pumpMotor:c('chamber <S1EXT> pump motor error detected'),"
    + "pumpN2:c('chamber <S1EXT> pump is running without n2 purge'),"
    + "vent:c('chamber <S4EXT> completed vent service cycle'),"
    + "mfc:c('remote mfc <L1> autofill in progress'),"
    + "access:c('access changed to user engineer'),"
    + "fwd:c('chamber <S4EXT> rfu forward power error'),"
    + "xep:c('func_string xep_evt_127_str reported'),"
    + "cassette:c('robot is ready to send the cassette to the loadlock'),"
    + "allWafers:c('chamber <S4EXT> has all wafers completed')"
    + "};})()");
  eq("categorize lot processing (before wafer)", ecat.lot, "Lot processing complete");
  eq("categorize wafer processing still works", ecat.wafer, "Wafer processing complete");
  eq("categorize pump motor error", ecat.pumpMotor, "Pump motor error");
  eq("categorize pump without N2", ecat.pumpN2, "Pump running without N2");
  eq("categorize vent complete", ecat.vent, "Vent complete");
  eq("categorize remote MFC autofill", ecat.mfc, "Remote MFC autofill");
  eq("categorize access changed", ecat.access, "Access level changed");
  eq("categorize RF forward power error", ecat.fwd, "RF forward power error");
  eq("categorize XEP event string", ecat.xep, "Event string (XEP)");
  eq("categorize ready to send cassette", ecat.cassette, "Ready to send cassette");
  eq("categorize all wafers completed", ecat.allWafers, "All wafers completed");
  check("categorize unmatched falls back to readable label", cat.novel.matched === false && cat.novel.category === "Some brand new message", cat.novel);
  check("categorize user rule wins", cat.override.matched === true && cat.override.category === "Custom PM", cat.override);
  check("normCategory collapses tags and numbers", cat.norm === "step at # #", cat.norm);
  check("parseCatRules bad regex -> CAT-BADRULE", cat.badRuleCode === true, cat);

  // 6b-id. ID-based category rules: parse `id:` lines and match by Event Number.
  var idr = await ev("(function(){"
    + "var rules=AP.parseCatRules(['id:494,807 => Known IDs','gas flow => Text Cat']);"
    + "var idRule=rules.filter(function(r){return r.ids;})[0];"
    + "var byId=AP.categorize('any text at all', rules, '494');"          // matches ID rule
    + "var byId2=AP.categorize('unrelated', rules, '807');"
    + "var miss=AP.categorize('nothing here', rules, '999');"            // no ID, no text -> auto
    + "var textStill=AP.categorize('chamber minimum gas flow error', rules, '999');" // text rule still works
    + "var idBeatsText=AP.categorize('chamber minimum gas flow error', rules, '494');" // ID rule listed first wins
    + "var noId=AP.categorize('any text at all', rules);"                // id omitted -> ID rule cannot fire
    + "return {ids:idRule?Object.keys(idRule.ids).sort():null, byId:byId, byId2:byId2, miss:miss, textStill:textStill, idBeats:idBeatsText, noId:noId};"
    + "})()");
  check("parseCatRules reads id: list", idr.ids && idr.ids.join(",") === "494,807", idr.ids);
  check("categorize by ID matches", idr.byId.matched === true && idr.byId.category === "Known IDs" && /ID rule/.test(idr.byId.source), idr.byId);
  eq("categorize by ID (second id in list)", idr.byId2.category, "Known IDs");
  check("categorize unknown ID falls through to auto", idr.miss.matched === false, idr.miss);
  eq("categorize text rule still fires without ID match", idr.textStill.category, "Text Cat");
  eq("categorize ID rule beats later text rule", idr.idBeats.category, "Known IDs");
  check("categorize ID rule inert when id omitted", idr.noId.matched === false, idr.noId);

  // 6b-idroll. rollupById and the uncategorized-ID worklist.
  var idroll = await ev("(function(){"
    + "var list=["
    + "{id:'901',sev:'TRACE',desc:'processing complete for wafer <S1> of lot <S3>'},"
    + "{id:'901',sev:'TRACE',desc:'processing complete for wafer <S2> of lot <S4>'},"      // same shape, diff numbers
    + "{id:'901',sev:'TRACE',desc:'processing complete for wafer <S5> of lot <S6>'},"      // still same shape
    + "{id:'570',sev:'PROMPT',desc:'port <S1EXT> wafer not sensed by vacuum'},"
    + "{id:'050',sev:'TRACE',desc:'front panel func_char a depressed'},"
    + "{id:'050',sev:'TRACE',desc:'front panel totally different free text here now'}"     // two distinct shapes
    + "];"
    + "var roll=AP.rollupById(list);"
    + "var top=roll[0];"
    + "var fp=roll.filter(function(r){return r.id==='050';})[0];"
    + "return {topId:top.id, topCount:top.count, topShapes:top.shapes, fpShapes:fp.shapes, n:roll.length};"
    + "})()");
  eq("rollupById ranks most common ID first", idroll.topId, "901");
  eq("rollupById counts occurrences", idroll.topCount, 3);
  eq("rollupById collapses same-shape variants to 1 shape", idroll.topShapes, 1);
  eq("rollupById counts distinct shapes for mixed ID", idroll.fpShapes, 2);
  eq("rollupById distinct IDs", idroll.n, 3);

  // 6b-idreport. Full-page: after an analysis, the worklist lists uncategorized IDs
  // (the standard fixture is fully categorized, so use an inline log with novel IDs)
  // and an id: rule removes one ID from the worklist while the other stays.
  var idrep = await ev("(function(){"
    + "var log='System type:  P5000\\nProcess type: Etch\\n   SCIII+ Event Data File:  E:\\\\Backups\\\\dep1\\\\Data\\\\ELOG.DAT\\nDate  Time  Event Number  Event Type  Description\\n"
    + "08/07/26  12:00:00  611  FAULT  chamber <S4EXT> zzz brand new widget alpha jam\\n"
    + "08/07/26  12:01:00  611  FAULT  chamber <S4EXT> zzz brand new widget beta jam\\n"
    + "08/07/26  12:02:00  622  FAULT  totally novel gizmo condition observed\\n';"
    + "document.getElementById('formatSel').value='auto';loadTexts([log],1);"
    + "document.getElementById('catRules').value='';document.getElementById('downMode').value='none';"
    + "document.querySelectorAll('.sevchk').forEach(function(c){c.checked=true;});"
    + "runAnalysis();"
    + "var before=uncategorizedIdReport(100);"
    + "var had611=/\\n\\s*611\\s+x2\\s/.test(before);"
    + "var had622=/\\n\\s*622\\s+x1\\s/.test(before);"
    + "document.getElementById('catRules').value='id:611 => Widget jam';"
    + "runAnalysis();"
    + "var after=uncategorizedIdReport(100);"
    + "return {had611:had611, had622:had622, still611:/\\n\\s*611\\s+x/.test(after), still622:/\\n\\s*622\\s+x/.test(after), headerHasTop:/Uncategorized event IDs \\(top/.test(before)};"
    + "})()");
  check("worklist header present", idrep.headerHasTop, idrep);
  check("worklist lists uncategorized ID 611 with count", idrep.had611, idrep);
  check("worklist lists uncategorized ID 622 with count", idrep.had622, idrep);
  check("id: rule removes ID 611 from the worklist", idrep.still611 === false, idrep);
  check("unrelated ID 622 stays on the worklist", idrep.still622 === true, idrep);

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

  // 6f. Filtering: applyFilters over a small occurrence set.
  var flt = await ev("(function(){"
    + "function mk(da,eq,cat,desc){return {start:new Date(2026,0,da,0,0,0),equipment:eq,category:cat,description:desc,durSec:0};}"
    + "var occ=[mk(1,'A','PM','pm trigger reached'),mk(2,'B','Gas','gas flow error'),mk(3,'A','PM','pm trigger reached'),mk(4,'C','Cal','calibration not done')];"
    + "var byChamber=AP.applyFilters(occ,{chambers:{A:true}});"
    + "var byCat=AP.applyFilters(occ,{categories:{PM:true,Gas:true}});"
    + "var byDate=AP.applyFilters(occ,{dateStart:new Date(2026,0,2),dateEnd:new Date(2026,0,3,23,59,59)});"
    + "var bySearch=AP.applyFilters(occ,{searchText:'gas'});"
    + "var byRe=AP.applyFilters(occ,{searchRe:/pm|cal/i});"
    + "return {all:occ.length,chamber:byChamber.length,cat:byCat.length,date:byDate.length,search:bySearch.length,re:byRe.length};"
    + "})()");
  eq("filter: base count", flt.all, 4);
  eq("filter: by chamber A", flt.chamber, 2);
  eq("filter: by category PM+Gas", flt.cat, 3);
  eq("filter: by date range", flt.date, 2);
  eq("filter: by search text", flt.search, 1);
  eq("filter: by regex", flt.re, 3);

  // 6g. Full-page: a chamber filter narrows the P5000 analysis, and min-count folds.
  var ff = await ev("(function(){"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__p],1);"
    + "document.getElementById('downMode').value='none';"
    + "document.querySelectorAll('.sevchk').forEach(function(c){c.checked=true;});"       // include all severities
    + "document.querySelectorAll('.chamberchk').forEach(function(c){c.checked=(c.value==='S4EXT');});"
    + "runAnalysis();"
    + "var only=STATE.lastResult.kept.every(function(o){return o.equipment==='S4EXT';});"
    + "var note=document.getElementById('summaryMsg').innerText;"
    + "var hasChamberBoxes=document.querySelectorAll('.chamberchk').length>0;"
    + "return {kept:STATE.lastResult.totalFaults, onlyS4:only, hasChamberBoxes:hasChamberBoxes, note:note};"
    + "})()");
  check("filter UI: chamber checkboxes built", ff.hasChamberBoxes, ff);
  check("filter UI: only S4EXT kept", ff.onlyS4 && ff.kept > 0, ff);
  check("filter UI: filter note shown", /after the filters/.test(ff.note), ff.note);

  // 6g-tool. Two tools in one batch: the Tool filter narrows to one, and the
  // Tool Pareto level counts per tool.
  var tf = await ev("(function(){"
    + "var etch='System type:  P5000\\nProcess type: Etch\\n   SCIII+ Event Data File:  E:\\\\Backups\\\\etch4\\\\Data\\\\ELOG.DAT\\nDate  Time  Event Number  Event Type  Description\\n"
    + "08/07/26  12:00:00  807  FAULT  chamber <S2EXT> chamber minimum gas flow error\\n"
    + "08/07/26  12:01:00  807  FAULT  chamber <S2EXT> chamber minimum gas flow error\\n';"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__p, etch],2);"
    + "document.getElementById('downMode').value='none';"
    + "document.querySelectorAll('.sevchk').forEach(function(c){c.checked=true;});"
    + "var toolVals=Array.prototype.map.call(document.querySelectorAll('.toolchk'),function(c){return c.value;}).sort();"
    + "var hasToolBoxes=document.querySelectorAll('.toolchk').length>0;"
    + "runAnalysis();"
    + "var toolLevel=STATE.lastResult.levels.tool.byCount.map(function(x){return x.key+':'+x.count;}).sort();"
    + "document.querySelectorAll('.toolchk').forEach(function(c){c.checked=(c.value==='etch4');});"
    + "runAnalysis();"
    + "var onlyEtch=STATE.lastResult.kept.every(function(o){return o.tool==='etch4';});"
    + "var keptEtch=STATE.lastResult.totalFaults;"
    + "return {toolVals:toolVals, hasToolBoxes:hasToolBoxes, toolLevel:toolLevel, onlyEtch:onlyEtch, keptEtch:keptEtch};"
    + "})()");
  check("filter UI: tool checkboxes built (dep1, etch4)", tf.hasToolBoxes && tf.toolVals.join(",") === "dep1,etch4", tf.toolVals);
  check("Tool level counts both tools", tf.toolLevel.indexOf("dep1:12") >= 0 && tf.toolLevel.indexOf("etch4:2") >= 0, tf.toolLevel);
  check("Tool filter narrows to etch4", tf.onlyEtch && tf.keptEtch === 2, tf);

  // 6h. min-count floor folds small groups into Other.
  var mc = await ev("(function(){"
    + "function mk(eq){return {start:new Date(2026,0,1,0,0,0),equipment:eq,category:'c',fault_code:eq,description:'d',durSec:0};}"
    + "var occ=[mk('A'),mk('A'),mk('A'),mk('B')];"           // A x3, B x1
    + "var r=AP.rankLevel(occ,'equipment','attributed',15,2);"  // minCount 2 -> B folds to Other
    + "var keys=r.byCount.map(function(x){return x.key;});"
    + "return {keys:keys};"
    + "})()");
  check("min-count: small group folded to Other", mc.keys.indexOf("B") === -1 && mc.keys.indexOf("Other") >= 0, mc.keys);

  // 6i. Charts: heatmapBins bins by weekday and hour.
  var hb = await ev("(function(){"
    + "var occ=[{start:new Date(2026,0,1,9,0,0)},{start:new Date(2026,0,1,9,30,0)},{start:new Date(2026,0,2,14,0,0)}];"  // Jan 1 2026 = Thursday (getDay 4)
    + "var b=AP.heatmapBins(occ);"
    + "return {total:b.total,max:b.max,thu9:b.matrix[4][9],fri14:b.matrix[5][14],empty:b.matrix[0][0],rows:b.matrix.length,cols:b.matrix[0].length};"
    + "})()");
  eq("heatmap: total", hb.total, 3);
  eq("heatmap: max cell", hb.max, 2);
  eq("heatmap: Thu 09:00 has 2", hb.thu9, 2);
  eq("heatmap: Fri 14:00 has 1", hb.fri14, 1);
  eq("heatmap: empty cell 0", hb.empty, 0);
  check("heatmap: 7x24 grid", hb.rows === 7 && hb.cols === 24, hb);

  // 6j. Chart-type switch renders each chart on the P5000 sample.
  var ch = await ev("(function(){"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__p],1);"
    + "document.getElementById('downMode').value='none';runAnalysis();"
    + "function bars(){return document.querySelectorAll('#countChart svg rect').length;}"
    + "document.getElementById('chartType').value='pareto';renderLevel();var pareto=document.querySelectorAll('#countChart svg polyline').length;"
    + "document.getElementById('chartType').value='hbar';renderLevel();var hbar=bars();"
    + "document.getElementById('logScale').checked=true;renderLevel();var hbarLog=bars();"
    + "document.getElementById('chartType').value='heatmap';document.getElementById('logScale').checked=false;renderLevel();"
    + "var cells=document.querySelectorAll('#countChart svg rect').length;var downEmpty=document.getElementById('downChart').innerHTML==='';"
    + "return {paretoLine:pareto,hbar:hbar,hbarLog:hbarLog,heatCells:cells,downEmpty:downEmpty};"
    + "})()");
  check("chart: pareto has cumulative line", ch.paretoLine >= 1, ch);
  check("chart: horizontal bars render", ch.hbar >= 1, ch);
  check("chart: log scale still renders bars", ch.hbarLog >= 1, ch);
  check("chart: heatmap renders 168 cells", ch.heatCells === 168, ch);
  check("chart: heatmap clears downtime panel", ch.downEmpty, ch);

  // 6k. Unknown-events helpers: rollupByShape and suggestRule (pure).
  var uk = await ev("(function(){"
    + "var ru=AP.rollupByShape(['chamber <S4EXT> abc 12','chamber <S1EXT> abc 99','totally other thing'],10);"
    + "var sr=AP.suggestRule('system reboot time down <L2> minutes, system wafer count <L1>');"
    + "return {topShape:ru[0].shape,topCount:ru[0].count,topPct:Math.round(ru[0].pct),groups:ru.length,pat:sr.pattern,lab:sr.label};"
    + "})()");
  eq("rollup: top shape", uk.topShape, "abc #");
  eq("rollup: top count", uk.topCount, 2);
  eq("rollup: top pct ~67", uk.topPct, 67);
  eq("rollup: distinct shapes", uk.groups, 2);
  eq("suggestRule: pattern", uk.pat, "system reboot time down minutes");
  eq("suggestRule: label", uk.lab, "System reboot time down minutes");

  // 6l. Full-page: Unknown panel + Add rule, using a mini P5000 with a message
  // that matches no built-in rule so there is always an uncategorized shape.
  await ev("window.__mini = 'System type:  P5000\\nDate  Time  Event Number  Event Type  Description\\n08/07/26  12:00:00  494  FAULT  zzz completely novel widget malfunction alpha\\n'; true");
  var up = await ev("(function(){"
    + "document.getElementById('catRules').value='';"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__mini],1);"
    + "document.getElementById('downMode').value='none';"
    + "document.querySelectorAll('.sevchk').forEach(function(c){c.checked=true;});"
    + "document.getElementById('systemBucket').checked=false;"
    + "runAnalysis();"
    + "var vis=document.getElementById('unknownCard').style.display!=='none';"
    + "var addBtns=document.querySelectorAll('#unkCatTable .addrule').length;"
    + "var before=document.getElementById('catRules').value;"
    + "if(addBtns) document.querySelector('#unkCatTable .addrule').click();"
    + "var after=document.getElementById('catRules').value;"
    + "var verbose=debugReport(true);"
    + "return {vis:vis,addBtns:addBtns,grew:after.length>before.length,hasArrow:/=>/.test(after),rule:after,verboseHasShapes:/Uncategorized message shapes|No-chamber event shapes/.test(verbose)};"
    + "})()");
  check("unknown: panel visible", up.vis, up);
  check("unknown: add-rule buttons present", up.addBtns >= 1, up);
  check("unknown: Add rule appended a rule", up.grew && up.hasArrow, up);
  check("unknown: appended rule is readable", /zzz completely novel widget/.test(up.rule), up.rule);
  check("verbose report includes shape rollups", up.verboseHasShapes, up);

  // 6m. Category-first default, "Matched by" source, and category metrics.
  var m6 = await ev("(function(){"
    + "document.getElementById('catRules').value='';"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__p],1);"
    + "document.getElementById('downMode').value='none';"
    + "document.querySelectorAll('.sevchk').forEach(function(c){c.checked=true;});"
    + "runAnalysis();"
    + "var activeTab=(document.querySelector('#levelTabs button.active')||{}).textContent;"
    + "var hasMatchedBy=/Matched by/.test(document.getElementById('resultTable').innerHTML);"
    + "var pm=STATE.lastResult.catSources['PM trigger reached']||'';"
    + "var metrics=debugReport(false);"
    + "return {active:activeTab, hasMatchedBy:hasMatchedBy, pmSource:pm, metricsHasCat:/Category metrics/.test(metrics), metricsHasCoverage:/categorized \\d+ of/.test(metrics)};"
    + "})()");
  eq("default level is Category", m6.active, "Category");
  check("Category table has Matched by column", m6.hasMatchedBy, m6);
  check("PM category source is built-in", /built-in/.test(m6.pmSource), m6);
  check("debug report has Category metrics", m6.metricsHasCat && m6.metricsHasCoverage, m6);

  // 6n. Subsystem-name mapping: a tag-less 'front panel' event becomes a module.
  var subm = await ev("(function(){"
    + "window.__mini2='System type:  P5000\\nDate  Time  Event Number  Event Type  Description\\n08/07/26  12:00:00  050  FAULT  front panel func_char depressed\\n';"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__mini2],1);"
    + "document.getElementById('downMode').value='none';"
    + "document.querySelectorAll('.sevchk').forEach(function(c){c.checked=true;});"
    + "runAnalysis();"
    + "var eqs=STATE.lastResult.kept.map(function(o){return o.equipment;});"
    + "return {eqs:eqs};"
    + "})()");
  check("subsystem mapping: front panel -> Front Panel module", subm.eqs.indexOf("Front Panel") >= 0, subm);

  var sysb = await ev("(function(){"
    + "document.getElementById('catRules').value='';"                            // clear rule added above
    + "document.getElementById('systemBucket').checked=true;"                     // set before load so the filter builds with 'System'
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__p],1);"
    + "document.getElementById('downMode').value='none';"
    + "document.querySelectorAll('.sevchk').forEach(function(c){c.checked=true;});"
    + "runAnalysis();"
    + "var eqs=STATE.lastResult.kept.map(function(o){return o.equipment;});"
    + "return {hasSystem:eqs.indexOf('System')>=0,noUnknown:eqs.indexOf('(unknown)')===-1};"
    + "})()");
  check("system bucket: tag-less events labeled System", sysb.hasSystem, sysb);
  check("system bucket: no (unknown) left", sysb.noUnknown, sysb);

  // 6o. Verbose debug box auto-expands so a screenshot captures the whole report.
  var dbgBox = await ev("(function(){"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__p],1);runAnalysis();"
    + "document.getElementById('debugVerbose').checked=false;"
    + "var card=document.getElementById('debugCard');"
    + "if(card.style.display==='none') document.getElementById('debugToggle').click();"
    + "var compact=document.getElementById('debugPre').style.maxHeight;"
    + "document.getElementById('debugVerbose').checked=true;document.getElementById('debugVerbose').dispatchEvent(new Event('change'));"
    + "var expanded=document.getElementById('debugPre').style.maxHeight;"
    + "return {compact:compact, expanded:expanded};"
    + "})()");
  eq("debug box compact height when not verbose", dbgBox.compact, "340px");
  eq("verbose debug box auto-expands", dbgBox.expanded, "none");

  // 7. Regression: the delimited path still works (uses the CSV fixture).
  var reg = await ev("(function(){document.getElementById('formatSel').value='auto';loadTexts([window.__csv],1);return {rows:STATE.rows.length,hasAlarmId:STATE.columns.some(function(c){return c.label==='AlarmID';})};})()");
  eq("regression: delimited fixture rows", reg.rows, 4);
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
