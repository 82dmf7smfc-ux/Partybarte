# Manuals

Where the manufacturers' manuals live while a driver is being written.

## Why this folder exists

The first rule of this project is that no driver is written from memory of a
protocol. The command syntax has to be checked against the manufacturer's own
manual, against a worked example, before any code sends anything.

A session doing that work usually cannot reach the manufacturers' websites. The
network policy on the machines these sessions run on allows source and package
hosts and very little else. So the documents have to be fetched separately and
put here by hand.

`FETCH_PROMPT.md` is the prompt for doing that. Hand it to a session that does
have internet access. It says which documents are wanted, what each one has to
answer, how to tell a real manual from a datasheet or a rewrite, and what to
hand back. The answer comes back as one zip. Unpack it here.

## What goes in git and what does not

The PDFs do not. They are the manufacturers' copyrighted documents and some of
them are large. `.gitignore` keeps them out.

What goes in git is this file, the fetch prompt, and the manifest that arrives
with a zip. The manifest is worth keeping because it records where each document
came from, its part number, and its SHA-256.

Each driver's `PROTOCOL.md` names the manual it was written from, with the part
number and the hash. That is how a later reader can tell whether the document in
their hands is the one the driver was built against.

## Layout

One folder per manufacturer, named the way `FETCH_PROMPT.md` describes.

```
manuals/
  README.md
  FETCH_PROMPT.md
  MANIFEST.md          arrives with the zip
  lakeshore/
  granville_phillips/
  ...
```
