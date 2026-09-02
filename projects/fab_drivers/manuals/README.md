# Manuals

Where the manufacturers' documents live, and how they get here.

## How documents are got

Research the web directly. Search for the manual, download it, read it. The
owner may also hand over a PDF or a compiled research file, and those land here
too.

If the network refuses a download, which is what happens on these machines for
most manufacturer sites, say so plainly and write a fetch prompt.
`FETCH_PROMPT.md` is the worked example of one. It goes to somebody with better
access and comes back as a zip that gets unpacked here. Three are outstanding,
one for Lake Shore, one for Granville-Phillips and one for the ThermoFlex
chillers.

**Look on GitHub before writing a fetch prompt.** The Thermo chiller session
found two Thermo NESLAB manuals as ordinary PDF files in the `manuals/` folder
of a public laboratory repository, `github.com/octopode/bathtime`, and read them
in full. `github.com` is reachable on these machines when nothing else is. Lab
groups keep the manuals for the instruments they automate next to the code that
drives them, so a repository that has a driver for a device may well have the
device's manual too. That is worth thirty seconds of looking before deciding a
document cannot be had.

## The part that does not bend

Say what each fact was taken from.

`PROTOCOL.md` names its sources and ranks them. A manual read directly is the
strongest. A research file compiled by someone else, a search result, a forum
thread, or a vendor's own driver source is weaker. Anything resting on a weaker
source, or on nothing, goes in `../REVIEW.md` as unverified, item by item.

That is the whole safeguard, and it is worth understanding why it is the one
that stayed. A driver built on a weak source is often the only thing available
in the time there is, and it is genuinely useful. A driver built on a weak
source that reads as though it came from the manual is not, because nobody goes
back to check it.

`../fab_drivers/devices/lakeshore/PROTOCOL.md` is the worked example. It opens
by saying no Lake Shore manual was read, names what was read instead, and ranks
it. `../REVIEW.md` then lists the nine specific things a bench visit should
check first.

## The shape of a fetch prompt

There are three outstanding requests. `FETCH_PROMPT.md` asks for the Lake Shore
temperature monitor manuals and the later devices in the plan.
`FETCH_PROMPT_GRANVILLE_PHILLIPS.md` asks for the Granville-Phillips gauge
manuals and carries thirteen numbered questions the driver needs answered.
`FETCH_PROMPT_THERMO_CHILLER.md` asks for one document, the ThermoFlex serial
appendix, and is much shorter than the other two because that session had
manuals for most of what it built. It is the example to copy when most of a
protocol is already sourced and a specific hole is left.
`FETCH_PROMPT.md` is the worked example of this shape. A new one covers:

- **What it is for.** The prompt goes to a session starting from nothing, so it
  says why the documents are wanted and what they feed.
- **The one rule.** Hand back the original documents. Do not retype, summarise
  or rewrite them. A paraphrase loses exactly the detail the code depends on,
  and it looks just as confident when it is wrong.
- **What counts as a source.** The manufacturer's own site first, then a
  university or national lab mirror. Never a rewrite, a summary site, or
  anything that reads as generated rather than published.
- **The documents wanted,** split into what blocks work now and what will block
  it soon. Collecting the later ones early saves a round trip per session.
- **Leads.** Every candidate URL already found, marked as leads rather than
  facts.
- **The questions each document has to answer,** numbered, to be answered with a
  page number or a plain no. This is the part that makes a document useful
  rather than merely present, and it is the part only the session that needs it
  can write.
- **Acceptance checks.** A real PDF, searchable text or marked as a scan, the
  full manual rather than a datasheet, not truncated.
- **What to hand back.** One zip, a folder per manufacturer, a `MANIFEST.md` and
  a `hashes.txt`.
- **What was not found, and where they looked.** As useful as the documents. It
  stops the next person repeating the search.

## What goes in git and what does not

The PDFs do not. They are the manufacturers' copyrighted documents and some of
them are large. `.gitignore` keeps them out.

What goes in git is this file, the fetch prompts, and the `MANIFEST.md` that
arrives with a zip. The manifest is worth keeping because it records where each
document came from, its part number, and its SHA-256.

Each driver's `PROTOCOL.md` names the manual it was written from, with the part
number and the hash. That is how a later reader can tell whether the document in
their hands is the one the driver was built against. It is also how a reviewer
can tell that a manual was really read, rather than assumed.

## Layout

One folder per manufacturer, named the way `FETCH_PROMPT.md` describes.

```
manuals/
  README.md
  FETCH_PROMPT.md      outstanding request, Lake Shore and the later devices
  FETCH_PROMPT_GRANVILLE_PHILLIPS.md   outstanding request, the gauges
  MANIFEST.md          arrives with the zip
  hashes.txt           arrives with the zip
  lakeshore/
  granville_phillips/
  ...
```
