#!/usr/bin/env python3
"""Integrity check for the Mirra CSV knowledge base. Schema 3.3."""
# Citation regex accepts the patent part qualifier, e.g. [pat-us6244942 spec].
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
CITE_RE = re.compile(r"\[([a-z0-9]+(?:[-.][a-z0-9]+)+(?:\s+[a-z]+)?(?:\s*[;,]\s*"
                     r"[a-z0-9]+(?:[-.][a-z0-9]+)+(?:\s+[a-z]+)?)*)\]", re.I)

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
