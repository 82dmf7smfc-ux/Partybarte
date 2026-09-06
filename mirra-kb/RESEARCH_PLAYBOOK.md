# Research playbook

Written after session 1, which was research-starved for one reason: the sandbox
blocked every outbound fetch. The next session almost certainly has different
network policy. This file says how to find that out in the first two minutes,
and what to do with the access once you have it.

---

## 1. Re-test egress first, before planning anything

Do not assume session 1's limits. Do not assume they are gone either. Test.

```bash
for u in https://patents.google.com/patent/US6537133B1/en \
         https://ppubs.uspto.gov/pubwebapp/ \
         https://www.appliedmaterials.com/us/en/product-library/mirra-cmp-200mm.html \
         https://ieeexplore.ieee.org/document/7919822/ \
         https://web.archive.org/ \
         https://nccavs-usergroups.avs.org/ \
         https://scholar.google.com/ \
         https://api.semanticscholar.org/graph/v1/paper/search?query=cmp \
         https://api.crossref.org/works?query=chemical+mechanical+planarization \
         https://api.openalex.org/works?search=chemical+mechanical+planarization ; do
  printf '%s  %s\n' "$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "$u")" "$u"
done
```

`403` from the proxy is an organization policy denial. Do not route around it,
do not retry it, and do not disable TLS verification. Report the blocked host and
work the list below for something that is reachable.

`000` usually means the tool is not using the proxy at all. Check `HTTPS_PROXY`
is set before concluding the host is blocked.

Record the result in `searches.csv` as a row with `where_run=direct-fetch`, the
way session 1 did. A future session should be able to see which hosts were
reachable and when.

If everything is open, the first hour is worth spending on verification rather
than on new nodes. See `NEXT_SESSION.md`.

---

## 2. The single highest-value target: the Wayback Machine

The Mirra shipped around 1997 to 2005. Applied Materials' live pages describe
Mirra Durum, a current SiC product, which is an excluded product and pollutes
every search. The pages that described the actual polisher are gone from the
live web and very likely archived.

```
https://web.archive.org/web/2000*/appliedmaterials.com/products/mirra*
https://web.archive.org/web/2002*/appliedmaterials.com/*cmp*
```

An archived Applied Materials product page or datasheet from 2000 is a tier 1
source and would immediately settle several things session 1 could not: platen
count, endpoint options and which platens carried them, head generations and zone
counts, throughput, and what the 150 mm configuration actually was.

The Wayback CDX API is scriptable and cheap:

```
http://web.archive.org/cdx/search/cdx?url=appliedmaterials.com*&output=json&filter=urlkey:.*mirra.*&collapse=urlkey&limit=200
```

If nothing else on this list works, try this one.

---

## 3. Patents, properly this time

Session 1 could not open a single patent. Every patent claim in the base is a
search summary, and the `spec` and `claims` qualifiers were assigned from
summary wording rather than from the document. That is the weakest thing in the
base after the architecture sourcing.

Routes, in order of preference:

1. **USPTO Patent Public Search** (`ppubs.uspto.gov`), the official full text.
2. **Google Patents** (`patents.google.com/patent/US6537133B1/en`), easiest to
   read, includes the family and forward citations.
3. **PatentsView API** (`api.patentsview.org`), structured, good for assignee
   sweeps.
4. **Espacenet / EPO OPS**, useful when the US text is blocked but the family
   member is not.
5. **patentimages.storage.googleapis.com** for the PDF when HTML is blocked.

Search by **assignee**, not keyword. Applied Materials, filed roughly 1995 to
2005. Then follow the citation trail in both directions, which is where the
useful family members hide.

Named inventors worth sweeping, all found in session 1 summaries:
Steven M. Zuniga (carrier heads and membranes), Manoocher Birang (optical
endpoint), and whoever is on US6886387 (brush cleaning), whose assignee was
never confirmed.

**When you read one, record which part the claim came from.** Background is prior
art, often a competitor, and is not this tool. Specification is an embodiment
that may never have shipped. Claims are what was protected. The contract requires
`[pat-us6537133 spec]` or `[pat-us6537133 claims]` and the validator now checks
those markers, so the qualifier has to be true.

---

## 4. The method session 1 should have used: find papers that ran on a Mirra

This is the highest-yield idea in this file and it costs one search.

Fab and university papers name their equipment in the experimental section.
A paper that says "wafers were polished on an Applied Materials Mirra" gives you
a **tier 2 or tier 3 source making a claim about this specific tool**, which is
exactly what the base is short of. Session 1 has 6 nodes tagged `mirra` and every
one of them rests on vendor material, trade press or an unread patent.

Query shapes:

```
"Applied Materials Mirra" polish experimental
"Mirra" CMP "polisher" site:.edu
"Mirra 3400" OR "Mirra Mesa" removal rate uniformity
"Titan head" OR "Titan Profiler" CMP uniformity
```

Run them on Google Scholar, Semantic Scholar, OpenAlex and Crossref. All four
have free APIs that return abstracts, and Semantic Scholar and OpenAlex return
open-access PDF links when they exist.

The same trick works for the cleaner: `"Mirra Mesa" clean defect` in the
literature rather than in vendor copy.

---

## 5. Open-access routes for the paywalled literature

Session 1 logged five sources as free PDFs and never opened them. That was a
network limit, not a paywall. They are the cheapest wins available:

- `rev-zantye-2004`, the 130-page CMP review, free author copy at eng.usf.edu
- `thesis-lai-mit`, MIT thesis chapter on CMP characterisation
- `mit-boning-cu-damascene`, Boning group copper damascene paper
- `nccavs-feeney-2012`, CMP User Group presentation on non-uniformity
- `entegris-pva-brush`, PVA brush application note

For anything genuinely paywalled, in order: **Unpaywall** (`api.unpaywall.org`,
DOI in, open-access PDF out), the author's own page, the institutional
repository, arXiv, then CORE. Do not use pirate mirrors.

Two archives worth knowing for this subject specifically:

- **NCCAVS CMP User Group** (`nccavs-usergroups.avs.org`) publishes years of
  presentation PDFs free. It is the best CMP-specific free archive there is, and
  session 1 cited one of them without opening it.
- **ECS Transactions and the ECS Journal of Solid State Science and Technology**
  carry most of the STI and ceria chemistry literature.

---

## 6. Improving source strength, concretely

The base currently has zero tier 0 and zero tier 1 sources that were actually
read. Every tier assignment is theoretical. Ways to raise real strength:

**Convert vendor claims into patent claims.** Anything the marketing copy says
about zone control, endpoint or the cleaner has a patent behind it. Find it and
cite the patent's claims instead. That moves a claim from tier 4 to tier 1 and
from an assertion to a protected description.

**Prefer the SEMI standard where one exists.** Uniformity metrics, wafer sizing
and cleanliness definitions are standardised. A standard beats a textbook for
anything definitional.

**Get a second independent source for anything tagged `mirra`.** Right now the
head zone counts have one source and the architecture has two, both tier 4. Two
independent sources at tier 3 or better is the bar for `established`.

**Use the tool itself.** Tier 0 observation is the strongest evidence available
about the machine in front of you and 17 nodes are already routed `on-tool`. One
afternoon with a camera and the service screens would close more `mirra`
questions than a week of searching. Remember the rules: it settles the claim for
that tool only, it can raise `confidence_mirra` and never `confidence`, and it
needs `observed_on` recording which tool and when.

**Chase the part numbers.** Session 1 found `0010-24500 Mirra Titan II Profiler
200mm` and `0010-77533 200mm MIRRA Titan 1 HEAD` in dealer listings. Part numbers
are checkable against parts catalogues and refurbisher sites, and they are
evidence that Titan I and Titan II are distinct generations and that a 200 mm
Profiler existed. Tier 5 as a citation, but excellent as a lead.

---

## 7. Improving source variation

The current register is lopsided: 31 sources, of which 26 are search snippets and
5 were never seen at all. Categories that are entirely missing and should not be:

| Missing category | Why it matters | Where to look |
|---|---|---|
| Tier 0 observation | The one kind of evidence nobody else can get | The tool |
| Read patents | The primary machine-specific source per the contract | See section 3 |
| SEMI standards | Definitions that beat everyone's prose | SEMI, paid, note both |
| Archived OEM pages | Tier 1 statements about the real product | Wayback, section 2 |
| Papers run on a Mirra | Tier 2 or 3 claims about this tool | Section 4 |
| Service and training material | Alarm codes, screens, procedures | Likely unobtainable, confirm and record as `unknowable` |
| Conference presentations | Free, specific, often with real numbers | NCCAVS CMP UG archive |

A healthy register for this project would be patents and archived OEM pages for
the tool, peer-reviewed literature for the physics, presentations for practice,
and observation for anything the machine can answer directly. Dealer listings and
trade press are leads, and should stay leads.

---

## 8. What not to do

- Do not cite a source you have not opened. If you must record the claim, set
  `access` honestly and say so in the prose. The validator now blocks
  `confidence_mirra=established` when everything behind it is unread.
- Do not let a summary's confident phrasing become your confident phrasing. A
  search summary can merge two documents into one sentence. Session 1's head
  zone counts may be exactly that.
- Do not accept a result about Mirra Trak, Mirra DNS, Desica, Mirra Durum,
  Reflexion or Reflexion LK as being about this tool. Say which product the
  source described and cap `confidence_mirra` at probable when a finding
  transfers.
- Do not re-run a search that is already in `searches.csv` with outcome `empty`
  unless enough time has passed. That is what the new `date` column is for.
