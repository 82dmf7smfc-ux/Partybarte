# Browser tool debug codes

The browser tool (`alarm_pareto.html`) records short codes while it reads a file.
They are hidden until you press "Show debug log", and "Copy debug report" copies
them so they can be shared for troubleshooting. Nothing there leaves your machine.

Each code groups every event of that kind, with a count and up to five example
lines. This page is the reference for what each code means. The codes live in the
`DEBUG_CODES` registry near the top of the tool's script, and the browser test
harness checks that every code the tool emits is listed there, so this list and
the tool stay in step.

Levels: `info` is normal, `warn` means something was skipped or guessed, `error`
means a file produced nothing.

| Code | Level | Meaning | What to do |
|---|---|---|---|
| `FMT-P5000` | info | A file was read as a P5000 Etch elog. | Nothing. Confirms the format. |
| `FMT-DELIM` | info | A file was read as a delimited (CSV style) file. | Nothing. Confirms the format. |
| `FMT-OVERRIDE` | info | The format was forced by the Format drop-down. | Nothing. You picked the format by hand. |
| `FMT-MIXED` | warn | The batch mixed formats. Columns were matched by position. | Prefer loading one format at a time for the cleanest result. |
| `PRE-META` | info | Tool details (system, process, software) were read from the P5000 preamble. | Nothing. |
| `HDR-NOTFOUND` | warn | The P5000 header row was not found, so every date line was read. | Check the file has a `Date Time Event Number Event Type Description` header. |
| `ROW-NOMATCH` | warn | A line did not match the P5000 row pattern and was skipped. | Look at the sample lines. If real data was dropped, share the report. |
| `ROW-CONT` | info | A line with no leading date was joined to the record above it. | Usually a wrapped line. Check the samples if a count looks high. |
| `TS-Y2K` | info | Rows used a 2-digit year, expanded with the 1969 pivot (00-68 to 2000s, 69-99 to 1900s). | Nothing, unless a year landed in the wrong century. |
| `TS-BADDATE` | warn | A timestamp could not be read, so the row was skipped in the analysis. | Check the Date and Time columns are mapped and formatted as expected. |
| `EQ-NOCHAMBER` | info | No chamber tag was found in a description. | Fine for lines with no chamber. Share samples if a real chamber was missed. |
| `FMT-EMPTY` | error | A file was detected but produced no data rows. | Check the start row, the header, and the format. |
| `CAT-UNMATCHED` | info | A message matched no category rule and was grouped by its normalized shape. | Look at the samples. Add a rule under "Message categories" to name that group. |
| `CAT-BADRULE` | warn | A category rule had an invalid pattern and was skipped. | Fix the regular expression on the named line. |

## Reporting a file that read wrong

1. Load the file in the tool.
2. Press "Show debug log", then "Copy debug report".
3. Paste the report. The codes and sample lines say exactly which lines the tool
   could not read, which is enough to extend the parser or the rules.
