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
| `session_03_thermo_chiller.md` | Thermo Neslab and ThermoFlex chillers | yes, see the note |
| `session_04_edwards_pumps.md` | Edwards nXDS, iXL and nEXT pumps | not yet |

Sessions 5 to 10 get their files as the sessions before them finish. The build
order is in `../CLAUDE.md`.

## A note on sessions 1 and 2

Neither driver was built from a manual, and for the same reason both times. This
machine cannot reach `lakeshore.com`, `mks.com`, `idealvac.com`, `lesker.com`,
or any university or national lab mirror of them. The egress proxy answers 403.
`github.com` and the package registries are reachable and nothing else is.

Test that early in a session. Knowing within five minutes which kind of session
you are in is worth a lot, because it changes what the whole session is for.

Three routes did work and are worth trying before giving up.

**Look on GitHub for the manual itself.** This is the one session 3 found and it
is the strongest by a long way. Lab groups keep the manuals for the instruments
they automate in the same repository as the code that drives them. Session 3
found two Thermo NESLAB manuals as ordinary PDFs in the `manuals/` folder of
`github.com/octopode/bathtime`, cloned them, extracted the text and read the
protocol appendices in full. That turned a session that was going to be another
guessing exercise into one written from the manufacturer's own document. Search
GitHub for the device name before assuming a manual cannot be had.

**The web search tool can read PDFs this machine cannot download**, and answers
narrow questions with specific statements from them. Second hand, and weaker
than a manual.

**Open source control system code on GitHub is a real cross-check.**
`epics-modules/vac` supplied the Series 350 command set in session 2, and a lab
ThermoFlex library supplied everything ThermoFlex specific in session 3. Weaker
than a manual and it carries no worked examples. Say so where you use it.

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

## A note on session 3

The Thermo chiller driver was built, and **it was the first one built with the
manufacturer's manual open**. Two Thermo NESLAB manuals were read in full, from
PDFs found in the `manuals/` folder of a public laboratory repository on GitHub
after every Thermo Fisher, distributor and university site was refused as usual.

So most of that driver is quoted rather than guessed. Nineteen complete frames
printed in those manuals are parametrised checksum tests, and eighteen of them
agree with the code byte for byte. The nineteenth is a misprint in the manual.

**The ThermoFlex half is the weak half.** The manuals cover the NESLAB RTE line.
Nothing found covers the ThermoFlex serial appendix, so its flow and pressure
command bytes and its whole fault bit table come from one open source library
and no manual. The Thermo chiller section of `../REVIEW.md` says which items
those are and how to check each one at the bench, which matters more here than
anywhere else in the project because somebody can actually put a cable on this
device.

Session 3 also made two changes to shared code that every later driver inherits.
`SerialTransport` can now read a reply by a length written inside it, which is
what binary protocols need and what the terminator could never do. And the trend
generator can draw two lines on one pair of axes, for a reading and the setpoint
it is holding.

`../manuals/FETCH_PROMPT_THERMO_CHILLER.md` asks for the one document still
missing. It is much shorter than the other two fetch prompts, because most of
this protocol is already sourced.
