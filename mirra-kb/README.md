# Mirra knowledge base

A linked knowledge base of the terms an expert engineer needs on Applied
Materials Mirra CMP systems, in standalone 150 mm and 200 mm configurations.
Storage is flat CSV plus one Markdown file per node. See `PROMPT.md` for the
full contract, schema and working rules.

## Reading it

```bash
python3 -m http.server 8000
```

Then open http://localhost:8000/mirra-kb-reader.html. The reader loads the CSVs
and the node files on refresh. It makes no network calls in CSV mode.

## Checking it

```bash
python3 validate.py
```

Exit code 0 means no errors. Run it before every commit.

## Layout

| Path | What it is |
|---|---|
| `nodes.csv` | One row per term, short structured fields only |
| `edges.csv` | Relations between terms, direction matters |
| `sources.csv` | Every source, with tier and access |
| `citations.csv` | Coarse node to source index by field |
| `searches.csv` | Every search run, including the empty ones |
| `nodes/<id>.md` | The prose for one term |
| `COLD_START.md` | Paste this into a fresh session to resume |
| `HANDOFF.md` | What is verified, what is not, what to do next |
| `LESSONS.md` | What the tooling caught and why the schema looks like this |
| `RESEARCH_NOTES.md` | The search summaries every citation actually rests on |
| `RESEARCH_PLAYBOOK.md` | How to find stronger sources, starting with an egress test |
| `SCOPE.md` | Stage 0 output, the boundary of the project |
| `STATE.md` | Overwritten each session |
| `SESSION_LOG.md` | Append only |
| `NEXT_SESSION.md` | Generated at the end of each session |

## Reading the confidence fields

`confidence` is about the general concept. `confidence_mirra` is about whether
it applies to this tool. They routinely differ, and a strong general confidence
never carries a weak tool claim. `access` in `sources.csv` records what was actually
consumed: `read`, `snippet-only`, `paywalled`, `not-retrieved` or `unrecorded`.
Everything except `read` means nobody has opened the page, and a node cannot
carry `confidence_mirra=established` when every source behind its tool claims is
unread. Right now all 31 sources are unread, so read `RESEARCH_NOTES.md` before
trusting anything.
