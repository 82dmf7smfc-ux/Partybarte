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
| `session_01_lakeshore.md` | Lakeshore 218 / 224 / 336 temperature monitors | not yet |

Sessions 2 to 10 get their files as the sessions before them finish. The build
order is in `../CLAUDE.md`.
