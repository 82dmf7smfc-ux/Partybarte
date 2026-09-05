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
| `SCOPE.md` | Stage 0 output, the boundary of the project |
| `STATE.md` | Overwritten each session |
| `SESSION_LOG.md` | Append only |
| `NEXT_SESSION.md` | Generated at the end of each session |

## Reading the confidence fields

`confidence` is about the general concept. `confidence_mirra` is about whether
it applies to this tool. They routinely differ, and a strong general confidence
never carries a weak tool claim. `access=snippet-only` in `sources.csv` means
the source was reached through a search summary and has not been read.
