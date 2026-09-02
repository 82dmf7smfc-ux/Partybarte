# Prompt: collect the equipment manuals into one zip

Feed this file to a session that has unrestricted internet access. It starts
from nothing, so everything it needs is here.

## What this is for

A separate project builds read-only monitoring drivers for fab equipment. Its
first rule is that no driver is written from memory of a protocol. Every command
has to be checked against the manufacturer's own manual first. The session that
writes the drivers has no route to the manufacturers' websites, so it cannot
fetch its own sources. That is the whole reason this job exists.

Your job is to collect the documents and hand back one zip. You are not writing
any code and you are not summarising anything.

## The one rule that matters

**Hand back the original documents. Do not retype them, do not summarise them,
and do not rewrite them.**

A summary of a manual is worthless here. The point of the document is that
somebody can look up a command and see the manufacturer's own worked example
next to it. A paraphrase loses exactly the detail the driver depends on, and it
looks just as confident when it is wrong.

So:

- Prefer a PDF straight from the manufacturer's own website.
- A copy of the same PDF hosted by a university or a national lab is fine. Many
  of these are mirrored by physics groups. Check it is the real thing, not a
  scanned excerpt.
- A third party rewrite, a "manual summary" site, or anything that reads like it
  was generated rather than published, is not acceptable. Leave it out.
- If a document cannot be found, say so plainly in the manifest. A missing
  document is a fine answer. A plausible substitute is not.

## Priority 1, needed now

The Lake Shore temperature monitors. Work on these first and do not let the rest
of the list hold them up.

| Device | Document wanted |
|---|---|
| Lake Shore Model 218 / 218S | User's Manual, the full one with the computer interface chapter |
| Lake Shore Model 224 | User's Manual |
| Lake Shore Model 336 | User's Manual |

Starting points found by an earlier search. Treat them as leads, not as facts.
Some may have moved.

- Model 336: `https://www.lakeshore.com/docs/default-source/product-downloads/336_manual0ebc9b06cbbb456491c65cf1337983e4.pdf?sfvrsn=2e8633a3_1`
- Model 218: `https://www.lakeshore.com/docs/default-source/product-downloads/manuals/218_manual.pdf?sfvrsn=6a03068_3`
- Model 218 mirror: `https://www.jlab.org/div_dept/physics_division/dsg/technical_documentation/HDice/Manuals_and_Specifications/LakeShore%20Model%20218%20Temperature%20Monitor.pdf`
- Model 218 mirror: `https://irtfweb.ifa.hawaii.edu/~iqup/domeenv/PDF/218_monitor.pdf`
- Model 224: not yet located. Start at the Lake Shore product download pages.

If a link is dead, search for the model number plus "user's manual" and prefer
`lakeshore.com`, then a `.edu` or `.gov` mirror.

### What these three manuals have to answer

This is the checklist the driver depends on. For each of the three manuals,
record in the manifest whether the document answers each question, and on which
page. If a manual does not answer one of these, say so. Do not answer it
yourself from another source.

1. The RS-232 settings. Which baud rates the instrument offers, the number of
   data bits, the parity, the stop bits, and whether it uses flow control or
   handshaking.
2. The character or characters that end a command sent to the instrument, and
   the ones that end a reply coming back. Whether that terminator can be changed
   by the user, and what it is set to from the factory.
3. The exact syntax and a worked example of each of these queries:
   `KRDG?`, `CRDG?`, `SRDG?`, `RDGST?`, `*IDN?`, `INNAME?`.
   The worked example matters more than the syntax line. It is the thing that
   settles what the reply actually looks like, spaces, signs, exponent and all.
4. The `RDGST?` reading status table. The weight of each bit and what each bit
   means.
5. What the instrument sends back for a sensor that is not connected, for one
   that is over range, and for one that is under range.
6. How the instrument reports that it did not understand a command. Whether
   there is a status or error register behind that, and how to read it.
7. Which input names the instrument uses. The three models differ, and this is
   one of the things the driver has to get right per model.
8. Whether a query for every input at once exists, for example `KRDG? 0`, and
   what its reply looks like.
9. For the Model 336 only. Its Ethernet interface. The TCP port, whether the
   command set is exactly the same as over serial, and whether anything has to
   happen before commands are accepted.
10. Any timing the manual states. How long the instrument may take to answer,
    and any minimum gap the host must leave between commands.

## Priority 2, wanted soon

Nine more drivers follow the Lake Shore one, one per session, and every one of
them will hit the same wall. Collecting them now saves nine round trips. Get
what you can. Do not spend long on any single one, and do not let a hard one
stop you handing back the rest.

| Device | Document wanted |
|---|---|
| Granville-Phillips 275 and 375 Convectron | Instruction manual, with the RS-232 command set |
| Granville-Phillips 350 and 356 Micro-Ion | Instruction manual, with the RS-232 command set |
| Thermo Neslab and ThermoFlex recirculating chillers | Manual covering the RS-232 communications protocol, the framed and checksummed one |
| Edwards nXDS scroll pumps | Instruction manual, with the serial command set |
| Edwards iXL dry pumps | Instruction manual, with the serial command set |
| Edwards nEXT turbomolecular pumps | Instruction manual, with the serial command set |
| MKS 937B and 946 vacuum gauge controllers | Operation manual, with the RS-232/485 command set |
| Pfeiffer TC110 and TC400 pump controllers | Operating instructions, plus anything describing the Pfeiffer Vacuum Protocol telegram format and the parameter list |
| Watlow EZ-Zone PM and RM controllers | The Modbus RTU register map, and the communications user guide |
| Advanced Energy MDX and Pinnacle supplies | Manual describing the AE Bus serial protocol, framing and checksum |
| SRS RGA100, RGA200, RGA300 | Operating manual and programming reference |

`idealvac.com` hosts a lot of vacuum equipment manuals free and without a login.
It is worth trying for the Granville-Phillips, MKS, Edwards and Pfeiffer items.

SEMI standards E5, E30 and E37 are wanted eventually for a later session. They
are sold, not free. Do not buy anything. Just note in the manifest that they
were not obtained and why.

## Checks to run before you accept a file

For every file you keep:

1. It really is a PDF. The first bytes of the file are `%PDF`. A page of HTML
   saved with a `.pdf` name is a common failure and it is easy to miss.
2. The text inside it can be searched. Try searching the Lake Shore ones for
   `KRDG`. If a search finds nothing, the document is a scan of paper rather
   than real text. Keep it anyway, it is still the manual, but mark it in the
   manifest as a scan so the reader knows they cannot grep it.
3. It is the full manual and not a datasheet. A datasheet is four glossy pages
   and has no command list. The manual has a chapter on the computer interface
   and runs to a hundred pages or more. If only a datasheet can be found, keep
   it, and say in the manifest that it is a datasheet.
4. It is not truncated. Open the last page.

## What to hand back

One zip, named `fab_manuals_<yyyy-mm-dd>.zip`, laid out like this:

```
fab_manuals_2026-09-02/
  MANIFEST.md
  hashes.txt
  lakeshore/
    lakeshore_218_users_manual.pdf
    lakeshore_224_users_manual.pdf
    lakeshore_336_users_manual.pdf
  granville_phillips/
  thermo_neslab/
  edwards/
  mks/
  pfeiffer/
  watlow/
  advanced_energy/
  srs_rga/
```

Name files after the device and the document, in lower case, with underscores.
Leave out a folder entirely if nothing was found for it, and say so in the
manifest.

`hashes.txt` is one line per file, the SHA-256 followed by the file name. The
driver documents record the hash of the manual they were written from, so that
a later reader can tell whether they are holding the same document.

`MANIFEST.md` has one section per document, with these lines:

- Device
- Title, copied exactly from the title page
- Part number, copied exactly. Lake Shore prints one on the title page
- Revision and date
- Publisher
- Source URL, the exact one the file came from
- Date fetched
- File name and size
- SHA-256
- Searchable text, yes or no
- Full manual or datasheet

Then, for the three Lake Shore documents only, the ten questions above, each
with a yes and a page number, or a no.

Finish the manifest with a short list of anything on the list that was not
found, and where you looked. That list is as useful as the documents. It tells
the next person not to repeat the search.
