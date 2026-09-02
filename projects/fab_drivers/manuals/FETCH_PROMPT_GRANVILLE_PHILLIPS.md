# Prompt: collect the Granville-Phillips gauge manuals into one zip

Feed this file to a session that has unrestricted internet access. It starts
from nothing, so everything it needs is here.

This is the standing way documents arrive in this repository. Sessions doing the
work never fetch their own sources when the network refuses them. They write a
request like this one and hand it over. `README.md` next to this file has the
rule and the reason.

## What this is for

A project builds read-only monitoring drivers for semiconductor fab equipment.
Its first rule is that no driver is written from memory of a protocol. Every
command has to be checked against the manufacturer's own manual.

A driver for the Granville-Phillips gauges has been written and it is short of
sources. The machine that wrote it could reach `github.com` and nothing else.
Every site hosting one of these manuals answered 403 at the egress proxy:
`mks.com`, `idealvac.com`, `lesker.com`, `manualslib.com`, and the mirrors at
`bl831.als.lbl.gov`, `mmrc.caltech.edu`, `nanophys.kth.se` and
`kmtnet.kasi.re.kr`.

The driver works and its tests pass. It rests on one worked example relayed
through a search tool and on an EPICS device support module read from GitHub.
The questions at the end of this file are the ones that decide whether it is
correct. Answering them is the point of the job.

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

- Prefer a PDF straight from the manufacturer's own website. These products are
  now MKS Instruments, previously Granville-Phillips, previously Helix
  Technology and Brooks Automation. Any of those names on the cover is fine.
- A copy of the same PDF hosted by a university, a national lab, or a
  distributor such as Kurt J. Lesker or Ideal Vacuum, is fine. Many are mirrored
  by physics groups. Check it is the real thing, not a scanned excerpt or a
  datasheet.
- A third party rewrite, a "manual summary" site, or anything that reads like it
  was generated rather than published, is not acceptable. Leave it out.
- If a document cannot be found, say so plainly in the manifest. A missing
  document is a fine answer. A plausible substitute is not.

## Priority 1, needed now

These four block the driver that exists.

| Device | Document wanted | Part number, if it helps |
|---|---|---|
| Series 375 Convectron gauge controller | Instruction Manual, the full one with the RS-232 and RS-485 chapter | 000495-114, or revisions 109 or 111 |
| Series 275 Mini-Convectron module with RS-485 | Instruction Manual | 275545, Revision C, November 2016 |
| Series 356 Micro-Ion Plus module | Instruction Manual | 356007 |
| Series 350 ion gauge controller | Instruction Manual | 350010 |

**The 375 manual is the most valuable single document in this list.** See
question 1.

## Priority 2, useful now, and needed soon

These describe the same protocol on neighbouring models and would settle several
questions by cross-reading.

| Device | Document wanted |
|---|---|
| Series 354 Micro-Ion module with RS-485 | Instruction Manual, 354008 |
| Series 340, 358 and 360 | "Process Control and RS-232 or RS-485 Interface", 011979 |
| Series 358 Micro-Ion controller | Instruction Manual |
| Series 307 gauge controller | Instruction Manual |
| Series 343 Mini-Ion module with RS-485 | Instruction Manual, 343048 or 343050 |

## Leads, which are leads and not facts

Every URL below was found by searching and none of them could be opened from
this machine. Treat them as starting points. Several may be dead or may point at
a datasheet rather than a manual.

- `https://www.lesker.com/newweb/gauges/pdf/375usermanual.pdf`
- `https://www.lesker.com/newweb/gauges/pdf/manuals/kjlc_375_series_manual_rev109.pdf`
- `https://www.lesker.com/newweb/gauges/pdf/manuals/375usermanualleskerrev111.pdf`
- `https://www.idealvac.com/files/ManualsII/GP_375InstructionManual_April08.pdf`
- `https://bl831.als.lbl.gov/~gmeigs/PDF/Granville_Philips_375_convectron.pdf`
- `https://users.obs.carnegiescience.edu/crane/pfs/man/Electronics/Granville-Phillips-Series375.pdf`
- `https://www.mks.com/mam/celum/celum_assets/resources/GP-275RS485DualRelays-275545-MAN.pdf`
- `https://www.idealvac.com/files/manuals/275_Tube_%20Instruction_Manual_with_RS485_EU.pdf`
- `https://www.lesker.com/newweb/gauges/pdf/manuals/kjlc_275_series_manual_v103.pdf`
- `https://www.ccrprocessproducts.com/wp-content/uploads/2015/08/GP-350Controller350010-MAN.pdf`
- `https://bl831.als.lbl.gov/~gmeigs/PDF/Granville_Phillips_350_IG_Controller.pdf`
- `https://www.idealvac.com/files/manuals/GP_350_InstructionManual_1.pdf`
- `https://kmtnet.kasi.re.kr/tmp/Manual_report/M10/CCD_Dewar_VacuumGauge_manual_MKS.pdf` (Series 356)
- `https://api.p1.mks.com/mam/celum/celum_assets/resources/GP-354wRS485Digital-354008-MAN.pdf`
- `https://mmrc.caltech.edu/Vacuum/Hornet_Ion_Gage/Micro-ion%20gage%20(Hornet).pdf` (Series 354)
- `https://www.mks.com/mam/celum/celum_assets/resources/GP-340-358-360GaugeInterface011979-MAN.pdf`
- `https://www.idealvac.com/files/manualsII/Granville_Phillips_358_Manual.pdf`
- `https://www.nanofab.utah.edu/wp-content/uploads/2022/11/granville-phillips-358-micro-ion-controller.pdf`

## The questions these documents have to answer

Answer each one with a page number and the manual it came from, or with a plain
"not in this manual". A "not in this manual" is a real answer and is worth as
much as a page number. Do not infer, do not fill a gap from another model, and
do not answer from your own knowledge of these instruments. If two manuals
disagree, say so and give both.

1. **On a Series 375, how do you ask for a particular gauge channel?** It is a
   multi-channel controller and the driver currently sends a bare `#01RD` and
   reads whatever answers, without knowing which channel that is. Give the exact
   command for each channel, with a worked example if the manual has one. **This
   is the most important question in the list.**

2. **Is there a command that reports which pressure units the instrument is
   configured for?** Torr, mbar or pascal. Set-unit commands are known to exist.
   A read-units query was searched for and not found, and its absence is
   currently recorded as a finding. If one exists, give the command and the
   exact reply, including what the reply looks like for each of the three units.

3. **Is there an identity command?** Anything that asks the instrument what
   model, serial number or firmware it is. The driver cannot currently check
   that its model setting matches the instrument in front of it.

4. **The exact reply format for a read.** The one worked example available here
   is `#01RD<CR>` returning `*01 9.34E-06<CR>`. Confirm it, character for
   character, per model. In particular: is the address always echoed, is the
   separator always one space, is there ever a line feed after the carriage
   return, and is the number always in that exponent form.

5. **Whether the address may be left out.** An EPICS driver sends a bare `#`
   with no address digits to a Series 350 over RS-232 and gets back a reply with
   no address in it. This driver always sends two address characters. Say what
   each manual requires on RS-232 and on RS-485.

6. **The address range, per model, and whether a broadcast address exists.**
   The address switch is understood to run 0 to 15, that is `00` to `0F` hex,
   with an `SA` offset command on top. Confirm per model. If any broadcast or
   "all modules" address exists, say what it is and what the manual says
   happens when several modules answer at once.

7. **The serial settings, per model.** Baud rate, data bits, parity, stop bits,
   and what the instrument ships set to. The 375 and 350 are believed to be 9600
   8-N-1. The 275 and 356 are guesses copied from those two. Also say what other
   baud rates each model offers and how they are selected.

8. **What a gauge reports when it is switched off, unplugged, faulted, or
   degassing.** `9.99E+09` is documented as the value for the first three to
   five seconds after power up. Is it also what a gauge that is off reports? Or
   does the instrument return an error, or stay silent? The driver and its mock
   both assume `9.99E+09`, so this decides whether the tests are testing the
   right thing.

9. **The full list of read-only commands,** per model, with the reply format of
   each. Anything that reads a value, a state or a configuration without
   changing it.

10. **The full list of commands that change something,** per model, with what
    each one changes. These go on the banned list. The driver currently bans
    `F1 0`, `F1 1`, `F2 0`, `F2 1`, `DG0 OFF`, `DG1 ON`, `SE0`, `SE1`, `SA`,
    `SW`, `SZ`, `SS`, `SUT`, `SUM` and `SUP`. Four of those mnemonics were
    assumed from prose descriptions and were never seen written out: `SZ`, `SS`,
    `SE0` and the `SU` stem. Confirm or correct each, and add anything missing.

11. **The error replies.** `?01 SYNTX_ER<CR>` is the one known. List the others
    and what causes each.

12. **The required timing.** Any minimum gap between one message and the next,
    any maximum time the instrument may take to answer, and on RS-485 any
    turnaround delay needed between one module releasing the line and the host
    driving it.

13. **Anything the manual warns about that is not a command.** Two in
    particular: whether an ion gauge can be damaged by a command sequence, and
    whether reading over the interface interferes with anything the instrument
    is doing for the tool it is wired into.

## Acceptance checks, before you hand anything back

- Every file opens as a real PDF.
- Text is searchable, or the file is marked in the manifest as a scan.
- It is the full manual, not a datasheet, a brochure or a quick start guide. A
  manual with a computer interface chapter runs to dozens of pages. A four page
  document is a datasheet.
- Nothing is truncated. Check the last page is the last page.

## What to hand back

One zip containing:

```
granville_phillips/
  <one file per document, named <series>_<part number>_<title>.pdf>
MANIFEST.md
hashes.txt
ANSWERS.md
```

- **`MANIFEST.md`**: one row per document, with the model, the title, the part
  number and revision, where it was downloaded from, the date, and its SHA-256.
- **`hashes.txt`**: the SHA-256 of every file, so it can be checked later.
- **`ANSWERS.md`**: the thirteen questions above, each answered with a page
  number and the manual it came from, or "not in this manual".
- **What was not found, and where you looked.** As useful as the documents
  themselves. It stops the next person repeating the search.
