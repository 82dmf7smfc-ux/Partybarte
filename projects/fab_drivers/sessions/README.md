# Session prompts

One file per driver session, in build order. Each file is the complete starting
prompt for that session and nothing else, so it can be handed straight to a new
session with nothing to trim.

A session starts with no memory of the one before it, so the last act of every
session is to write the next file here and hand it over. These live in the
repository rather than in a chat window because a prompt that exists only in a
chat log is one closed tab away from being lost.

The next session to run is the highest numbered file that has no matching driver
under `../fab_drivers/devices/` yet.

| File | Device | Built |
|---|---|---|
| `session_01_lakeshore.md` | Lakeshore 218 / 224 / 336 temperature monitors | yes, see the note |
| `session_02_granville_phillips.md` | Granville-Phillips 275/375 and 350/356 gauges | not yet |

Sessions 3 to 10 get their files as the sessions before them finish. The build
order is in `../CLAUDE.md`.

## A note on session 1

The Lakeshore driver was built, and it was built without a Lake Shore manual.
This machine cannot reach `lakeshore.com` or any mirror, so it was written from
a research file the project owner supplied instead.

That is weaker than reading the manual, and the Lakeshore section of
`../REVIEW.md` lists item by item what is backed by a worked example, what is
assumed, and what to check first on a bench. Read it before the driver goes near
a tool.

`../manuals/FETCH_PROMPT.md` still stands. Running it would let somebody check
the driver against the real documents, which is the right next step for it.
