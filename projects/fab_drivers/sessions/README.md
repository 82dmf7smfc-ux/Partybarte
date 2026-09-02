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
| `session_02_granville_phillips.md` | Granville-Phillips 275/375 and 350/356 gauges | yes, see the note |
| `session_03_thermo_chiller.md` | Thermo Neslab and ThermoFlex chillers | not yet |

Sessions 4 to 10 get their files as the sessions before them finish. The build
order is in `../CLAUDE.md`.

## A note on sessions 1 and 2

Neither driver was built from a manual, and for the same reason both times. This
machine cannot reach `lakeshore.com`, `mks.com`, `idealvac.com`, `lesker.com`,
or any university or national lab mirror of them. The egress proxy answers 403.
`github.com` and the package registries are reachable and nothing else is.

Test that early in a session. Knowing within five minutes which kind of session
you are in is worth a lot, because it changes what the whole session is for.

Two routes did work in session 2 and are worth trying before giving up. The web
search tool can read PDFs this machine cannot download, and answers narrow
questions with specific statements from them. And open source control system
code on GitHub is a real cross-check: `epics-modules/vac` supplied the Series
350 command set. Both are weaker than a manual. Say so where you use them.

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

## A note on session 2

The Granville-Phillips driver was built, and it was built without a
Granville-Phillips manual. It rests on one worked exchange relayed through the
web search tool and on the EPICS `epics-modules/vac` device support read
directly from GitHub.

The Granville-Phillips section of `../REVIEW.md` lists what is backed by a
worked example, what is assumed, and what to check first on a bench. Two items
there are worth knowing before the driver goes near a tool. Nothing found says
how to select a channel on a Series 375, so the driver reads whatever a bare
`RD` returns and says out loud that it does not know which gauge that is. And no
read-units query was found on any model, so the pressure unit in a trend file is
whatever the person who set the driver up believed.

`../manuals/FETCH_PROMPT_GRANVILLE_PHILLIPS.md` carries thirteen numbered
questions the manuals need to answer. Running it settles both of those.
