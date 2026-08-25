# Reading queue

Documents worth reading that are not yet read. Three tiers.

**These tier definitions are a proposal, not settled.** `KICKOFF.md` says to use
"the three tiers described in `CLAUDE.md`", but `CLAUDE.md` describes no tiers.
The gap is logged in `CHANGES.md`, item 2. What follows is the working
definition until you replace it.

| Tier | Meaning | Consequence |
|---|---|---|
| 1 | Needed before a specific named class can be written properly. | The class waits. Name the class in the entry. |
| 2 | Needed for depth or for a literature review. Not tied to one class. | Read during the staged literature reviews. |
| 3 | Parked. Looked promising, not clearly needed yet. | Revisit at the next quarterly maintenance pass. |

Rules for an entry. Give the title, a URL, where you found it, and one line on
why it is worth the time. An item moves between tiers as your view of it
changes, and that is expected. An item leaves the queue only when it is read
and logged in `verified.log`, or when it is dropped with a reason.

## Tier 1, blocking a named class

Empty.

## Tier 2, depth and literature reviews

Empty.

## Tier 3, parked

Empty.

---

## Why this file is empty

`KICKOFF.md` asks for the queue to be seeded from the bibliographies of the
sources fetched in phase 2, and expects it to be substantial. It says the depth
of the course comes from what the CAS lecture notes and the Jain decks cite.

That is right, and it is exactly why nothing is listed here yet. Nothing was
fetched. Session zero ran with network egress denied, so no bibliography has
been read. See the header of `verified.log` for the evidence.

Seeding this file from recollection would produce the specific failure
`CLAUDE.md` source rule 1 exists to prevent: citing a paper seen only in
another paper's bibliography, or worse, never seen at all. A queue of
plausible-looking references that nobody has opened is worse than an empty one,
because it looks like work has been done.

To fill it, on a session with network access:

1. `python3 magnet-course/library/fetch_sources.py`
2. Read the bibliographies of `cas`, `hall`, `coils`, `bahrdt`, `sgobba`, and
   the Jain decks (`jainov`, `jainus`, `jainharm`, `jainaxis`).
3. Add what they cite here, with the tier and the reason.
