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

**Ask for the clipboard, not a photograph.** The "Copy uncategorized IDs" button
puts the whole worklist on the clipboard as text. Pasted text has exact counts
and exact spelling; a photograph of a screen has neither, and a rule written from
a misread character silently matches nothing. Pictures are fine when that is what
arrives — read them carefully and say which strings were uncertain — but say once
that pasting is better, then work with whatever comes.

### Real log lines

Raw rows are what confirm a pattern is safe. From a picture, transcribe the
example messages into the guide below before writing a regex against them, and
flag any character that could be read two ways (`l`/`1`, `0`/`O`, `<S4EXT>` vs
`<S1EXT>`).

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

## Keep a record of what was decided

Rules are judgement calls, and the reasoning is worth more than the regex. When a
batch lands, note anything a later session would otherwise re-litigate — a
wording that looked general but was tool-specific, two faults deliberately kept
apart, an ID that turned out to carry three unrelated messages.

### Batch log

*(Nothing yet. The first batch of real-log rules goes here.)*
