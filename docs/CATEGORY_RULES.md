# Growing the category rules

This is the working guide for the arc where the owner sends pictures of real
elogs and of the debug worklist, and those turn into new category rules. Read it
before asking the owner anything: most of what a session needs to know is here.

The goal is coverage. Every message that matches no rule still gets a label, but
that label is invented from the message text, so the Pareto fills up with
near-duplicate rows that mean the same thing. A real rule collapses them into one
named fault a person recognises.

## How a message gets its category

Three passes, in this order. The first hit wins.

1. **Your rules**, in the order typed into "Message categories". Two forms:
   - `id:494,807 => Label` — exact match on the Event Number. One ID or a list.
   - `gas flow error => Gas flow error` — a case-insensitive regex on the text.
2. **The built-in rules**, `BUILTIN_CAT_RULES` in `alarm_pareto.html`, in array
   order.
3. **Nothing matched.** The message gets a readable label built from its own
   leading words, and is recorded as *uncategorized*.

That third case is the one to understand properly, because it does not look like
a failure on screen. The row shows a sensible-looking category and the "Matched
by" column reads **`auto: message shape`**. That is the tell. Anything reading
`auto: message shape` is work still to do, however tidy the label looks.

Rule order matters within each pass. `lot processing complete` sits above
`processing complete for wafer` in the built-ins because the wafer pattern would
otherwise swallow the lot message.

## What the owner sends, and what to do with it

### The uncategorized worklist

Full report → Analyze → tick **Verbose** → **Show debug log**. The report then
carries three things worth reading:

- `Uncategorized event IDs (top 100 of N distinct, by count)` — the worklist.
  Each entry is an ID with its count, severity, and an example message. An ID
  carrying several distinct messages is split into one indented line per
  sub-message, so each can get its own rule.
- `Uncategorized message shapes (top 20 of N)` — the same problem grouped by
  shape rather than by ID, for messages whose ID varies.
- `Category metrics` — `categorized X of Y (Z%)`, the per-rule hit counts, and
  **rules that never matched**. That last list is how dead rules get pruned.

### Everything arrives as a photograph

The bench machine has no way to get text out. Pictures of the screen are the
entire channel, permanently. Do not ask for pasted text, do not suggest the
"Copy uncategorized IDs" button, and do not frame a photograph as the inferior
option — it is the only option, and asking has already worn thin.

What that changes about the work:

- **Verbose mode was built for this.** With Verbose ticked the debug box grows to
  fit the whole report with no inner scroll bar, so the report can be captured by
  scrolling the page rather than fighting a scroll pane inside it. Larger browser
  zoom before capturing costs nothing and makes the difference between a legible
  count and a guess.
- **Transcribe before writing a regex,** and write down which characters were
  ambiguous — `l`/`1`, `0`/`O`, `rn`/`m`, `<S4EXT>` against `<S1EXT>`. That note
  is what makes a failed rule quick to pin later.
- **Prefer the invariant middle of a message over a long exact quote.** A short
  distinctive phrase has fewer characters to misread than a whole line, and it
  survives the chamber tags and values anyway. This is the same advice as the
  rule-writing section below, but here it also buys transcription safety.

### The tool proofreads the transcription

A rule written from a photograph is unverified until the tool says otherwise, and
there is a mechanism for exactly that. The debug report's **Category metrics**
block ends with **"rules that never matched"** — every rule that fired zero
times. A mis-transcribed pattern lands there, because it matches nothing.

So a batch is not finished when the rules are written. It is finished when the
owner has re-run with the new rules and that list comes back clean, or when every
name still on it is a rule deliberately kept for a log this run did not cover.
Ask for that one screenshot at the end of a batch; it is the cheapest check
available and it catches the whole class of error that photographs introduce.

Coverage moves in the same block: `categorized X of Y (Z%)` before and after says
whether the batch was worth adding.

### Real log lines

Raw rows are what confirm a pattern is safe — the worklist shows one example per
shape, and a rule is easier to trust after seeing several real messages that
should hit it. Transcribe the examples into the batch log at the bottom of this
guide before writing the regex, so a later session can check the pattern against
what was actually seen rather than against the pattern's own wording.

## Writing the rule

Prefer an **ID rule** when the ID is stable and the wording is not. Event numbers
do not change with the chamber, the values, or the software version, so
`id:494 => PM trigger reached` survives things a text pattern does not.

Prefer a **text rule** when one wording covers many IDs, or when the ID varies
across tools.

Rules to keep to:

- **Match the invariant part.** The chamber tag, the numbers and the bracketed
  values all vary. `reached the pm trigger time` is the stable middle of the
  message; `chamber <S4EXT> ... 12 hours` is not.
- **Do not anchor to the start.** Messages carry a leading `chamber <TAG>`.
- **Name the fault, not the message.** "Gas flow error", not "chamber minimum gas
  flow error detected on". The label becomes a Pareto bar and a hand-out row.
- **Reuse an existing label** when the message is the same fault worded
  differently. Two labels for one fault split the bar and hide the problem.
- **Put the narrow rule above the broad one.** Both passes are first-hit-wins.

## Where the pieces live

| what | where |
|---|---|
| Built-in rules | `BUILTIN_CAT_RULES`, `alarm_pareto.html` |
| Rule matching and precedence | `categorize()` |
| User rule parsing (`=>`, `id:`) | `parseCatRules()` |
| Shape collapsing | `normCategory()` |
| Worklist text | `uncategorizedIdReport()` |
| Coverage and dead-rule metrics | `categoryMetricsLines()` |
| Existing rule tests | `tests/browser/run.mjs`, the `categorize ...` checks |

The Python tool owns the same analysis math, but categories are a browser-tool
feature; adding a rule here does not put the browser and Python tools out of step.

## Finishing a batch

Every rule added earns a line in the harness beside the existing `categorize`
checks — one per rule, asserting the example message the owner supplied lands on
the intended label. That is what stops a later rule reordering from quietly
breaking an earlier one.

Then, in the same commit:

- `CHANGELOG.md`, under Unreleased, naming the faults now recognised.
- `CLAUDE.md`, the test count.
- This file, if the workflow itself changed.

Report coverage as a number the owner can compare against the last batch:
`categorized X of Y (Z%)` from the Category metrics block, before and after.

And close the loop: ask for the Category metrics screenshot after the owner has
re-run with the new rules, and check "rules that never matched" for anything just
added. A rule in that list was almost certainly mis-transcribed from the picture,
not wrongly conceived.

## Keep a record of what was decided

Rules are judgement calls, and the reasoning is worth more than the regex. When a
batch lands, note anything a later session would otherwise re-litigate — a
wording that looked general but was tool-specific, two faults deliberately kept
apart, an ID that turned out to carry three unrelated messages.

### Batch log

#### Batch 1 — etch3, 5,158 rows, 2026-08-17

Source: four photographs of the verbose debug report. Tool preamble read
`P5000 / Etch / E4.70 / tool etch3 (etch)`, header at line 11, 5158 rows, and the
timestamps used a 2-digit year expanded on the 1969 pivot.

Coverage: **4233 of 5158 (82%), uncategorized 925** before this batch.

The worklist was `top 59 of 59 distinct`, so every uncategorized Event Number was
in frame and the counts below sum to the whole 925. That is why this batch is
large: it is not a sample of the tail, it is all of it.

**No `id:` rules were written, deliberately.** `BUILTIN_CAT_RULES` entries are
`{re, label}` and the built-in loop only tests `re` against the text —
`categorize()` reads `r.ids` for user rules alone. So a built-in cannot key on an
Event Number even where the number is the stabler fact. Separately, several IDs
in the photograph carry leading zeros (`005`, `067`, `068`, `069`, `089`) and an
`id:` rule compares against `String(id).trim()`, so whether the tool holds them
as `005` or `5` decides whether the rule fires. Both reasons point the same way.

Transcribed examples, with the count and severity as read:

| ID | count | sev | example message as transcribed |
|---|---|---|---|
| 448 | 261 | TRACE | `chamber <S4EXT> chamber_abcd_optset state changed to <L1EXT> service_command_optset` |
| 572 | 108 | PROMPT | `chamber <S4EXT> chamber_abcd_optset has completed leak up rate service program` |
| 1029 | 75 | PROMPT | `chamber <S4EXT> chamber_abcd_optset has completed lfc cal service program` |
| 1156 | 56 | WARNING | `<S4EXT> chx_index_optset bad message byte count func_char+colon <L1>` |
| 447 | 49 | TRACE | `system control state changed to <L1EXT> system_state_optset` |
| 1267 | 46 | WARNING | `ocr does not respond check connection` |
| 005 | 28 | WARNING | `system constant out of range func_cut id <L1> has value <L2>` |
| 428 | 24 | FAULT | `link sequence to lot for wafers in cassette <S4EXT> chamber_abcd_optset` |
| 640 | 18 | FAULT | `func_switch undefined_disk_error_text` |
| 1004 | 17 | WARNING | `ozone concentration out of range in ch <S4EXT> chamber_abcd_optset recipe running` |
| 166 | 16 | PROMPT | `completed manual home all loader axes` |
| 456 | 16 | FAULT | `chamber <S4EXT> chamber_abcd_optset detected magnet coil current not changing` |
| 490 | 15 | FAULT | `required endpoint system not present` |
| 726 | 13 | WARNING | `chamber <S4EXT> chamber_abcd_optset lift step <L1> out of range, will use limit of <L2>` |
| 1069 | 12 | PROMPT | `gpc event func_append+colon <S4EXT> gpc_event_optset, status <L1> param <L2> <L3>` |
| 908 | 11 | WARNING | `afx ozone analyzer has gain ratio error` |
| 1003 | 10 | FAULT | `blade has been auto retracted due to some errors had occurred to chamber` |
| 111 | 10 | FAULT | `need to unload to slot func_cut <L1> of cassette <S4EXT> cassette_name_table, is already full` |
| 778 | 10 | FAULT | `ch <S4EXT> chamber_abcd_optset interlock lamp overtemp or out of pos or cover open` |
| 848 | 9 | TRACE | `equipment restart` |
| 1001 | 9 | FAULT | `ch <S4EXT> chamber_abcd_optset crf2 delivered pwr deviation err, delivered pwr <L1> func_char+char_w, limit set <L2> func_char+char_w` |
| 1002 | 9 | FAULT | `some errors had occurred to ch <S4EXT> chamber_abcd_optset; blade being retracted` |
| 446 | 9 | PROMPT | `all processing of wafers is complete` |
| 836 | 9 | FAULT | `orient command error` |
| 997 | 8 | FAULT | `mainframe aux_final <S4> auxiliary final line pressure high fault func_switch rest_of_311` |
| 1119 | 6 | FAULT | `chamber <S4EXT> chamber_abcd_optset cvd - func_char+char_1 microwave pressure too high` |
| 346 | 6 | FAULT | `cover is open error in chamber <S4EXT> chamber_abcd_optset` |
| 367 | 6 | FAULT | `liquid source <S4> temp out of fault tolerance func_cut func_char+colon func_long_2+3 degreesC func_switch ch_p3_paren` |
| 725 | 5 | WARNING | `chamber <S4EXT> chamber_abcd_optset service program has flow with mfc func_cut <L1> too high` |
| 296 | 4 | FAULT | `chamber <S4EXT> chamber_abcd_optset backing pump over temperature fault` |
| 1120 | 3 | FAULT | `chamber <S4EXT> chamber_abcd_optset cvd - func_char+char_1 microwave plasma detector not operational` |
| 1155 | 3 | WARNING | `<S4EXT> chx_index_optset bad message function code or exception response func_char+colon <L1>` |
| 299 | 3 | FAULT | `chamber <S4EXT> chamber_abcd_optset foreline idle pressure is too high` |
| 342 | 3 | FAULT | `ch <S4EXT> chamber_abcd_optset interlock func_append+colon cover open or out of pos or no coolant flow or lamp over temp` |
| 307 | 3 | FAULT | `ch <S4EXT> chamber_abcd_optset turbo purge off - high pressure with trapped process gases` |
| 441 | 3 | TRACE | `func_caps abort selected in reply to a sequencing fault` |
| 527 | 3 | PROMPT | `check system control screen for error recovery options` |
| 089 | 2 | FAULT | `reboot the system after a change to the chamber config` |
| 108 | 2 | FAULT | `cannot extend - indexer not at right level to receive wafer` |
| 142 | 2 | FAULT | `cannot find storage elevator zero pos - check cap sensors` |
| 159 | 2 | FAULT | `there is already a wafer on the blade` |
| 362 | 2 | FAULT | `ch <S4EXT> chamber_abcd_optset process gases stopped - pressure func_cut above func_si_long_1 u_millitorr ...` |
| 513 | 2 | FAULT | `the load lock ch roughing pump is not running` |
| 767 | 2 | PROMPT | `remote liquid source <S4> completed required cleaning time` |
| 866 | 1 | FAULT | `any wafers that were in the sys have been forgotten - inspect and recreate` |
| 067 | 1 | FAULT | `recipe and sequence func_caps selection , lot sequences and wafer lot names lost` |
| 068 | 1 | FAULT | `saved mfc leak up, cal and cycle purge valve selection func_append+char_s - data lost` |
| 069 | 1 | FAULT | `mfc and pressure zero offset func_append+char_s lost, liquid source control will take time` |
| 1151 | 1 | WARNING | `<S4EXT> chx_index_optset bad message start character` |
| 1154 | 1 | WARNING | `<S4EXT> chx_index_optset bad message slave address func_char+colon <L1>` |
| 160 | 1 | FAULT | `rotation lost with wafer on vacuum chuck` |
| 198 | 1 | TRACE | `false motion complete on <S4EXT> stepper_name_table` |
| 356 | 1 | FAULT | `ch <S4EXT> chamber_abcd_optset temp rate of change too low at max power func_switch error_temp_data` |
| 457 | 1 | WARNING | `dummy wafer num. <S4EXT> dummy_wafer_1234_optset reached rf - on time warning level` |
| 557 | 1 | FAULT | `chamber <S4EXT> chamber_abcd_optset turbo not at speed timeout reached` |
| 638 | 1 | FAULT | `func_switch undefined_disk_error_text` |
| 639 | 1 | FAULT | `func_switch undefined_disk_error_text` |
| 746 | 1 | FAULT | `ltc ht ex <S4> temperature deviation fault alarm` |
| 781 | 1 | FAULT | `attempt hi flow cal without high flow cal xducer installed ch <S4EXT> chamber_abcd_optset` |

**Characters that were genuinely ambiguous in the photograph.** Each was kept out
of the regex, so a misreading here cannot produce a dead rule:

- `lfc cal` (1029) — could be `1fc`. Matched on `cal service program`.
- `crf2` (1001) — could be `cfr2`. Matched on `delivered pwr deviation`.
- `rest_of_311` and `aux_final` (997) — matched on
  `auxiliary final line pressure high`.
- `sr2000` / `sr2088` and the `$ffff "` run (362) — matched on
  `process gases stopped`.
- `ltc ht ex` (746) — matched on `temperature deviation fault`.
- `afx` (908) — matched on `ozone analyzer has gain ratio error`.
- `func_long_2+3 degreesC` (367) — matched on `temp out of fault tolerance`.
- Leading zeros on `005`, `067`, `068`, `069`, `089` — irrelevant, no `id:` rules.

The tag placeholders read `<S4EXT>` for chamber and `<L1EXT>` for the optset
values throughout; `<S4>` (no `EXT`) appears on the mainframe and liquid-source
lines. No rule depends on telling them apart.

**Judgement calls worth not re-litigating:**

- **Four wordings were folded into existing or shared labels.** `446`
  (`all processing of wafers is complete`) reuses the built-in **All wafers
  completed** rather than earning a second name for the same event. `1003` and
  `1002` are one fault reported from two directions — blade retracted, and errors
  occurred so the blade is being retracted — and share **Blade retracted after
  chamber error**. `778` and `342` are the same interlock reported with different
  member lists and share **Chamber interlock**. `1151`, `1154`, `1155` and `1156`
  are four framing errors on the same link and share **Chamber index comms
  error**.
- **`1001` was kept apart from the built-in RF forward power error.** Delivered
  power deviating from its setpoint is a different measurement from a forward
  power read error, and merging them would hide which one a tool is actually
  doing. Kept as **RF delivered power deviation**.
- **`346` was kept apart from the interlock rule.** `cover is open error` names
  one member on its own, where `778`/`342` are the compound interlock. A cover
  left open is a different thing to chase than an interlock trip.
- **`572` and `1029` were kept apart.** Both are "a service program finished",
  but leak-up-rate and LFC cal are different maintenance activities with
  different follow-ups, and at 108 and 75 events each they are worth separate
  bars.
- **`089` was kept apart from the built-in System reboot.** That rule is
  `system reboot time down`, a reboot that happened; `089` is a prompt asking for
  one that has not happened yet.
- **The four data-loss messages share one rule.** `866`, `067`, `068` and `069`
  are one event each and all describe state lost across a restart, so they fold
  into **Data lost after restart** rather than four one-row bars.

**Three built-ins matched nothing on this log** and were left in place: PM
trigger reached, Wafer not sensed, and Parameter out of spec. They are not dead
rules, they are rules for logs this run did not cover, so they are expected to
stay on the "rules that never matched" list for this tool.

Everything new was appended to the end of `BUILTIN_CAT_RULES`. Because the
built-in loop is first-hit-wins in array order, appending cannot change how any
of the 4233 already-categorized events are labelled — the batch can only take
from the uncategorized 925.
