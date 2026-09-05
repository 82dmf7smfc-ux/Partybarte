# Mirra Knowledge Base: Option B, CSV plus Markdown

Storage: flat CSV index files, one Markdown file per node for prose.
Reader: `mirra-kb-reader.html` v3.3, kept in the same folder.
Editing: any text editor. Excel only with care, see section 10.
Schema version: 3.3

Version 5. Adds claim-level citations, scope tagging, split confidence,
contested claims, a patent reading rule, a search log, and Stage 0.
Also adds the clean domain, applies_to, head_gen, and an exclusion list.
Every rule here matches Option A. Only the storage differs.

---

## 1. Why this is not a plain CSV pair

Nodes plus edges as two CSVs works until the prose arrives. So this option
splits the difference:

- CSVs hold short structured fields only.
- Each node gets its own Markdown file for the long text.
- `validate.py` checks that the links between them stay valid.

Everything stays human readable and git friendly, which is the real reason
to pick this over a database.

The reader parses quoted multi-line CSV and sniffs the delimiter, so a
stray comma is no longer fatal. Keeping commas out of CSV fields is still
the easy path, especially if you ever open them in Excel.

---

## 2. Project prompt

Paste this block at the start of a new project or session.

```
GOAL
Build a linked knowledge base of the terms an expert engineer must know,
understand, and apply on Applied Materials Mirra CMP systems in standalone
150 mm and 200 mm configurations.

"Expert" means able to:
- diagnose a fault from tool behavior
- set and defend a recipe parameter
- predict how a change affects removal rate, uniformity, and defectivity

TARGET SIZE
Roughly 400 to 550 nodes across five domains, with the clean domain at
parity with the polisher. Four polish applications are in scope, so the
consumables domain is the one most likely to overrun. If any domain heads
past 140, say so rather than continuing.

CONSTRAINTS
- Public sources only. I have no OEM manuals.
- Applied Materials patents are the primary machine-specific source.
- Never invent a specification. Unknown is a valid and expected answer.

DOMAINS IN SCOPE
1. hardware      Polisher hardware and subsystems
2. consumables   Pads, slurries, conditioning, chemistry
3. process       Process physics and metrology
4. controls      Control software, alarms, facilities
5. clean         Post-CMP cleaning, only on Mirra Mesa. Full depth,
                 at parity with the polisher domains.

CONFIGURATIONS IN SCOPE
Standalone Mirra polisher, 150 mm and 200 mm. Dry-in, wet-out.
Mirra Mesa, the same polisher with the integrated Mesa cleaner, dry-in,
dry-out.
Every node carries applies_to:
  polisher  true of the polisher, present on both configurations
  mesa      true only of the cleaner, absent on a standalone tool
  both      spans the two, for example wafer handoff and scheduling
Default is polisher. Only tag mesa when the claim is about the cleaner.

HEAD GENERATIONS
Standard Titan and Titan Profiler heads are both in scope, and custom
head configurations exist on real tools. Head behaviour is the largest
single variable on this platform. Any node about the head, membrane,
retaining ring, zone pressure, or profile control carries head_gen:
  titan           standard Titan head only
  titan-profiler  Titan Profiler only
  either          true of both
  custom          a modified configuration, see below
  unknown         you could not determine it. Say so rather than guessing.
Never write a head claim without head_gen. "The Mirra head does X" is not
a checkable statement.

CUSTOM CONFIGURATIONS
Custom heads and modified tools are not documented in any public source,
by definition. So a custom claim can never be cited. Handle it this way:
- Write the OEM baseline as the node body, cited normally.
- Put the deviation in a "## Custom configurations" section, labelled
  "Observed, not sourced:" with whatever context is known.
- Set head_gen to custom only when the whole node is about a modification.
Never let an observed deviation quietly overwrite the documented baseline.
The baseline is what a future reader needs in order to recognise that a
tool in front of them is not standard.

FIRST-HAND OBSERVATION
I have regular hands-on access to a real tool. That adds a source type
'observation' at tier 0, and it comes with strict rules:
- Tier 0 is authoritative for the tool that was observed and for nothing
  else. One tool is not the platform. Never let an observation raise the
  general 'confidence' field. It may raise 'confidence_mirra'.
- Every observation source records observed_on: which tool, and when.
- A node cited only to tier 0 must carry head_gen and applies_to. An
  untagged observation cannot be checked against anything later.
- Observation settles a contested claim for one tool. It does not delete
  the disagreement. Keep the contested section and note what was seen.
- Do not ask me to observe something as a condition of writing a node.
  Write the node, mark verify='on-tool', and I will get to it.

ROUTING EVERY GAP
Every node with unknown values or uncertain confidence carries verify:
  on-tool     answerable by inspection, measurement, or a service screen
  research    a public source probably exists, not found yet
  unknowable  confirmed unavailable publicly and not observable
Default to on-tool when the answer is physically present on the machine.
This turns the Gaps tab from a list of failures into a work list.

POLISH APPLICATIONS IN SCOPE
All four, so slurry and defect chemistry go deep rather than generic.
Every node carries applications, semicolon separated, from:
  oxide-sti  tungsten  copper  silicon-poly  all
Use 'all' only when the term is genuinely application independent, like
platen speed. Slurry, oxidizer, pH, dishing, erosion, and most post-CMP
defect terms are application specific. Splitting a term per application is
usually better than one node hedged four ways.

EXCLUDED, AND THEY WILL POLLUTE YOUR SEARCHES
These are different products. Reject results about them and say so:
  Mirra Trak / MirraTrak   integrated with the OnTRAK Integra cleaner
  Mirra DNS                integrated with the DNS AS-2000 cleaner
  Desica                   a different cleaner option, Marangoni drying
  Mirra Durum              current SiC variant, dominates live AMAT pages
  Reflexion / Reflexion LK 300 mm successor platform
Shared polisher architecture means some findings do transfer. When one
does, say which product the source was describing and tag confidence_mirra
no higher than probable.

SCOPE TAGGING
Every node carries a specificity value. This is the most important field
in the schema, because the whole point of the project is separating what
is true of this machine from what is true of polishing in general.
  general  physics or engineering that is not specific to CMP
  cmp      applies to CMP broadly, any vendor
  mirra    specific to this tool family
Do not tag a node 'mirra' unless a source actually ties the claim to the
tool. Wanting it to be Mirra specific is not evidence.

CONFIDENCE, SPLIT
  confidence        how sure you are about the general concept
  confidence_mirra  how sure you are that it applies to this tool
These routinely differ. A textbook definition with a guessed tool
application is confidence=established, confidence_mirra=uncertain. Never
let a strong general confidence carry a weak tool claim.

WAFER SIZE
Treat 150 mm versus 200 mm as an attribute on a node, not a separate tree.
Only fill wafer_note where the difference is real. Otherwise write na.

STORAGE
Flat files. Structure is given in section 5.
- nodes.csv, edges.csv, sources.csv, citations.csv, searches.csv
- nodes/<id>.md for prose

CSV RULES
- Keep commas, quotes and line breaks out of CSV fields. Prose belongs in
  the .md file. Use a semicolon if you need a separator inside a field.
- Column order never changes.

OUTPUT CONTRACT
Every batch comes back in this order, each block labelled with its
filename and nothing else between blocks:
  1. Rows to append to sources.csv     new sources first
  2. Rows to append to nodes.csv
  3. Rows to append to edges.csv
  4. Rows to append to citations.csv
  5. Rows to append to searches.csv
  6. Full contents of each nodes/<id>.md file
Then a short note on anything you were unsure of.

CITATIONS, AT CLAIM LEVEL
Put the source id inline, in square brackets, at the end of the sentence
it supports: "... removal there climbs [stg-1997]." Several sources go in
one bracket separated by semicolons.
citations.csv stays as the field-level index. The inline markers are what
tell future-me which sentence rests on what. A paragraph with one marker
at the end is not a cited paragraph, it is one cited sentence and several
uncited ones. Mark each claim.
An unsourced sentence is allowed only when it is your own synthesis, and
it must say so: "Inferred, no source: ..."

READING PATENTS
A patent has three parts and they are not equally trustworthy:
  Background     describes prior art, often a competitor. Not this tool.
  Specification  describes an embodiment that may never have shipped.
  Claims         describes what was protected, which is narrower than the
                 specification and is the strongest statement about intent.
Always say which part a claim came from: [pat-us5738574 spec] or
[pat-us5738574 claims]. Never cite a patent as if it documents the shipped
machine. Assignee and filing date are not proof the feature reached
production.

CONTESTED CLAIMS
When two credible sources disagree, do not pick a winner silently. Add a
"## Contested" section to the node file with both positions and their
source ids. Recording a disagreement is a research result.

SOURCE TIERS
T0  First-hand observation of a real tool. Scoped to that tool only.
T1  AMAT patents and published applications, SEMI standards, AMAT public specs
T2  Peer reviewed CMP literature and textbooks
T3  University theses, conference papers, national lab reports
T4  Vendor application notes and white papers. Flag marketing claims.
T5  Forums, auction listings, undated PDFs. Leads only. Never a cited fact.

RULES
- No claim without an inline source marker, or an explicit inferred label.
- Never blend a T4 claim into a T1 statement without saying so.
- If a source is paywalled, find a credible free alternative. Note both.
- Search patents by assignee, not keyword alone.
- A causes or mitigates edge asserts a mechanism. Give it a source_id.
- Every equation defines every variable with units at the point it appears.
- Write ordinary Markdown in the .md files. Tables, numbered lists, and
  links all render.
- Log every search you run in searches.csv, including the ones that found
  nothing. Empty results are the expensive thing to rediscover.
- No em dashes. Short sentences.

WORKING STYLE
- Batches of about 20 nodes.
- Never renumber or reuse an id.
- Ask before adding a new node type or relation type.
- Suggest what to do next, but I decide the order. Do not gate anything.
```

---

## 3. Stage plan

| Stage | Output | Reader shows it as |
|---|---|---|
| 0 | Tool identity fixed | A short written answer, no nodes yet |
| 1 | sources.csv | Sources tab fills up |
| 2 | nodes.csv | Sidebar fills, most nodes red |
| 3 | edges.csv | Orphan count drops toward zero |
| 4 | nodes/*.md | Coverage bars move |
| 5 | Gap closure | Gaps tab stops shrinking |

Stages 1 through 5 overlap. Stage 0 does not.

### Stage 0, before any terms

Mostly settled. The polisher core is three polishing platens with four
wafer carriers on a carousel, one to three polishing steps, 150 mm and
200 mm. Base Mirra is dry-in, wet-out. Mirra Mesa is the same polisher
made dry-in, dry-out by the integrated Mesa cleaner. Heads in scope are
standard Titan, Titan Profiler, and custom configurations.

What Stage 0 still owes you, from public sources, in writing:

1. Which head generation shipped when, and what actually differs between
   Titan and Titan Profiler in zone count and control.
2. What the Mesa cleaner's wafer path is, station by station, and which
   of those stations exist on the 150 mm version.
3. Which endpoint options were offered, and on which platens.
4. What changes between the 150 mm and 200 mm configurations beyond the
   obvious change parts.
5. What is genuinely unknowable from public sources.

Answer five honestly. That list is the boundary of the whole project.
Everything past it is observation, not research, and files as custom or
uncertain.

Record the answers in `SCOPE.md` and move on.

---

## 4. Housekeeping

**Backups.** Git is the backup. Commit after every validated batch.

```bash
python3 validate.py && git add -A && git commit -m "session N: <topic>"
```

If you are not using git, keep dated copies of the whole folder instead.
A single bad find-and-replace across `nodes/` is otherwise unrecoverable.

**Schema version.** 3.3, recorded at the top of this file and in
`SCOPE.md`. If you change a column, bump it, note it in SESSION_LOG.md,
and check whether the reader still matches.

---

## 5. File structure

```
mirra-kb/
  nodes.csv
  edges.csv
  sources.csv
  citations.csv
  searches.csv
  nodes/
    retaining-ring.md
    preston-equation.md
    ...
  validate.py
  mirra-kb-reader.html        v3.3
  SCOPE.md                    Stage 0 output, schema version
  PROMPT.md                   this file
  STATE.md                    overwritten each session
  SESSION_LOG.md              append only
  NEXT_SESSION.md             generated at the end of each session
```

### nodes.csv

```
id,term,aliases,type,domain,specificity,applies_to,head_gen,applications,verify,gloss,value_status,confidence,confidence_mirra,wafer_note,updated_session
```

| Column | Rule |
|---|---|
| `id` | Lowercase, hyphenated. Never changes. |
| `term` | Display name. Title case. |
| `aliases` | Semicolon separated. `retainer ring;retainer` |
| `type` | concept, subsystem, component, consumable, principle, equation, parameter, signal, failure_mode, metric, procedure, standard |
| `domain` | hardware, consumables, process, controls, clean |
| `specificity` | mirra, cmp, general. Drives a filter row in the reader. |
| `applies_to` | polisher, mesa, both. Default polisher. Drives a second filter row once any Mesa node exists. |
| `head_gen` | titan, titan-profiler, either, custom, unknown, or blank. Required on any head, membrane, ring, or zone node. |
| `applications` | Semicolon separated from oxide-sti, tungsten, copper, silicon-poly, all. Drives a filter row. |
| `verify` | on-tool, research, or unknowable. Groups the Gaps tab into three work lists. |
| `gloss` | One line. Renders large under the title and is the main search text. |
| `value_status` | published, inferred, unknown |
| `confidence` | established, probable, uncertain. The general concept. |
| `confidence_mirra` | established, probable, uncertain, or blank if there is no tool claim. Renders as a badge on the On the Mirra heading. |
| `wafer_note` | `na` unless the difference is real. |

`contested` is not a column. It lives as a `## Contested` section in the
node file, because it is prose. The reader picks it up from there and
renders it as a banner.

The reader accepts a few alternative column names so a rename does not
break your afternoon. Stick to the list above anyway.

### edges.csv

```
from_id,to_id,relation,source_id,note
```

`relation` is one of: part_of, governed_by, measured_by, controlled_by,
causes, mitigates, trades_off_with, prerequisite_for, alias_of,
contrasted_with

**Direction matters.** `from_id` is the subject.

```
retaining-ring,carrier-head,part_of,,
```

reads "retaining ring is part of carrier head". The reader shows the
reverse on the other node as "contains". Get it wrong and both pages read
backwards.

A `causes` or `mitigates` edge asserts a mechanism. Fill `source_id`. The
reader lists the ones you did not.

### sources.csv

```
id,title_slug,author_or_assignee,year,source_type,url,access,tier,observed_on
```

`source_type` includes `observation` for first-hand findings, which take
tier 0 and must fill `observed_on` with the tool and date.

`title_slug` uses hyphens instead of spaces to keep commas out. The reader
turns hyphens back into spaces when a value has no spaces of its own. A
plain `title` column with real spaces also works.

### citations.csv

```
node_id,source_id,field
```

`field` is one of: definition, mirra_application, physics, typical_values,
general. This is the coarse index. The inline `[src-id]` markers in the
prose are the fine one. Both matter.

### searches.csv

```
session,query,where_run,outcome,note
```

`outcome` is hit, thin, or empty. The empty rows are the valuable ones.
Without them you will re-run the same fruitless patent query three
sessions from now.

### nodes/&lt;id&gt;.md

The reader splits on headings and matches them to slots:

| Heading | Where it appears |
|---|---|
| Definition | Definition |
| Mirra application, On the Mirra, Application | On the Mirra |
| Physics, Theory, How it works | Physics |
| Typical values, Values, Ranges | Typical values |
| Contested, Sources disagree, Dispute | Contested banner |
| Custom configurations | Kept as its own section, unmapped by design |
| Observed | Kept as its own section. Use for first-hand findings. |
| Open questions, Questions, Unknowns | Open questions |
| Relations, Sources | Ignored, these come from the CSVs |

**Any other heading is kept, not dropped.** It renders as its own section
under the heading you wrote.

```markdown
---
id: retaining-ring
term: Retaining Ring
---

## Definition
A ring surrounding the wafer inside the head [stg-1997]. It stops the
wafer sliding out, and it presses the pad down just outside the wafer
edge [pat-us5738574 spec].

## Mirra application
A consumable that wears in use. Inferred, no source: wear should change
the edge pressure profile, since the ring load path runs through it.

## Physics
The ring compresses the pad ahead of the wafer edge [stg-1997].

## Contested
Two sources give different ring load ranges [zan-2004; some-appnote].
Neither states the head generation, so they may not be comparable.

## Custom configurations
Observed, not sourced: some tools run a non-OEM ring profile. Record what
you saw and on which tool. This never overwrites the baseline above.

## Open questions
- What is the published wear limit for the 200 mm ring?
```

Text before the first heading becomes the definition. Frontmatter is
stripped and ignored.

### id convention

Nodes: `retaining-ring`, `preston-equation`.
Sources: `pat-us5738574`, `book-steigerwald-1997`, `semi-m1`.

Never change an id. If a term is renamed, update `term` and add the old
name to `aliases`.

---

## 6. How the reader reads your prose

Write ordinary Markdown. Headings, numbered lists, bullet lists, tables,
links, blockquotes, code fences, bold and italic all render. Nothing is
silently dropped.

Three things happen automatically.

**Inline citations become chips.** `[stg-1997]` renders as a small tag. If
the id is not in sources.csv it turns red, so a typo or a citation to a
source you forgot to log is visible on the page.

**Equations are detected and set apart.** A line whose left side is a bare
symbol and whose right side is symbols and operators becomes a monospace
box. Consecutive equation lines group into one box.

**Variable definitions become a definition list.** A line whose left side
is a bare symbol and whose right side is words becomes a two-column entry.
So this input:

```
MRR = k_p × P × v

MRR = material removal rate, nm/min
k_p = Preston coefficient, fitted rather than derived
P = applied pressure at the wafer surface, kPa
v = relative velocity between wafer and pad, m/s
```

renders as one equation box followed by a four-row definition list. No
special syntax. If detection guesses wrong, a fenced block tagged `eq`
forces it.

### Notation

- Subscripts with an underscore: `k_p`, `C_m`, `t_r`
- Numeric subscripts as Unicode: `ε₀`
- Compound subscripts with a comma and no space: `ε_r,eff`
- Multiplication always explicit: `×` or `·`, never adjacency

### What the reader flags

Red on a node page: orphan, uncited, broken link, missing prose file.
Listed in Health: contested, unsourced causal edges, terms tagged mirra
with nothing written in the Mirra section, terms resting on tier 4 or 5.

---

## 7. validate.py

The reader catches problems visually. This catches them in bulk and gives
a clean exit code for a git hook.

```python
#!/usr/bin/env python3
"""Integrity check for the Mirra CSV knowledge base. Schema 3.3."""
import csv, os, re, sys, collections

TYPES = {"concept","subsystem","component","consumable","principle",
         "equation","parameter","signal","failure_mode","metric",
         "procedure","standard"}
DOMAINS = {"hardware","consumables","process","controls","clean"}
SPECS = {"mirra","cmp","general"}
VERIFY = {"on-tool","research","unknowable"}
APPS = {"oxide-sti","tungsten","copper","silicon-poly","all"}
APPLIES = {"polisher","mesa","both"}
HEADS = {"titan","titan-profiler","either","custom","unknown"}
HEAD_WORDS = re.compile(r"head|membrane|ring|zone|profil|carrier", re.I)
RELATIONS = {"part_of","governed_by","measured_by","controlled_by","causes",
             "mitigates","trades_off_with","prerequisite_for","alias_of",
             "contrasted_with"}
CAUSAL = {"causes","mitigates"}
FIELDS = {"definition","mirra_application","physics","typical_values","general"}
TIERS = {"0","1","2","3","4","5"}
CONF = {"established","probable","uncertain"}
STATUS = {"published","inferred","unknown"}
CITE_RE = re.compile(r"\[([a-z0-9]+(?:[-.][a-z0-9]+)+(?:\s*[;,]\s*"
                     r"[a-z0-9]+(?:[-.][a-z0-9]+)+)*)\]", re.I)

errs, warns, info = [], [], []

def load(name):
    if not os.path.exists(name): return []
    with open(name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

nodes, edges = load("nodes.csv"), load("edges.csv")
sources, cites = load("sources.csv"), load("citations.csv")
node_ids = set(); src_ids = set()

for nid, c in collections.Counter(n["id"] for n in nodes).items():
    if c > 1: errs.append(f"duplicate node id: {nid}")

for n in nodes:
    node_ids.add(n["id"])
    for col, ok in (("type",TYPES),("domain",DOMAINS),("specificity",SPECS),
                    ("applies_to",APPLIES),("confidence",CONF),("value_status",STATUS)):
        if n.get(col,"") not in ok:
            errs.append(f"{n['id']}: bad {col} '{n.get(col,'')}'")
    hg = n.get("head_gen","")
    if hg and hg not in HEADS:
        errs.append(f"{n['id']}: bad head_gen '{hg}'")
    if not hg and n.get("domain") == "hardware" and HEAD_WORDS.search(n["term"]):
        warns.append(f"{n['id']}: head related but head_gen is blank")
    if n.get("domain") == "clean" and n.get("applies_to") != "mesa":
        warns.append(f"{n['id']}: clean domain but applies_to is not mesa")
    v = n.get("verify","")
    if v and v not in VERIFY:
        errs.append(f"{n['id']}: bad verify '{v}'")
    if not v and (n.get("value_status") == "unknown"
                  or n.get("confidence") == "uncertain"):
        warns.append(f"{n['id']}: gap with no verify routing")
    bad = [a for a in re.split(r"[;,|]", n.get("applications","")) if a.strip()
           and a.strip() not in APPS]
    if bad:
        errs.append(f"{n['id']}: unknown application(s) {bad}")
    cm = n.get("confidence_mirra","")
    if cm and cm not in CONF:
        errs.append(f"{n['id']}: bad confidence_mirra '{cm}'")
    if n.get("specificity") == "mirra" and not cm:
        warns.append(f"{n['id']}: tagged mirra but confidence_mirra is blank")
    if len(n.get("gloss","")) > 110:
        warns.append(f"{n['id']}: gloss is {len(n['gloss'])} chars, keep it short")

for s in sources:
    src_ids.add(s["id"])
    if s["tier"] not in TIERS: errs.append(f"{s['id']}: bad tier '{s['tier']}'")

linked = set()
for e in edges:
    for side in ("from_id","to_id"):
        if e[side] not in node_ids:
            errs.append(f"edge points at missing node: {e[side]}")
    if e["relation"] not in RELATIONS:
        errs.append(f"bad relation '{e['relation']}' on {e['from_id']}")
    if e["relation"] in CAUSAL and not e.get("source_id"):
        warns.append(f"unsourced causal edge: {e['from_id']} {e['relation']} {e['to_id']}")
    if e.get("source_id") and e["source_id"] not in src_ids:
        errs.append(f"edge cites missing source: {e['source_id']}")
    linked.add(e["from_id"]); linked.add(e["to_id"])

cited = set()
for c in cites:
    if c["node_id"] not in node_ids:
        errs.append(f"citation for missing node: {c['node_id']}")
    if c["source_id"] not in src_ids:
        errs.append(f"citation to missing source: {c['source_id']}")
    if c.get("field") and c["field"] not in FIELDS:
        errs.append(f"bad citation field '{c['field']}' on {c['node_id']}")
    cited.add(c["node_id"])

MAPPED = {"definition","mirra application","on the mirra","application",
          "physics","theory","how it works","typical values","values","ranges",
          "contested","sources disagree","dispute","custom configurations","observed",
          "open questions","questions","unknowns","relations","sources"}
custom = collections.Counter()
inline_used = set()
for nid in sorted(node_ids):
    path = f"nodes/{nid}.md"
    if not os.path.exists(path):
        warns.append(f"no prose file: {path}")
        continue
    text = open(path, encoding="utf-8").read()
    for line in text.split("\n"):
        if line.startswith("#"):
            h = line.lstrip("#").strip().lower()
            if h and h not in MAPPED: custom[h] += 1
    found = CITE_RE.findall(text)
    for group in found:
        for sid in re.split(r"\s*[;,]\s*", group):
            sid = sid.split()[0]           # strip 'spec' / 'claims' qualifier
            inline_used.add(sid)
            if sid not in src_ids:
                errs.append(f"{nid}: inline citation to unknown source '{sid}'")
    body = re.sub(r"^#.*$", "", text, flags=re.M).strip()
    if len(body) > 300 and not found:
        warns.append(f"{nid}: {len(body)} chars of prose and no inline citations")

for f in os.listdir("nodes"):
    if f.endswith(".md") and f[:-3] not in node_ids:
        errs.append(f"orphan prose file: nodes/{f}")

for nid in sorted(node_ids - linked): warns.append(f"orphan node, no edges: {nid}")
for nid in sorted(node_ids - cited):  warns.append(f"uncited node: {nid}")
for sid in sorted(src_ids - inline_used - {c['source_id'] for c in cites}):
    info.append(f"source logged but never used: {sid}")

spread = collections.Counter(n.get("specificity","") for n in nodes)
appl   = collections.Counter(n.get("applies_to","") for n in nodes)
heads  = collections.Counter(n.get("head_gen","") for n in nodes if n.get("head_gen"))
print(f"nodes {len(nodes)}  edges {len(edges)}  sources {len(sources)}  "
      f"citations {len(cites)}")
print("scope:  " + "  ".join(f"{k} {v}" for k, v in spread.most_common()))
print("config: " + "  ".join(f"{k} {v}" for k, v in appl.most_common()))
route = collections.Counter(n.get("verify","unrouted") or "unrouted" for n in nodes)
print("gaps:   " + "  ".join(f"{k} {v}" for k, v in route.most_common()))
obs = {s["id"] for s in sources if s.get("source_type") == "observation"}
for s in sources:
    if s.get("source_type") == "observation" and not s.get("observed_on"):
        warns.append(f"{s['id']}: observation source with no observed_on")
by_node = collections.defaultdict(set)
for c in cites: by_node[c["node_id"]].add(c["source_id"])
for nid, ss in by_node.items():
    if ss and ss <= obs:
        n = next((x for x in nodes if x["id"] == nid), {})
        if not n.get("head_gen"):
            warns.append(f"{nid}: observation-only and no head_gen")
if heads:
    print("heads:  " + "  ".join(f"{k} {v}" for k, v in heads.most_common()))
for w in warns: print("WARN ", w)
for e in errs:  print("ERROR", e)
for i in info:  print("INFO ", i)
if custom:
    print("\nCustom headings in use, rendered as their own sections:")
    for h, n in custom.most_common(): print(f"  {n:>3}  {h}")
print(f"\n{len(errs)} errors, {len(warns)} warnings")
sys.exit(1 if errs else 0)
```

Two checks earn their keep. The inline citation check catches a marker
pointing at a source id you never logged. The prose-without-citations
check catches an entry that reads authoritatively and rests on nothing.

The custom heading report tells you when the schema is missing a slot. If
the same unmapped heading appears on thirty nodes, promote it to a real
field rather than leaving it loose.

---

## 8. Carry-through documentation

### STATE.md

```markdown
# State as of session N, YYYY-MM-DD
Schema version: 3.3   Reader version: 3.3

## Tool identity, from Stage 0
See SCOPE.md. Summary: ...

## Counts, from the reader Health tab
Terms: X   Connections: Y   Sources: Z   Written up: W

## Scope
mirra X   cmp X   general X
polisher X   mesa X   both X
Mirra terms with uncertain confidence_mirra: X
Head nodes with no head_gen: X          Custom configuration notes: X
Observation-only nodes: X               Unrouted gaps: X

## Gap routing
on-tool X    research X    unknowable X

## By domain
hardware     X terms, X written, X uncertain
consumables  ...
process      ...
controls     ...
clean        ...

## Validator
Last run: clean / X errors / X warnings
Unresolved warnings: list them
Custom headings appearing often: list them

## Current focus
One or two lines.

## Known dead ends
Confirmed unfindable in public sources. Stop looking here.
```

### SESSION_LOG.md

Append only. One entry per session. Never edit an old entry.

```markdown
## Session N, YYYY-MM-DD, focus: <topic>
Added: <n> nodes, <n> edges, <n> sources, <n> searches logged
Key finds: two or three lines
Corrections: any earlier node revised, and why
Contested found: any new disagreement between sources
Validator issues: anything flagged and what caused it
Tooling changes: any edit to the reader, validate.py, or the columns
Commit: <hash>
```

The tooling-changes line is the one people skip. The reader, this prompt,
and validate.py have to agree. If you change one, note it, or a future
session works from a stale contract.

---

## 9. End of session handoff

```
END OF SESSION PROTOCOL
When I say "wrap up", do all of the following in order:

1. Remind me to run validate.py. Ask for the output.
2. Ask me for the reader's Health tab numbers.
3. Emit the full replacement text for STATE.md.
4. Emit the append block for SESSION_LOG.md.
5. Emit NEXT_SESSION.md using the template below.
6. Suggest a git commit message.
7. List anything you are unsure about that I should verify myself, and
   anything I may have over-claimed as Mirra specific.

Do not skip step 7.
```

### NEXT_SESSION.md template

```markdown
# Next session prompt, session N+1

## Paste this at the start
I am continuing the Mirra CMP knowledge base build.
Attached: PROMPT.md, SCOPE.md, STATE.md, nodes.csv, sources.csv, edges.csv.
Read all of them before responding.

Last session covered: <one line>
This session focus: <one line>

## Objectives, in order
1. <specific and finishable>
2. <specific and finishable>
3. <specific and finishable>

## Open questions carried forward
- <question>, blocked on <what>

## Searches to run
- <exact query string>, on <where>

## Searches already run and empty
- <exact query string>, on <where>

## First action
<the single first thing to do, no ambiguity>
```

A good objective is "fill the Physics section for the eight pad
conditioning nodes". A bad objective is "work on consumables".

---

## 10. Working with the files

**Serving beats picking.** Run `python3 -m http.server 8000` in the folder
and open `http://localhost:8000/mirra-kb-reader.html`. The reader loads
everything on refresh, so the edit-refresh loop is two seconds. It fetches
the node files in parallel batches, so this stays fast at a few hundred
nodes.

CSV mode never touches the network. That is a real advantage over SQLite
mode, which fetches an engine the first time.

**Excel will try to help.** It reformats numbers and turns anything
date-shaped into a date. A value like `2-3` becomes `2-Mar`. Either never
open these in Excel, or import as text every time.

**Consider TSV.** Tabs almost never appear in your text. The reader sniffs
the delimiter already, so switching costs one line in `validate.py`.

---

## 11. Suggestions

**Run Stage 0 and one real batch before committing to this option.** Tool
identity into SCOPE.md, then twenty nodes on the physics spine, validate,
then a wrap up and a cold restart from the generated prompt.

**Watch the specificity split as your honesty meter.** If 80 percent of
your nodes are tagged `cmp` and `general`, that is not a failure. It is the
accurate picture of what public sources give you. If the `mirra` share
looks high, the likely cause is wishful tagging rather than good research.

**Separate the skeleton pass from the prose pass.** Add 20 bare nodes with
gloss and edges, then look at the reader. Seeing the shape of the web
before writing prose usually changes which terms you think matter.

**Build the physics spine first.** Six principle nodes before anything
else: Preston relation, contact and lubrication regime, slurry transport,
pad asperity mechanics, planarization length scale, endpoint detection.
Every hardware and consumable node then hangs off one with `governed_by`.

**Expect the controls domain to stay thin.** Alarm codes and software
behavior are the weakest area in public sources. Build the structure,
accept the uncertainty, and mark that branch as needing insider
verification rather than grinding on it.

**Head generation is where over-claiming will happen.** Titan and Titan
Profiler share a name in every source that mentions either. If you cannot
tell which one a claim describes, `head_gen` is `unknown`, not `either`.
Those two mean different things and only one of them is honest.

**Keep the custom notes separate from the baseline.** A modified tool is
the one in front of you, but the OEM baseline is what lets a future reader
tell that it is modified. Losing the baseline costs more than losing the
modification.

**Observation is a source, not a shortcut.** Tier 0 is the strongest
evidence you will ever have about the tool in front of you and the weakest
about the platform. The failure mode is generalising one tool into a fact
about all Mirras. If you catch yourself writing "the Mirra does X" from
something you saw once, that is a `head_gen` and `applies_to` claim, not a
platform claim.

**Route gaps before you research them.** Sorting the gap list into on-tool,
research, and unknowable takes ten minutes and saves whole sessions. A
question you can answer by walking to the machine should never consume a
search budget.

**Patents are the workhorse and the main risk.** Assignee Applied
Materials, filed roughly 1995 to 2005. Follow the citation trail both
directions. Always record which part of the patent a claim came from. A
specification embodiment is a description of an idea, not of a machine
anyone shipped.

**Consider Obsidian alongside the reader.** It reads the `nodes/` folder
with no import step. The reader gives you scope, health and tier views
Obsidian cannot. Obsidian gives you an editing environment the reader does
not.
