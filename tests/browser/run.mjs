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

// Three shapes the downtime guess has to tell apart. None of them has a
// Duration column or a set/clear column, so the only thing separating them is
// whether the default phrase lists actually pair up in the text.
//
// This one pairs: four chambers go offline and come back.
const deriveLog = [
  "When,ID,Message",
  "2026-02-10 08:00:00,E1,Chamber 1 state changed to offline",
  "2026-02-10 10:00:00,E2,Chamber 1 state changed to online",
  "2026-02-10 11:00:00,E3,Chamber 2 offline for maintenance",
  "2026-02-10 14:30:00,E4,Chamber 2 state changed to online",
  "2026-02-11 09:00:00,E5,Chamber 1 state changed to offline",
  "2026-02-11 12:00:00,E6,Chamber 1 state changed to online",
  "2026-02-12 07:00:00,E7,Load Lock A state changed to offline",
  "2026-02-12 08:15:00,E8,Load Lock A state changed to online",
  ""
].join("\n");

// The same log with every "online" message removed. Derive would cap each
// interval at the last timestamp and report huge invented downtime, so the
// guess must refuse it.
const deriveDownsOnly = [
  "When,ID,Message",
  "2026-02-10 08:00:00,E1,Chamber 1 state changed to offline",
  "2026-02-10 11:00:00,E3,Chamber 2 offline for maintenance",
  "2026-02-11 09:00:00,E5,Chamber 1 state changed to offline",
  ""
].join("\n");

// A log that outruns a 30-day window. The other fixtures all sit inside one, so
// nothing they do can show what the window drops.
const windowLog = [
  "Stamp,Code,Text",
  "2026-01-01 08:00:00,W1,Pump motor error",
  "2026-02-01 08:00:00,W2,Gas flow error",
  "2026-03-01 08:00:00,W3,Pump motor error",
  "2026-05-01 08:00:00,W4,Gas flow error",
  "2026-05-15 08:00:00,W5,Pump motor error",
  ""
].join("\n");

// Chambers named, but wording the default phrase lists have never seen. Derive
// would find nothing and report no downtime while looking as though it had
// measured some.
const deriveNoWording = [
  "When,ID,Message",
  "2026-02-10 08:00:00,E1,Chamber 1 pressure out of range",
  "2026-02-10 10:00:00,E2,Chamber 1 pressure recovered",
  "2026-02-11 09:00:00,E5,Chamber 2 gas flow deviation",
  ""
].join("\n");

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
  await ev("window.__p = " + JSON.stringify(p5000) + "; window.__csv = " + JSON.stringify(csv)
    + "; window.__derive = " + JSON.stringify(deriveLog)
    + "; window.__downsOnly = " + JSON.stringify(deriveDownsOnly)
    + "; window.__noWording = " + JSON.stringify(deriveNoWording)
    + "; window.__window = " + JSON.stringify(windowLog) + "; true");

  // 1. window.AP exists and is populated.
  var apKeys = await ev("Object.keys(window.AP || {}).length");
  check("window.AP exposed", apKeys > 10, { keys: apKeys });

  // 1b. The page opens in the quick report. This is read before anything else
  // touches the mode, and the mode tests at the end clear the stored choice, so
  // a repeat run sees a first-time visitor again.
  var firstMode = await ev("({cls:document.body.className, saved:localStorage.getItem('ap_mode')})");
  check("page opens in the quick report", firstMode.cls === "mode-quick" && firstMode.saved === null, firstMode);

  // Everything from here to section 9 exercises the full report, which is the
  // whole tool. The mode tests at the end drive the quick report on purpose.
  await ev("setMode('full', false); true");
  eq("switched to the full report for the main suite", await ev("document.body.className"), "mode-full");

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

  // 6b-etch3. Batch 1 from the real etch3 log. Every message below was
  // transcribed from the owner's photograph of the uncategorized worklist, so
  // each check is the proof that one rule survived the transcription. If one of
  // these fails, the pattern is wrong, not the example.
  var e3a = await ev("(function(){function c(s){return AP.categorize(s).category;}return {"
    + "svcState:c('chamber <S4EXT> chamber_abcd_optset state changed to <L1EXT> service_command_optset'),"
    + "leakUp:c('chamber <S4EXT> chamber_abcd_optset has completed leak up rate service program'),"
    + "lfcCal:c('chamber <S4EXT> chamber_abcd_optset has completed lfc cal service program'),"
    + "badByte:c('<S4EXT> chx_index_optset bad message byte count func_char+colon <L1>'),"
    + "badFunc:c('<S4EXT> chx_index_optset bad message function code or exception response func_char+colon <L1>'),"
    + "badStart:c('<S4EXT> chx_index_optset bad message start character'),"
    + "badSlave:c('<S4EXT> chx_index_optset bad message slave address func_char+colon <L1>'),"
    + "sysState:c('system control state changed to <L1EXT> system_state_optset'),"
    + "ocr:c('ocr does not respond check connection'),"
    + "sysConst:c('system constant out of range func_cut id <L1> has value <L2>'),"
    + "linkSeq:c('link sequence to lot for wafers in cassette <S4EXT> chamber_abcd_optset'),"
    + "disk:c('func_switch undefined_disk_error_text'),"
    + "ozoneConc:c('ozone concentration out of range in ch <S4EXT> chamber_abcd_optset recipe running'),"
    + "manualHome:c('completed manual home all loader axes'),"
    + "magnet:c('chamber <S4EXT> chamber_abcd_optset detected magnet coil current not changing'),"
    + "endpoint:c('required endpoint system not present'),"
    + "liftStep:c('chamber <S4EXT> chamber_abcd_optset lift step <L1> out of range, will use limit of <L2>'),"
    + "gpc:c('gpc event func_append+colon <S4EXT> gpc_event_optset, status <L1> param <L2> <L3>'),"
    + "ozoneGain:c('afx ozone analyzer has gain ratio error'),"
    + "bladeAuto:c('blade has been auto retracted due to some errors had occurred to chamber'),"
    + "bladeErr:c('some errors had occurred to ch <S4EXT> chamber_abcd_optset; blade being retracted'),"
    + "slotFull:c('need to unload to slot func_cut <L1> of cassette <S4EXT> cassette_name_table, is already full'),"
    + "ilkLamp:c('ch <S4EXT> chamber_abcd_optset interlock lamp overtemp or out of pos or cover open'),"
    + "ilkCover:c('ch <S4EXT> chamber_abcd_optset interlock func_append+colon cover open or out of pos or no coolant flow or lamp over temp')"
    + "};})()");
  eq("categorize etch3 chamber service state change", e3a.svcState, "Chamber service state change");
  eq("categorize etch3 leak up rate complete", e3a.leakUp, "Leak up rate check complete");
  eq("categorize etch3 LFC cal complete", e3a.lfcCal, "LFC calibration complete");
  eq("categorize etch3 bad message byte count", e3a.badByte, "Chamber index comms error");
  eq("categorize etch3 bad message function code", e3a.badFunc, "Chamber index comms error");
  eq("categorize etch3 bad message start character", e3a.badStart, "Chamber index comms error");
  eq("categorize etch3 bad message slave address", e3a.badSlave, "Chamber index comms error");
  eq("categorize etch3 system control state change", e3a.sysState, "System control state change");
  eq("categorize etch3 OCR not responding", e3a.ocr, "OCR not responding");
  eq("categorize etch3 system constant out of range", e3a.sysConst, "System constant out of range");
  eq("categorize etch3 sequence not linked to lot", e3a.linkSeq, "Sequence not linked to lot");
  eq("categorize etch3 disk error", e3a.disk, "Disk error");
  eq("categorize etch3 ozone concentration out of range", e3a.ozoneConc, "Ozone concentration out of range");
  eq("categorize etch3 loader manual home", e3a.manualHome, "Loader manual home complete");
  eq("categorize etch3 magnet coil current", e3a.magnet, "Magnet coil current not changing");
  eq("categorize etch3 endpoint system missing", e3a.endpoint, "Endpoint system missing");
  eq("categorize etch3 lift step out of range", e3a.liftStep, "Lift step out of range");
  eq("categorize etch3 GPC event", e3a.gpc, "GPC event");
  eq("categorize etch3 ozone analyzer gain ratio", e3a.ozoneGain, "Ozone analyzer gain ratio error");
  eq("categorize etch3 blade auto retracted", e3a.bladeAuto, "Blade retracted after chamber error");
  eq("categorize etch3 blade being retracted (same label)", e3a.bladeErr, "Blade retracted after chamber error");
  eq("categorize etch3 cassette slot already full", e3a.slotFull, "Cassette slot already full");
  eq("categorize etch3 interlock lamp overtemp", e3a.ilkLamp, "Chamber interlock");
  eq("categorize etch3 interlock cover open (same label)", e3a.ilkCover, "Chamber interlock");

  var e3b = await ev("(function(){function c(s){return AP.categorize(s).category;}return {"
    + "restart:c('equipment restart'),"
    + "pwrDev:c('ch <S4EXT> chamber_abcd_optset crf2 delivered pwr deviation err, delivered pwr <L1> func_char+char_w, limit set <L2> func_char+char_w'),"
    + "allProc:c('all processing of wafers is complete'),"
    + "orient:c('orient command error'),"
    + "auxLine:c('mainframe aux_final <S4> auxiliary final line pressure high fault func_switch rest_of_311'),"
    + "coverOpen:c('cover is open error in chamber <S4EXT> chamber_abcd_optset'),"
    + "lsTemp:c('liquid source <S4> temp out of fault tolerance func_cut func_char+colon func_long_2+3 degreesC func_switch ch_p3_paren'),"
    + "uwPress:c('chamber <S4EXT> chamber_abcd_optset cvd - func_char+char_1 microwave pressure too high'),"
    + "mfcFlow:c('chamber <S4EXT> chamber_abcd_optset service program has flow with mfc func_cut <L1> too high'),"
    + "backing:c('chamber <S4EXT> chamber_abcd_optset backing pump over temperature fault'),"
    + "uwDet:c('chamber <S4EXT> chamber_abcd_optset cvd - func_char+char_1 microwave plasma detector not operational'),"
    + "foreline:c('chamber <S4EXT> chamber_abcd_optset foreline idle pressure is too high'),"
    + "turboPurge:c('ch <S4EXT> chamber_abcd_optset turbo purge off - high pressure with trapped process gases'),"
    + "abortSeq:c('func_caps abort selected in reply to a sequencing fault'),"
    + "recovery:c('check system control screen for error recovery options'),"
    + "rebootCfg:c('reboot the system after a change to the chamber config'),"
    + "indexer:c('cannot extend - indexer not at right level to receive wafer'),"
    + "elevator:c('cannot find storage elevator zero pos - check cap sensors'),"
    + "onBlade:c('there is already a wafer on the blade'),"
    + "gasStop:c('ch <S4EXT> chamber_abcd_optset process gases stopped - pressure func_cut above func_si_long_1 u_millitorr'),"
    + "roughing:c('the load lock ch roughing pump is not running'),"
    + "cleaning:c('remote liquid source <S4> completed required cleaning time'),"
    + "forgotten:c('any wafers that were in the sys have been forgotten - inspect and recreate'),"
    + "namesLost:c('recipe and sequence func_caps selection , lot sequences and wafer lot names lost'),"
    + "dataLost:c('saved mfc leak up, cal and cycle purge valve selection func_append+char_s - data lost'),"
    + "zeroLost:c('mfc and pressure zero offset func_append+char_s lost, liquid source control will take time'),"
    + "rotation:c('rotation lost with wafer on vacuum chuck'),"
    + "falseMotion:c('false motion complete on <S4EXT> stepper_name_table'),"
    + "rateLow:c('ch <S4EXT> chamber_abcd_optset temp rate of change too low at max power func_switch error_temp_data'),"
    + "dummyRf:c('dummy wafer num. <S4EXT> dummy_wafer_1234_optset reached rf - on time warning level'),"
    + "turboSpeed:c('chamber <S4EXT> chamber_abcd_optset turbo not at speed timeout reached'),"
    + "htEx:c('ltc ht ex <S4> temperature deviation fault alarm'),"
    + "hiFlow:c('attempt hi flow cal without high flow cal xducer installed ch <S4EXT> chamber_abcd_optset')"
    + "};})()");
  eq("categorize etch3 equipment restart", e3b.restart, "Equipment restart");
  eq("categorize etch3 RF delivered power deviation", e3b.pwrDev, "RF delivered power deviation");
  eq("categorize etch3 all processing complete reuses All wafers completed", e3b.allProc, "All wafers completed");
  eq("categorize etch3 orient command error", e3b.orient, "Orient command error");
  eq("categorize etch3 auxiliary line pressure high", e3b.auxLine, "Auxiliary line pressure high");
  eq("categorize etch3 chamber cover open", e3b.coverOpen, "Chamber cover open");
  eq("categorize etch3 liquid source temp out of tolerance", e3b.lsTemp, "Liquid source temp out of tolerance");
  eq("categorize etch3 microwave pressure too high", e3b.uwPress, "Microwave pressure too high");
  eq("categorize etch3 MFC flow too high", e3b.mfcFlow, "MFC flow too high");
  eq("categorize etch3 backing pump over temperature", e3b.backing, "Backing pump over temperature");
  eq("categorize etch3 microwave plasma detector", e3b.uwDet, "Microwave plasma detector fault");
  eq("categorize etch3 foreline pressure high", e3b.foreline, "Foreline pressure high");
  eq("categorize etch3 turbo purge off", e3b.turboPurge, "Turbo purge off");
  eq("categorize etch3 abort after sequencing fault", e3b.abortSeq, "Abort after sequencing fault");
  eq("categorize etch3 error recovery prompt", e3b.recovery, "Error recovery prompt");
  eq("categorize etch3 reboot required after config change", e3b.rebootCfg, "Reboot required after config change");
  eq("categorize etch3 indexer not at right level", e3b.indexer, "Indexer not at right level");
  eq("categorize etch3 storage elevator zero not found", e3b.elevator, "Storage elevator zero not found");
  eq("categorize etch3 wafer already on blade", e3b.onBlade, "Wafer already on blade");
  eq("categorize etch3 process gases stopped", e3b.gasStop, "Process gases stopped");
  eq("categorize etch3 roughing pump not running", e3b.roughing, "Roughing pump not running");
  eq("categorize etch3 liquid source cleaning complete", e3b.cleaning, "Liquid source cleaning complete");
  eq("categorize etch3 wafers forgotten", e3b.forgotten, "Data lost after restart");
  eq("categorize etch3 lot names lost (same label)", e3b.namesLost, "Data lost after restart");
  eq("categorize etch3 valve selection data lost (same label)", e3b.dataLost, "Data lost after restart");
  eq("categorize etch3 zero offset lost (same label)", e3b.zeroLost, "Data lost after restart");
  eq("categorize etch3 rotation lost on chuck", e3b.rotation, "Rotation lost on chuck");
  eq("categorize etch3 false motion complete", e3b.falseMotion, "False motion complete");
  eq("categorize etch3 heat-up rate too low", e3b.rateLow, "Heat-up rate too low");
  eq("categorize etch3 dummy wafer RF time warning", e3b.dummyRf, "Dummy wafer RF time warning");
  eq("categorize etch3 turbo not at speed", e3b.turboSpeed, "Turbo not at speed");
  eq("categorize etch3 heat exchanger temp deviation", e3b.htEx, "Heat exchanger temp deviation");
  eq("categorize etch3 high flow cal transducer missing", e3b.hiFlow, "High flow cal transducer missing");

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
    + "{id:'901',sev:'TRACE',desc:'processing complete for wafer <S7> of lot <S8>'},"      // 4 total, clear top
    + "{id:'570',sev:'PROMPT',desc:'port <S1EXT> wafer not sensed by vacuum'},"
    + "{id:'050',sev:'TRACE',desc:'front panel func_char a depressed'},"
    + "{id:'050',sev:'TRACE',desc:'front panel func_char a depressed'},"                    // repeat: this sub-message wins
    + "{id:'050',sev:'TRACE',desc:'front panel totally different free text here now'}"     // two distinct shapes
    + "];"
    + "var roll=AP.rollupById(list);"
    + "var top=roll[0];"
    + "var fp=roll.filter(function(r){return r.id==='050';})[0];"
    + "return {topId:top.id, topCount:top.count, topShapes:top.shapes, topListLen:top.shapeList.length, fpShapes:fp.shapes, fpListLen:fp.shapeList.length, fpTopCount:fp.shapeList[0].count, fpTopEx:fp.shapeList[0].example, n:roll.length};"
    + "})()");
  eq("rollupById ranks most common ID first", idroll.topId, "901");
  eq("rollupById counts occurrences", idroll.topCount, 4);
  eq("rollupById collapses same-shape variants to 1 shape", idroll.topShapes, 1);
  eq("rollupById single-shape ID has one shapeList entry", idroll.topListLen, 1);
  eq("rollupById counts distinct shapes for mixed ID", idroll.fpShapes, 2);
  eq("rollupById mixed ID shapeList has both sub-messages", idroll.fpListLen, 2);
  eq("rollupById shapeList sorts most common sub-message first", idroll.fpTopEx, "front panel func_char a depressed");
  eq("rollupById shapeList counts the top sub-message", idroll.fpTopCount, 2);
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
    + "var split611=/611\\s+x2\\s+\\[FAULT\\]\\s+2 shapes, split per sub-message:/.test(before);"
    + "var alphaSub=/\\n\\s+x1\\s+chamber <S4EXT> zzz brand new widget alpha jam/.test(before);"
    + "var betaSub=/\\n\\s+x1\\s+chamber <S4EXT> zzz brand new widget beta jam/.test(before);"
    + "var single622=/622\\s+x1\\s+\\[FAULT\\]\\s+1 shape\\s+totally novel gizmo/.test(before);"
    + "document.getElementById('catRules').value='id:611 => Widget jam';"
    + "runAnalysis();"
    + "var after=uncategorizedIdReport(100);"
    + "document.getElementById('catRules').value='id:611 => Widget jam\\nid:622 => Gizmo fault';"
    + "runAnalysis();"
    + "var allDone=uncategorizedIdReport(100);"
    + "return {had611:had611, had622:had622, split611:split611, alphaSub:alphaSub, betaSub:betaSub, single622:single622, still611:/\\n\\s*611\\s+x/.test(after), still622:/\\n\\s*622\\s+x/.test(after), headerHasTop:/Uncategorized event IDs \\(top/.test(before), allDoneNone:/none\\. Every event matched a real category rule/.test(allDone)};"
    + "})()");
  check("worklist header present", idrep.headerHasTop, idrep);
  check("worklist lists uncategorized ID 611 with count", idrep.had611, idrep);
  check("worklist lists uncategorized ID 622 with count", idrep.had622, idrep);
  check("multi-shape ID 611 is split per sub-message", idrep.split611, idrep);
  check("worklist shows the alpha sub-message", idrep.alphaSub, idrep);
  check("worklist shows the beta sub-message", idrep.betaSub, idrep);
  check("single-shape ID 622 stays one line", idrep.single622, idrep);
  check("id: rule removes ID 611 from the worklist", idrep.still611 === false, idrep);
  check("unrelated ID 622 stays on the worklist", idrep.still622 === true, idrep);
  check("when all matched by rules, worklist says none (honest)", idrep.allDoneNone, idrep);

  // 6b-idpre. Before any analysis, the worklist must not claim full categorization.
  var idpre = await ev("(function(){var saved=ANALYZED; ANALYZED=false; var r=uncategorizedIdReport(100); ANALYZED=saved; return r;})()");
  check("worklist says run Analyze first before an analysis", /run Analyze first/.test(idpre) && !/every event matched/i.test(idpre), idpre);

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

  // 6p. The debug button lives at the bottom, after the results section, and is
  // revealed once there is data. A note tells the user to Analyze first.
  var dbgPos = await ev("(function(){"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__p],1);runAnalysis();"
    + "var sec=document.getElementById('debugSection');"
    + "var results=document.getElementById('results');"
    + "var afterResults=(results.compareDocumentPosition(sec) & Node.DOCUMENT_POSITION_FOLLOWING)!==0;"
    + "var note=sec.textContent;"
    + "return {shown:sec.style.display!=='none', afterResults:afterResults, hasNote:/Analyze first/i.test(note)};"
    + "})()");
  check("debug section is revealed after import/analyze", dbgPos.shown, dbgPos);
  check("debug section sits after the results section", dbgPos.afterResults, dbgPos);
  check("debug section note says Analyze first", dbgPos.hasNote, dbgPos);

  // 7. Regression: the delimited path still works (uses the CSV fixture).
  var reg = await ev("(function(){document.getElementById('formatSel').value='auto';loadTexts([window.__csv],1);return {rows:STATE.rows.length,hasAlarmId:STATE.columns.some(function(c){return c.label==='AlarmID';})};})()");
  eq("regression: delimited fixture rows", reg.rows, 4);
  check("regression: CSV headers read", reg.hasAlarmId, reg);

  // 8. Remembered setup. These tests write to local storage, so they run last
  // and clear every ap_setup_ key at both ends, leaving the page as they found
  // it. Helpers are installed on the page so each step reads the same way.
  await ev("(function(){"
    + "window.__wipe=function(){var kill=[];for(var i=0;i<localStorage.length;i++){var k=localStorage.key(i);if(k.indexOf('ap_setup_')===0)kill.push(k);}kill.forEach(function(k){localStorage.removeItem(k);});return kill.length;};"
    // Read the role drop-down for a column, by the column's name.
    + "window.__role=function(lbl){for(var i=0;i<STATE.columns.length;i++){if(STATE.columns[i].label===lbl){var s=document.getElementById('colid_'+STATE.columns[i].key);return s?s.value:'?';}}return '?';};"
    // Set one, the way a person would: change the value, then fire the event.
    + "window.__setRole=function(lbl,role){for(var i=0;i<STATE.columns.length;i++){if(STATE.columns[i].label===lbl){var s=document.getElementById('colid_'+STATE.columns[i].key);s.value=role;s.dispatchEvent(new Event('change',{bubbles:true}));return true;}}return false;};"
    + "window.__set=function(id,val,evt){var el=document.getElementById(id);el.value=val;el.dispatchEvent(new Event(evt||'change',{bubbles:true}));};"
    + "window.__keys=function(){var out=[];for(var i=0;i<localStorage.length;i++){var k=localStorage.key(i);if(k.indexOf('ap_setup_')===0)out.push(k);}return out.sort();};"
    // A second P5000 log, same seven columns but a different tool in its preamble.
    + "window.__etch='System type:  P5000\\nProcess type: Etch\\n   SCIII+ Event Data File:  E:\\\\Backups\\\\etch4\\\\Data\\\\ELOG.DAT\\nDate  Time  Event Number  Event Type  Description\\n"
    + "08/07/26  12:00:00  807  FAULT  chamber <S2EXT> chamber minimum gas flow error\\n"
    + "08/07/26  12:01:00  807  FAULT  chamber <S2EXT> chamber minimum gas flow error\\n';"
    + "return true;})()");

  // 8a. A fresh tool has nothing saved: the columns are guessed and the Forget
  // button stays out of the way.
  var s0 = await ev("(function(){"
    + "window.__wipe();"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__p],1);"
    + "return {chamber:__role('Chamber'), msg:document.getElementById('setupMsg').textContent,"
    + " forget:document.getElementById('forgetSetupBtn').style.display, keys:__keys().length};"
    + "})()");
  eq("setup: first import guesses the Chamber column", s0.chamber, "equipment");
  check("setup: nothing saved yet, so no message", s0.msg === "" && s0.keys === 0, s0);
  eq("setup: Forget button hidden when nothing is saved", s0.forget, "none");

  // 8b. What the user changes is written under a key named for the tool.
  var s1 = await ev("(function(){"
    + "__setRole('Chamber','ignore');"
    + "__set('downMode','events');__set('setVal','ON','input');"
    + "var sev=document.querySelectorAll('.sevchk')[0];var sevVal=sev.value;"
    + "sev.checked=false;sev.dispatchEvent(new Event('change',{bubbles:true}));"
    + "var saved=JSON.parse(localStorage.getItem('ap_setup_tool dep1')||'null');"
    + "return {keys:__keys(), saved:saved, sevVal:sevVal,"
    + " forget:document.getElementById('forgetSetupBtn').style.display};"
    + "})()");
  check("setup: saved under the tool name", s1.keys.join(",") === "ap_setup_tool dep1", s1.keys);
  check("setup: saved entry records the column roles", !!s1.saved && s1.saved.columns.some(function (c) { return c.label === "Chamber" && c.role === "ignore"; }), s1.saved);
  eq("setup: saved entry records the downtime mode", s1.saved && s1.saved.downMode, "events");
  eq("setup: saved entry records a downtime setting", s1.saved && s1.saved.setVal, "ON");
  check("setup: saved entry records the unticked severity", !!s1.saved && s1.saved.filters.sevchk.indexOf(s1.sevVal) >= 0, s1.saved && s1.saved.filters);
  eq("setup: Forget button appears once something is saved", s1.forget, "");

  // 8c. Re-importing the same tool brings all of it back, with no setup work.
  var s2 = await ev("(function(){"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__p],1);"
    + "var sev=document.querySelectorAll('.sevchk')[0];"
    + "return {chamber:__role('Chamber'), downMode:document.getElementById('downMode').value,"
    + " setVal:document.getElementById('setVal').value, sevChecked:sev?sev.checked:null, sevVal:sev?sev.value:null,"
    + " msg:document.getElementById('setupMsg').textContent, codes:AP.getDebug().order.slice(),"
    + " eventOpts:document.getElementById('eventOpts').style.display};"
    + "})()");
  eq("setup: re-import restores the column role", s2.chamber, "ignore");
  eq("setup: re-import restores the downtime mode", s2.downMode, "events");
  eq("setup: re-import restores the set/clear wording", s2.setVal, "ON");
  check("setup: re-import shows the panel for the restored mode", s2.eventOpts === "", s2);
  check("setup: re-import restores the unticked severity box", s2.sevChecked === false && s2.sevVal === s1.sevVal, s2);
  check("setup: re-import says which tool it restored", /dep1/.test(s2.msg) && /Restored/.test(s2.msg), s2.msg);
  check("setup: re-import records SETUP-RESTORED", s2.codes.indexOf("SETUP-RESTORED") >= 0, s2.codes);
  check("SETUP-RESTORED is a registered debug code", await ev("!!AP.DEBUG_CODES['SETUP-RESTORED']"), true);

  // 8d. The core of it: an etch log does not inherit the dep log's answers, and
  // saving one tool's setup leaves the other's alone.
  var s3 = await ev("(function(){"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__etch],1);"
    + "var fresh={chamber:__role('Chamber'), downMode:document.getElementById('downMode').value,"
    + " msg:document.getElementById('setupMsg').textContent};"
    + "__setRole('Chamber','other');__set('downMode','duration');"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__p],1);"
    + "var dep={chamber:__role('Chamber'), downMode:document.getElementById('downMode').value};"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__etch],1);"
    + "var etch={chamber:__role('Chamber'), downMode:document.getElementById('downMode').value};"
    + "return {fresh:fresh, dep:dep, etch:etch, keys:__keys()};"
    + "})()");
  check("setup: a different tool starts from the guess, not the other tool's setup", s3.fresh.chamber === "equipment" && s3.fresh.downMode === "none", s3.fresh);
  check("setup: a different tool shows no restore message", s3.fresh.msg === "", s3.fresh.msg);
  check("setup: the dep log still recalls its own", s3.dep.chamber === "ignore" && s3.dep.downMode === "events", s3.dep);
  check("setup: the etch log recalls its own", s3.etch.chamber === "other" && s3.etch.downMode === "duration", s3.etch);
  check("setup: one key per tool", s3.keys.join(",") === "ap_setup_tool dep1,ap_setup_tool etch4", s3.keys);

  // 8e. The derive lists ride along with the rest.
  var s4 = await ev("(function(){"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__etch],1);"
    + "__set('downMode','derive');"
    + "__set('downPhrases','went dark','input');__set('upPhrases','came back','input');"
    + "__set('chamberNames','Widget Chamber','input');"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__etch],1);"
    + "return {down:document.getElementById('downPhrases').value, up:document.getElementById('upPhrases').value,"
    + " names:document.getElementById('chamberNames').value, mode:document.getElementById('downMode').value,"
    + " deriveShown:document.getElementById('deriveOpts').style.display};"
    + "})()");
  eq("setup: down phrases ride along", s4.down, "went dark");
  eq("setup: up phrases ride along", s4.up, "came back");
  eq("setup: chamber names ride along", s4.names, "Widget Chamber");
  check("setup: derive panel is shown on restore", s4.mode === "derive" && s4.deriveShown === "", s4);

  // 8f. Forget throws the saved setup away and guesses the columns again.
  var s5 = await ev("(function(){"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__p],1);"
    + "var before=__role('Chamber');"
    + "document.getElementById('forgetSetupBtn').click();"
    + "var after={chamber:__role('Chamber'), msg:document.getElementById('setupMsg').textContent,"
    + " downMode:document.getElementById('downMode').value,"
    + " forget:document.getElementById('forgetSetupBtn').style.display, keys:__keys()};"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__p],1);"
    + "after.reimport=__role('Chamber');after.reimportMsg=document.getElementById('setupMsg').textContent;"
    + "return {before:before, after:after};"
    + "})()");
  eq("setup: the dep setup was still there before forgetting", s5.before, "ignore");
  eq("setup: Forget re-guesses the columns", s5.after.chamber, "equipment");
  check("setup: Forget says so", /Forgot the saved setup for dep1/.test(s5.after.msg), s5.after.msg);
  eq("setup: Forget also clears the downtime settings", s5.after.downMode, "none");
  check("setup: Forget removes only that tool's key", s5.after.keys.join(",") === "ap_setup_tool etch4", s5.after.keys);
  check("setup: a forgotten setup stays forgotten on re-import", s5.after.reimport === "equipment" && s5.after.reimportMsg === "", s5.after);

  // 8g. A delimited export names no tool, so it is filed by its column layout.
  var s6 = await ev("(function(){"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__csv],1);"
    + "var key=__keys();"                                    // nothing yet
    + "__setRole('AlarmID','ignore');"
    + "var saved=__keys().filter(function(k){return k.indexOf('ap_setup_columns')===0;});"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__csv],1);"
    + "return {beforeKeys:key.length, savedKey:saved[0]||null, role:__role('AlarmID'),"
    + " msg:document.getElementById('setupMsg').textContent};"
    + "})()");
  eq("setup: the CSV had nothing saved before", s6.beforeKeys, 1);   // only the etch4 key survives
  check("setup: a delimited file is filed by its columns", /^ap_setup_columns /.test(s6.savedKey || ""), s6.savedKey);
  eq("setup: the delimited mapping comes back", s6.role, "ignore");
  check("setup: the delimited restore names the layout", /this column layout/.test(s6.msg), s6.msg);

  // 8h. A damaged entry is treated as absent, not as an error.
  var s7 = await ev("(function(){"
    + "localStorage.setItem('ap_setup_tool dep1','{not json at all');"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__p],1);"
    + "return {chamber:__role('Chamber'), msg:document.getElementById('setupMsg').textContent, rows:STATE.rows.length};"
    + "})()");
  check("setup: a damaged saved entry is ignored", s7.chamber === "equipment" && s7.msg === "" && s7.rows === 12, s7);

  // Leave the browser as we found it, so a second run starts clean.
  var wiped = await ev("window.__wipe()");
  check("setup: test keys cleared", wiped >= 1, wiped);

  // 9. The quick report. Everything above ran in the full report; these drive
  // the short road a technician takes: pick a file, press Analyze, read it.
  // A helper reports whether a card is really on screen, since the modes hide
  // cards with a stylesheet rule rather than by setting display inline.
  await ev("(function(){window.__shown=function(id){var el=document.getElementById(id);"
    + "return !!(el && getComputedStyle(el).display!=='none');};return true;})()");

  // 9a. What the quick report shows and hides, once a file is loaded.
  var q1 = await ev("(function(){"
    + "setMode('quick');"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__p],1);"
    + "return {importCard:__shown('importCard'), runCard:__shown('runCard'), runBtn:__shown('runBtn'),"
    + " window:__shown('quickWindow'), mapCard:__shown('mapCard'), controls:__shown('controlsCard'),"
    + " debug:__shown('debugSection'), quickBtn:document.getElementById('modeQuick').className,"
    + " fullBtn:document.getElementById('modeFull').className};"
    + "})()");
  check("quick: import card, Analyze, and the window chips are shown", q1.importCard && q1.runCard && q1.runBtn && q1.window, q1);
  check("quick: the column table and settings are hidden", !q1.mapCard && !q1.controls, q1);
  check("quick: the debug log is hidden", !q1.debug, q1);
  check("quick: the mode buttons show which mode is on", q1.quickBtn === "active" && q1.fullBtn === "", q1);

  // 9b. The whole quick road, with nothing set by hand: load, press Analyze,
  // read the answer. The numbers must match what the full report gets from the
  // same file (top fault 494, 8 rows kept by the default severity filter).
  var q2 = await ev("(function(){"
    + "setMode('quick');"
    + "document.getElementById('catRules').value='';"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__p],1);"
    + "document.getElementById('runBtn').click();"
    + "var R=STATE.lastResult;"
    + "return {results:__shown('results'), total:R.totalFaults, topFault:R.levels.fault_code.byCount[0].key,"
    + " downMode:R.map.downMode, note:document.getElementById('quickNote').textContent,"
    + " unknown:__shown('unknownCard'), noteShown:__shown('quickNote')};"
    + "})()");
  check("quick: Analyze produces a report", q2.results && q2.noteShown, q2);
  eq("quick: same rows kept as the full report", q2.total, 8);
  eq("quick: same top fault as the full report", q2.topFault, "494");
  eq("quick: downtime mode guessed as none for this log", q2.downMode, "none");
  check("quick: the unknown-events panel stays hidden", !q2.unknown, q2);

  // 9c. The note owes the reader an account of every guess it made.
  check("quick note: names the tool and row count", /Read 12 rows from dep1/.test(q2.note), q2.note);
  check("quick note: names the timestamp columns", /Timestamp from Date \+ Time/.test(q2.note), q2.note);
  check("quick note: names the ID column", /counted by Event Number/.test(q2.note), q2.note);
  check("quick note: says why there is no downtime", /No downtime column was found/.test(q2.note), q2.note);
  check("quick note: says how much of the log this is", /Covering the last 30 days of the log/.test(q2.note), q2.note);
  check("quick note: offers the way out", /Something look wrong\? Open the full report/.test(q2.note), q2.note);

  // 9d. That way out flips to the full report with the data and result intact.
  var q3 = await ev("(function(){"
    + "document.getElementById('toFullBtn').click();"
    + "return {cls:document.body.className, rows:STATE.rows.length, results:__shown('results'),"
    + " map:__shown('mapCard'), debug:__shown('debugSection'), total:STATE.lastResult.totalFaults,"
    + " saved:localStorage.getItem('ap_mode'), tiles:document.querySelectorAll('#statCards .stat').length,"
    + " downPanel:__shown('downPanel'), chartOpts:__shown('chartOpts')};"
    + "})()");
  check("quick: the way out opens the full report", q3.cls === "mode-full" && q3.map && q3.debug, q3);
  check("quick: flipping keeps the file and the result", q3.rows === 12 && q3.total === 8 && q3.results, q3);
  eq("quick: the chosen mode is remembered", q3.saved, "full");
  // The result on screen was drawn for the quick report, which leaves out the
  // downtime tiles and the empty downtime chart. Flipping has to redraw it.
  check("quick: flipping redraws the result for the mode it lands in",
    q3.tiles === 4 && q3.downPanel && q3.chartOpts, q3);

  // 9d-b. And the other way: a full result flipped to quick loses the noise.
  var q3b = await ev("(function(){setMode('quick');"
    + "return {tiles:document.querySelectorAll('#statCards .stat').length,"
    + " downPanel:__shown('downPanel'), chartType:__shown('chartTypeField'),"
    + " logScale:__shown('logScaleField'),"
    + " single:document.getElementById('paretoSplit').className.indexOf('single')>=0};})()");
  check("quick: no zero-value downtime tiles when there is no downtime column", q3b.tiles === 2, q3b);
  check("quick: no empty downtime chart, and the chart takes the width", !q3b.downPanel && q3b.single, q3b);
  check("quick: the chart picker is offered", q3b.chartType, q3b);
  check("quick: log scale is not, since it changes what the bars appear to say", !q3b.logScale, q3b);

  // 9d-c. The picker is not decoration: each chart type draws in the quick
  // report, on the same data, with no settings panel to reach for.
  var q3c = await ev("(function(){"
    + "setMode('quick');"
    + "function bars(){return document.querySelectorAll('#countChart svg rect').length;}"
    + "document.getElementById('chartType').value='pareto';renderLevel();"
    + "var line=document.querySelectorAll('#countChart svg polyline').length;"
    + "document.getElementById('chartType').value='hbar';renderLevel();var hbar=bars();"
    + "document.getElementById('chartType').value='heatmap';renderLevel();var cells=bars();"
    + "document.getElementById('chartType').value='pareto';renderLevel();"
    + "return {line:line, hbar:hbar, cells:cells, back:bars()};"
    + "})()");
  check("quick: the Pareto draws its cumulative line", q3c.line >= 1, q3c);
  check("quick: horizontal bars draw", q3c.hbar >= 1, q3c);
  eq("quick: the heatmap draws its 168 cells", q3c.cells, 168);
  check("quick: switching back redraws the Pareto", q3c.back >= 1, q3c);

  // 9e. The downtime guess reads the columns. The CSV fixture has a DownSeconds
  // column, and an inline log with a Status column pairs set and clear rows.
  var q4 = await ev("(function(){"
    + "setMode('quick');"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__csv],1);"
    + "var csv={guess:guessDownMode(), mode:document.getElementById('downMode').value};"
    + "var states='When,AlarmID,Message,Status\\n2026-02-10 10:00:00,E1,Pump fault,SET\\n2026-02-10 11:00:00,E1,Pump fault,CLEAR\\n';"
    + "loadTexts([states],1);"
    + "var st={guess:guessDownMode(), mode:document.getElementById('downMode').value};"
    + "return {csv:csv, st:st};"
    + "})()");
  check("quick: a duration column is found and used", q4.csv.guess === "duration" && q4.csv.mode === "duration", q4.csv);
  check("quick: set/clear rows are found and paired", q4.st.guess === "events" && q4.st.mode === "events", q4.st);

  // 9f. The window chips. "All of it" widens the window and re-runs, and the
  // note says so rather than leaving the reader to guess.
  var q5 = await ev("(function(){"
    + "setMode('quick');"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__p],1);"
    + "document.getElementById('runBtn').click();"
    + "var before=STATE.lastResult.windowDays;"
    + "var all=Array.prototype.filter.call(document.querySelectorAll('.winchip'),function(b){return b.getAttribute('data-days')==='0';})[0];"
    + "all.click();"
    + "var after=STATE.lastResult.windowDays;"
    + "var note=document.getElementById('quickNote').textContent;"
    + "var active=Array.prototype.filter.call(document.querySelectorAll('.winchip'),function(b){return b.className.indexOf('active')>=0;}).map(function(b){return b.textContent;});"
    + "var ninety=Array.prototype.filter.call(document.querySelectorAll('.winchip'),function(b){return b.getAttribute('data-days')==='90';})[0];"
    + "ninety.click();"
    + "return {before:before, after:after, note:note, active:active,"
    + " ninety:STATE.lastResult.windowDays, settings:document.getElementById('windowDays').value};"
    + "})()");
  eq("quick: the window starts at 30 days", q5.before, 30);
  eq("quick: All of it widens the window", q5.after, 36500);
  check("quick: the note says the whole log is covered", /Covering the whole log/.test(q5.note), q5.note);
  check("quick: the chosen chip is lit, and only that one", q5.active.length === 1 && /All of it/.test(q5.active[0]), q5.active);
  check("quick: a chip re-runs the analysis and writes through to the settings", q5.ninety === 90 && q5.settings === "90", q5);

  // 9g. A column problem is reported where the reader is looking. In the quick
  // report the column table is hidden, so the message cannot only go there.
  var q6 = await ev("(function(){"
    + "setMode('quick');"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__p],1);"
    + "__setRole('Event Number','ignore');"
    + "document.getElementById('runBtn').click();"
    + "var out={importMsg:document.getElementById('importMsg').textContent,"
    + " mapMsg:document.getElementById('mapMsg').textContent};"
    + "__setRole('Event Number','fault_code');"
    + "return out;"
    + "})()");
  check("quick: a missing Message ID is reported above Analyze", /Tag one column as Message ID/.test(q6.importMsg), q6.importMsg);
  check("quick: and it points at the full report", /Open the full report/.test(q6.importMsg), q6.importMsg);
  check("quick: the full report still gets the message beside the columns", /Tag one column as Message ID/.test(q6.mapMsg), q6.mapMsg);

  // 9h. A file that partly failed to read says so in the note, since the quick
  // report has no debug log to find it in.
  var q7 = await ev("(function(){"
    + "setMode('quick');"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__p],1);"
    + "document.getElementById('runBtn').click();"
    + "var clean=document.getElementById('quickNote').innerHTML;"
    + "dbg('FMT-EMPTY','a second file read as nothing');"
    + "showQuickNote(STATE.lastResult);"
    + "var dirty=document.getElementById('quickNote').innerHTML;"
    + "return {cleanOk:/msg ok/.test(clean), cleanQuiet:!/did not read/.test(clean),"
    + " dirtyWarn:/msg warn/.test(dirty), dirtyText:/did not read \\(FMT-EMPTY\\)/.test(dirty)};"
    + "})()");
  check("quick: a clean read says nothing about errors", q7.cleanOk && q7.cleanQuiet, q7);
  check("quick: a failed read is named in the note", q7.dirtyWarn && q7.dirtyText, q7);

  // 9i. A pinned #quick or #full on the address wins over the stored choice.
  var q8 = await ev("(function(){"
    + "setMode('full');"                               // stored choice: full
    + "var saved=localStorage.getItem('ap_mode');"
    + "setMode('quick', false);"                       // a pinned address does not store
    + "return {saved:saved, stillSaved:localStorage.getItem('ap_mode'), cls:document.body.className};"
    + "})()");
  check("quick: a mode chosen by hand is stored", q8.saved === "full", q8);
  check("quick: a pinned mode applies without overwriting the stored choice", q8.cls === "mode-quick" && q8.stillSaved === "full", q8);

  // 9j. An opened debug log does not follow the reader into the quick report.
  //
  // The debug log is two blocks: the "Show debug log" button (#debugSection) and
  // the panel it opens (#debugCard), which is a sibling of it rather than a
  // child. The mode rule named only the button, so someone who opened the debug
  // log in the full report and then switched to the quick report kept the whole
  // panel on screen -- and could not put it away, because the toggle had gone
  // with the rest of the full report. The check above this one passed the whole
  // time: it asked about the button, which was correctly hidden.
  // An earlier test may already have opened the log, so this opens it only if it
  // is closed rather than clicking blindly and toggling it shut. The button is
  // checked with getClientRects, not __shown: it sits inside #debugSection, and
  // an element's own computed display says nothing about a hidden ancestor.
  var q9 = await ev("(function(){"
    + "function onScreen(id){var e=document.getElementById(id);return !!(e&&e.getClientRects().length>0);}"
    + "function openLog(){var c=document.getElementById('debugCard');"
    + "if(getComputedStyle(c).display==='none') document.getElementById('debugToggle').click();}"
    + "setMode('full');"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__p],1);"
    + "document.getElementById('runBtn').click();"
    + "openLog();"
    + "var open={section:onScreen('debugSection'), card:onScreen('debugCard')};"
    + "setMode('quick');"
    + "var quick={section:onScreen('debugSection'), card:onScreen('debugCard'),"
    + " toggle:onScreen('debugToggle')};"
    + "setMode('full');"
    + "var back={card:onScreen('debugCard')};"
    + "return {open:open, quick:quick, back:back};"
    + "})()");
  check("debug: the full report opens the log", q9.open.section && q9.open.card, q9.open);
  check("debug: an opened log is gone from the quick report", !q9.quick.card, q9.quick);
  check("debug: and so is the button that opens it", !q9.quick.section && !q9.quick.toggle, q9.quick);
  check("debug: going back to the full report finds it still open", q9.back.card, q9.back);

  // 10. A ranking's percentages belong to that ranking.
  //
  // byCount and byDown are two orderings of the same groups. They were built
  // from the same row objects, so the second call to collapse() overwrote the
  // rank, pct and cum the first had written: the "Count %" and "Cum %" columns
  // and the Pareto's cumulative line were showing downtime shares, which are all
  // zero whenever a log has no downtime column. Every DOM assertion passed while
  // the cumulative line lay flat along the bottom of the chart.
  var r1 = await ev("(function(){"
    + "setMode('full');"
    + "document.getElementById('catRules').value='';"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__p],1);"
    + "document.getElementById('runBtn').click();"
    + "var L=STATE.lastResult.levels.category;"
    + "return {pct:L.byCount.map(function(r){return +r.pct.toFixed(1);}),"
    + " cum:L.byCount.map(function(r){return +r.cum.toFixed(1);}),"
    + " ranks:L.byCount.map(function(r){return r.rank;}),"
    + " shared:L.byCount.some(function(r){return L.byDown.indexOf(r)!==-1;})};"
    + "})()");
  check("ranking: Count % is the share of the count, not of the downtime",
    JSON.stringify(r1.pct) === JSON.stringify([62.5, 12.5, 12.5, 12.5]), r1.pct);
  check("ranking: Cum % climbs to 100", JSON.stringify(r1.cum) === JSON.stringify([62.5, 75, 87.5, 100]), r1.cum);
  check("ranking: the count ranking is numbered from its own order",
    JSON.stringify(r1.ranks) === JSON.stringify([1, 2, 3, 4]), r1.ranks);
  check("ranking: the two rankings do not share row objects", r1.shared === false, r1);

  // The same, on a log that does have downtime: the two rankings must disagree
  // rather than both reporting the downtime share.
  // The DownSeconds column is already tagged Duration by the automatic guess,
  // so nothing here fires a change event: that would save a setup for this
  // layout and leave the next test restoring it instead of guessing.
  var r2 = await ev("(function(){"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__csv],1);"
    + "document.getElementById('downMode').value='duration';syncDownModeUI();"
    + "document.getElementById('windowDays').value=36500;"
    + "document.getElementById('runBtn').click();"
    + "var L=STATE.lastResult.levels.fault_code;"
    + "var out={countPct:L.byCount.map(function(r){return +r.pct.toFixed(1);}),"
    + " downPct:L.byDown.map(function(r){return +r.pct.toFixed(1);}),"
    + " countKeys:L.byCount.map(function(r){return r.key;}),"
    + " downKeys:L.byDown.map(function(r){return r.key;}), wiped:__wipe()};"
    + "return out;"
    + "})()");
  // Counts are E101 x2, E202, E303, so 50/25/25. The seconds are 14400, 7200
  // and 1800 of 23400, so the downtime ranking is a different order and a
  // different set of shares: 61.5/30.8/7.7.
  check("ranking: count shares stay count shares when downtime exists",
    JSON.stringify(r2.countPct) === JSON.stringify([50, 25, 25]), r2.countPct);
  check("ranking: downtime shares are computed from the downtime",
    JSON.stringify(r2.downPct) === JSON.stringify([61.5, 30.8, 7.7]), r2.downPct);
  check("ranking: the two rankings order the same groups differently",
    JSON.stringify(r2.countKeys) === JSON.stringify(["E101", "E202", "E303"]) &&
    JSON.stringify(r2.downKeys) === JSON.stringify(["E101", "E303", "E202"]), r2);

  // 11. The ranked table drops the two all-zero downtime columns in the quick
  // report, the same way the tiles and the empty chart were dropped.
  await ev("(function(){window.__heads=function(){"
    + "return Array.prototype.map.call(document.querySelectorAll('#resultTable th'),"
    + "function(t){return t.textContent;});};"
    + "window.__cells=function(){var tr=document.querySelectorAll('#resultTable tr')[1];"
    + "return tr?tr.children.length:0;};return true;})()");
  var t1 = await ev("(function(){"
    + "setMode('quick');"
    + "document.getElementById('catRules').value='';"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__p],1);"
    + "document.getElementById('runBtn').click();"
    + "var quick={heads:__heads(), cells:__cells()};"
    + "setMode('full');"
    + "var full={heads:__heads(), cells:__cells()};"
    + "return {quick:quick, full:full};"
    + "})()");
  check("table: the quick report drops the zero downtime columns",
    t1.quick.heads.indexOf("Attributed (h)") === -1 && t1.quick.heads.indexOf("Wall clock (h)") === -1, t1.quick.heads);
  check("table: and the body rows lose the same two cells", t1.quick.cells === t1.quick.heads.length, t1.quick);
  check("table: the full report keeps them, since its note explains the zeros",
    t1.full.heads.indexOf("Attributed (h)") !== -1 && t1.full.heads.indexOf("Wall clock (h)") !== -1, t1.full.heads);
  check("table: flipping the mode redraws the columns", t1.full.cells === t1.full.heads.length, t1.full);

  // 11b. The rest of the zero-downtime chatter. Dropping the two table columns
  // left three other places still talking about downtime the quick report is no
  // longer showing: the Insights chamber table carried the same zero column, the
  // footer named a ranking method for a ranking that is not on screen, and the
  // summary said downtime "is shown as zero" when none is shown at all.
  var t3 = await ev("(function(){"
    + "setMode('quick');"
    + "document.getElementById('catRules').value='';"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__p],1);"
    + "document.getElementById('runBtn').click();"
    + "function heads(){return Array.prototype.map.call("
    + "document.querySelectorAll('#chamberTable th'),function(t){return t.textContent;});}"
    + "function cells(){var tr=document.querySelectorAll('#chamberTable tr')[1];return tr?tr.children.length:0;}"
    + "var quick={heads:heads(), cells:cells(),"
    + " foot:document.getElementById('rangeFoot').textContent,"
    + " summary:document.getElementById('summaryMsg').textContent};"
    + "setMode('full');"
    + "var full={heads:heads(), cells:cells(),"
    + " foot:document.getElementById('rangeFoot').textContent,"
    + " summary:document.getElementById('summaryMsg').textContent};"
    + "return {quick:quick, full:full};"
    + "})()");
  check("insights: the chamber table drops its zero downtime column",
    t3.quick.heads.indexOf("Downtime (h)") === -1 && t3.quick.cells === t3.quick.heads.length, t3.quick);
  check("insights: the full report keeps it", t3.full.heads.indexOf("Downtime (h)") !== -1
    && t3.full.cells === t3.full.heads.length, t3.full);
  check("footer: no downtime ranking method where no downtime is ranked",
    !/Downtime ranking method/.test(t3.quick.foot), t3.quick.foot);
  check("footer: the date range is still there", /Date range/.test(t3.quick.foot), t3.quick.foot);
  check("footer: the full report still names the method",
    /Downtime ranking method/.test(t3.full.foot), t3.full.foot);
  check("summary: does not say zeros are shown when none are",
    !/shown as zero/.test(t3.quick.summary), t3.quick.summary);
  check("summary: the full report still explains its zeros",
    /shown as zero/.test(t3.full.summary), t3.full.summary);

  // 11c. Every cut between the rows read and the rows reported says what it
  // dropped. The window used to be silent, so the tile count could fall below
  // the last number in the summary with nothing accounting for the difference.
  var t4 = await ev("(function(){"
    + "setMode('quick');"
    + "document.getElementById('catRules').value='';"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__window],1);"
    + "setWindowDays(0);"                                  // whole log: nothing to drop
    + "document.getElementById('runBtn').click();"
    + "var all={note:STATE.lastResult.windowNote, total:STATE.lastResult.totalFaults};"
    + "setWindowDays(30);"                                 // the fixture runs past 30 days
    + "document.getElementById('runBtn').click();"
    + "var cut={note:STATE.lastResult.windowNote, total:STATE.lastResult.totalFaults,"
    + " summary:document.getElementById('summaryMsg').textContent};"
    + "return {all:all, cut:cut};"
    + "})()");
  check("window: says nothing when it drops nothing", t4.all.note === "", t4.all);
  check("window: names what it dropped when it does drop",
    /Kept \d+ of \d+ rows inside the 30 day window\./.test(t4.cut.note), t4.cut.note);
  check("window: and the reader sees it in the summary",
    /inside the 30 day window/.test(t4.cut.summary), t4.cut.summary);
  check("window: the number it kept is the number reported",
    t4.cut.note === "" || +t4.cut.note.match(/Kept (\d+)/)[1] === t4.cut.total, t4.cut);

  // A log that does have downtime keeps the columns in the quick report, since
  // there the numbers say something.
  var t2 = await ev("(function(){"
    + "setMode('quick');"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__csv],1);"
    + "document.getElementById('runBtn').click();"
    + "return {heads:__heads(), mode:STATE.lastResult.map.downMode, cells:__cells()};"
    + "})()");
  check("table: a log with real downtime keeps the columns in the quick report",
    t2.heads.indexOf("Attributed (h)") !== -1 && t2.cells === t2.heads.length, t2);

  // 12. The downtime guess may pick "Derive from messages", but only on
  // evidence. Choosing it wrongly invents downtime rather than omitting it, so
  // the guess runs the pairing first and takes the road only if pairs close.
  var d1 = await ev("(function(){"
    + "setMode('quick');"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__derive],1);"
    + "var pairs=derivePairsAvailable();"
    + "var guess=guessDownMode();"
    + "document.getElementById('windowDays').value=36500;"
    + "document.getElementById('runBtn').click();"
    + "var R=STATE.lastResult;"
    + "return {pairs:pairs, guess:guess, mode:R.map.downMode, derived:!!R.isDerived,"
    + " intervals:R.derived?R.derived.intervals.length:0,"
    + " hours:+(R.grandAttrib/3600).toFixed(2),"
    + " note:document.getElementById('quickNote').textContent,"
    + " phrases:document.getElementById('downPhrases').value.trim().length>0};"
    + "})()");
  eq("derive: the default phrases find the pairs in the log", d1.pairs, 4);
  check("derive: a log whose messages pair up is derived", d1.guess === "derive" && d1.mode === "derive", d1);
  check("derive: the phrase lists are filled in for the analysis to use", d1.phrases, d1);
  eq("derive: every pair became an interval", d1.intervals, 4);
  eq("derive: the estimated downtime is the sum of the pairs", d1.hours, 9.75);
  check("derive: the note says downtime was estimated by pairing messages",
    /Downtime estimated by pairing down and up messages/.test(d1.note), d1.note);
  check("derive: and says how many pairs it found", /\(4 pairs found\)/.test(d1.note), d1.note);

  // Downs with no ups. Every interval would be capped at the last timestamp,
  // which reads as enormous downtime that never happened.
  var d2 = await ev("(function(){"
    + "setMode('quick');"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__downsOnly],1);"
    + "return {pairs:derivePairsAvailable(), guess:guessDownMode()};"
    + "})()");
  eq("derive: downs that never close are not pairs", d2.pairs, 0);
  check("derive: a log of downs alone is ranked by count instead", d2.guess === "none", d2);

  // Wording the default lists have never seen.
  var d3 = await ev("(function(){"
    + "setMode('quick');"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__noWording],1);"
    + "return {pairs:derivePairsAvailable(), guess:guessDownMode()};"
    + "})()");
  check("derive: unfamiliar wording is not guessed at", d3.pairs === 0 && d3.guess === "none", d3);

  // A real downtime column still outranks the messages.
  var d4 = await ev("(function(){"
    + "setMode('quick');"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__csv],1);"
    + "return guessDownMode();"
    + "})()");
  eq("derive: a Duration column still wins over the message text", d4, "duration");

  // 13. What the quick report puts on paper. The hand-out is the summary, the
  // ranked table and the Pareto; anything whose job is to change the report
  // rather than to say what it found comes off the page.
  // A button inside a hidden card still reports its own display, so asking
  // __shown about it would say it is on the page. This asks whether the element
  // was laid out at all, which is what "on the paper" actually means.
  await ev("(function(){window.__visible=function(id){var el=document.getElementById(id);"
    + "return !!(el && el.getClientRects().length > 0);};return true;})()");
  await send("Emulation.setEmulatedMedia", { media: "print" });
  var pr = await ev("(function(){"
    + "setMode('quick');"
    + "document.getElementById('formatSel').value='auto';loadTexts([window.__p],1);"
    + "document.getElementById('windowDays').value=30;syncWindowChips();"
    + "document.getElementById('runBtn').click();"
    + "return {note:__visible('quickNote'), tiles:__visible('statCards'), table:__visible('resultTable'),"
    + " chart:__visible('countChart'), insights:__visible('insightsCard'), window:__visible('quickWindow'),"
    + " tabs:__visible('levelTabs'), chartOpts:__visible('chartOpts'), buttons:__visible('printBtn'),"
    + " header:__visible('modeQuick'), debug:__visible('debugSection'), importCard:__visible('importCard'),"
    + " toFull:__visible('toFullBtn')};"
    + "})()");
  check("print: the quick report keeps the summary, the ranking and the Pareto",
    pr.note && pr.tiles && pr.table && pr.chart, pr);
  check("print: the controls come off the page",
    !pr.window && !pr.tabs && !pr.chartOpts && !pr.buttons && !pr.toFull, pr);
  check("print: so does everything that is not the hand-out",
    !pr.insights && !pr.header && !pr.debug && !pr.importCard, pr);

  // The note has to survive printing: it is the only thing on the paper saying
  // which window and which columns produced these numbers.
  var prNote = await ev("document.getElementById('quickNote').textContent");
  check("print: the assumptions are still stated on the paper",
    /Covering the last 30 days/.test(prNote) && /faults counted by/.test(prNote), prNote);

  // The full report prints as it always has.
  var prFull = await ev("(function(){setMode('full');"
    + "return {insights:__visible('insightsCard'), tabs:__visible('levelTabs'), table:__visible('resultTable')};})()");
  check("print: the full report is left alone", prFull.insights && prFull.tabs && prFull.table, prFull);
  await send("Emulation.setEmulatedMedia", { media: "" });

  // Leave the stored mode and the saved setups as we found them.
  var cleaned = await ev("(function(){localStorage.removeItem('ap_mode');return __wipe()+1;})()");
  check("quick: mode and setup keys cleared", cleaned >= 1, cleaned);

  ws.close();
  proc.kill("SIGKILL");

  // CLAUDE.md quotes the number this suite should report, and a session reads
  // that number before touching anything. Left stale it reads as a regression,
  // which has happened: the count was written down as 138 while the suite was
  // 176, and again as 215 one commit before it became 220. So the suite checks
  // its own paperwork rather than trusting anyone to remember.
  //
  // This is a gate, not a check: it never adds to `passed`, because the number
  // it is comparing against is that very count.
  var notes = join(REPO, "CLAUDE.md");
  if (existsSync(notes)) {
    var quoted = readFileSync(notes, "utf8").match(/should report `(\d+) passed/);
    if (!quoted) {
      console.log("  FAIL CLAUDE.md no longer states the expected test count");
      failed += 1;
    } else if (+quoted[1] !== passed) {
      console.log("  FAIL CLAUDE.md says " + quoted[1] + " passed; this run counted " + passed +
        ". Update the number in CLAUDE.md as part of this change.");
      failed += 1;
    } else {
      console.log("  ok   CLAUDE.md test count is current (" + passed + ")");
    }
  }

  console.log("\n" + passed + " passed, " + failed + " failed");
  process.exit(failed ? 1 : 0);
}

main().catch(function (e) {
  console.error("Harness error: " + (e && e.stack ? e.stack : e));
  try { proc.kill("SIGKILL"); } catch (x) {}
  process.exit(2);
});
