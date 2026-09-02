# Manuals

Where the manufacturers' documents live, and how they get here.

## The standing rule

**A session does not fetch documents. The project owner supplies them.**

This is the owner's decision and it holds at every stage of every project in
this repository. It is not a workaround for one blocked session. A session that
needs a document it does not have writes a fetch prompt, hands it over, and
stops.

Two reasons it is worth being firm about.

The practical one. The machines these sessions run on cannot reach the
manufacturers' websites. The network policy allows source and package hosts and
refuses the rest. Time spent discovering that again is time wasted, and every
session would rediscover it.

The real one. When fetching a document is hard, the tempting substitutes are all
close to hand: a search snippet, a summary site, a forum answer, a vendor's own
source code on GitHub, or plain memory of a protocol that looks like this one.
Every one of those produces code that looks finished and was never checked. The
rule removes the temptation by removing the choice.

## What a session does when a document is missing

1. Look here first. It may already have arrived.
2. Stop the work that depends on it. Carry on with anything that does not.
3. Write a fetch prompt, using the shape below, and hand over the file itself.
4. Record what is blocked in `../REVIEW.md`, and mark the row in
   `../sessions/README.md`.
5. Stop. The owner runs the prompt and unpacks the answer here.

Searching for candidate links is allowed, and worth doing. A fetch prompt that
carries exact URLs saves the owner a hunt. Reading what a search result says
about a protocol is not allowed. A snippet is not a worked example.

## The shape of a fetch prompt

`FETCH_PROMPT.md` is the current outstanding request, and it is the worked
example of this shape. A new one covers:

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
  FETCH_PROMPT.md      the current outstanding request
  MANIFEST.md          arrives with the zip
  hashes.txt           arrives with the zip
  lakeshore/
  granville_phillips/
  ...
```
