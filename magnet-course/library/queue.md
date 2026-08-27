# Reading queue

Three tiers, per `CLAUDE.md`: read next, read eventually, noted only.

## How this queue was built, and what is wrong with it

`CLAUDE.md` says the queue is fed from the bibliographies of sources you have
read. **Nothing has been read.** All 40 URLs were attempted on 2026-08-27 and
all 40 failed, because this machine has no outbound network access. See
`library/verified.log`.

So this queue is seeded from the only two things available locally: the
syllabus, and the research checklist in
`syllabus/magnet-lifecycle-research.html`. That makes it a work plan, not a
literature trail. It is smaller and shallower than the queue described in
`KICKOFF.md`, which expected the CAS notes and the Jain decks to supply the
depth. They will, once they can be fetched. Until then this queue lists what to
fetch, not what was found by following citations.

Section 4 is the part that carries real information: topics the research
checklist names for which the syllabus supplies no source at all. Those are
genuine gaps, and they were found by reading the two local documents against
each other.

Ordering within tier 1 follows the build order in `BUILD_PROMPTS.md`: class 06
first, then unit 3, then unit 4.

---

## Tier 1: read next

Ten sources. These carry the exemplar class and the two units built after it.
Nothing else should be fetched before these are cached and noted.

| key | why it is first | blocks |
|---|---|---|
| `hall` | The class 06 primary. The syllabus says read it end to end and calls it the single most useful free document in the course. Class 06 is the exemplar, so the template stands or falls on this one. | c06, c09, c10, c11, c30 |
| `bahrdt` | Cited by nine classes, more than any other source. Spans materials, measurement, stability and handling, so it is load bearing across four units. | c01, c02, c03, c04, c05, c20, c24, c25, c27 |
| `jainov` | Cited by six classes and described as the best single map of the field. Cheapest way to find out what the other sources are for. | c01, c07, c08, c09, c16, c28 |
| `cas` | The full CERN-2010-004 volume. Contains `hall`, `coils`, `bahrdt` and `sgobba` as chapters, so one fetch may cover four keys. Also holds the mechanical error chapters unit 3 and class 29 need. Check its size against `library/README.md` before caching. | c09, c13, c29 |
| `tn1297pdf` | The core read for class 12, the uncertainty budget. Unit 3 decides whether the multi-year dataset means anything, and this is the document that defines how to say so. | c12, c34 |
| `coils` | Class 07 primary, written for exactly the coil fabrication and calibration task. Also feeds the Helmholtz work in class 08, which is the method the whole aging study rests on. | c07, c30 |
| `immw20` | Real production practice: positioning, scanner description, data handling, measured versus expected. Four classes, and the closest thing to a worked example of a running bench. | c13, c16, c23, c31 |
| `magpy` | The modeling spine. Class 06's `worked.py` needs it to supply the true field for the active area averaging calculation, so the exemplar cannot be finished without it. Also unavailable to install here, see `requirements.txt`. | c18, c21, c23 |
| `arnoldmeas` | The practitioner counterpart to the CAS notes, and the free stand-in for ASTM A977. Covers the demagnetization curve, the Helmholtz method, and elevated temperature measurement. | c03, c08, c25 |
| `npl` | A national laboratory comparison of methods compliant with IEC 60404-5. The free stand-in for the standard itself, and the one document that would show whether buying the IEC text is avoidable. | c08 |

## Tier 2: read eventually

Seventeen sources. Needed, but not before the material that cites them is being
written.

| key | when it becomes tier 1 |
|---|---|
| `sgobba` | Unit 1, classes 02 and 05. Promote when the foundations are written. |
| `pmg88` | Unit 1 and class 25. The stabilising and handling chapter is the practical one. |
| `mmpa` | Class 05. Carries the IEC TC 68 material free, so it matters to the standards question. |
| `arnoldunder` | Class 04, load lines and permeance coefficient in plain language. |
| `jainus` | Classes 14, 17, 34. A whole lecture set, so budget a session. |
| `jainharm` | Class 17, harmonic description of 2D fields. |
| `jainaxis` | Class 17, determination of magnetic axis. |
| `immw12` | Classes 14 and 33, long running measurement discipline. |
| `magcam` | Classes 01, 15, 18, 19. Vendor blog, so read for vocabulary and typical resolutions, not for claims. |
| `amamag` | Class 20, the open version of the paywalled IEEE paper. Verify it really is the same content. |
| `bcam` | Classes 15 and 20, a built-from-parts array camera. |
| `visc` | Unit 6, classes 24 to 26. The only source in the whole syllabus for magnetic viscosity, which is a single point of failure. See section 4. |
| `femmtut` | Class 22, to be done start to finish. |
| `femmman` | Class 22, appendix A.1 on permanent magnet modeling. |
| `femmfaq` | Class 22, the H direction convention. |
| `magpypaper` | Class 21 background, open access. |
| `nistunc` | Class 12, for the GUM itself and the Monte Carlo supplement. |

## Tier 3: noted only

Thirteen sources. Recorded so they are not rediscovered from scratch.

| key | note |
|---|---|
| `casprog` | Archive to mine, not a document to read. Cited by no class. |
| `uspas` | Same. Cited by no class. |
| `femmcas` | Compressed orientation to FEMM. Redundant if `femmtut` is done properly. |
| `feexer` | Theory under the FEA. Optional by the syllabus's own wording. |
| `magpygh` | Source repository. Useful for visualisation examples in class 19, not for reading. |
| `radia` | Only if Magpylib cannot handle the open boundary case in class 22. |
| `ema` | An index, not a source. Use it to find alternatives if Magpylib does not fit. |
| `tn1297` | Landing page for `tn1297pdf`. Fetch the PDF instead. |
| `nistbib` | Worked examples, only if the budget in class 12 gets stuck. |
| `a977` | Paid. Free route is `arnoldmeas` plus `pmg88`. Buy only if a customer cites it. |
| `a773` | Paid. Free route is `sgobba`. Cited by no class. Rarely needed. |
| `iec` | Paid. Free route is `mmpa` plus `npl`. |
| `magcamieee` | Paid. Free route is `amamag`, same authors. Skip unless `amamag` proves to differ. |

---

## Section 4: topics with no source, and searches to run

These came out of reading `magnet-lifecycle-research.html` against the syllabus.
Each is a subject the checklist treats as part of the programme for which the
syllabus supplies no reference. None of these is a citation. They are searches
to run on the first session with network access.

**Highest value, because a class depends on them:**

1. **A reference magnet datasheet.** `shared/reference-part.md` cannot be
   finished without one. Needed: a specific purchasable part, simple geometry,
   published temperature coefficients for both Br and HcJ, and a grade stable
   enough to hold as a control for years. This blocks every worked example in
   all 35 classes. Search vendor catalogues with published grade data rather
   than retailer listings.
2. **A second source on magnetic viscosity.** Class 26 asks you to estimate the
   size of the signal you are hunting, and the whole aging programme rests on
   that estimate. The syllabus offers exactly one source for it, `visc`. One
   paper is not enough to set a detection threshold against. `CLAUDE.md` rule 7
   says show both numbers when sources disagree, which is impossible with one
   source. Search for long term open circuit measurements of NdFeB and SmCo with
   stated measurement precision.
3. **Hall probe calibration practice beyond Sanfilippo.** Class 11 writes a
   calibration plan for a home bench. `hall` and `tn1297` frame it, but neither
   covers what a bench without an NMR reference actually does. Search national
   lab technical notes and instrument vendor application notes.

**Named in the checklist, no source in the syllabus:**

4. Fluxgate magnetometers, operation and practical ceiling. Class 09 covers
   them with `jainov` and `hall` only, neither of which is a fluxgate document.
5. NMR teslameters as a calibration reference. Same gap, and it is the
   traceability route class 11 has to price.
6. AMR, GMR and TMR sensors: linearity, hysteresis, array potential. Class 09
   again. Vendor application notes are the likely route.
7. VSM and SQUID magnetometry, sample size limits and cost per run. Scoping
   only, to know what is out of reach.
8. Hysteresigraph and permeameter practice. The syllabus routes this through
   `a977` (paid) and `arnoldmeas`. Confirm `arnoldmeas` actually covers it.
9. IEC 60404-14, dipole moment measurement. Named in the checklist and in class
   08's note on `iec`, but `iec` points at 60404-5. Two different parts of the
   standard. Find out which one class 08 needs.
10. Magneto-optical viewing film. Class 20 covers it with no source.
11. NV diamond magnetometry. Class 20, scoping only.
12. Inverse methods, magnetization from a surface map. Class 18 covers field
    continuation but not the inverse problem the checklist names.
13. Corrosion mechanisms and coating systems for NdFeB, NiCuNi, epoxy,
    parylene. Class 27 has `sgobba` and `bahrdt`, which are magnetics documents,
    not corrosion documents. The checklist says corrosion is often the real
    lifecycle limit, so this gap sits under a load bearing claim.
14. Rotor and curved surface scanning with a rotary stage. Named in the
    checklist, absent from unit 4.
15. Pull force testers and production QC gates. What industry actually uses.

**Publication venues to mine, not documents:**

16. International Magnetic Measurement Workshop proceedings. The checklist calls
    this the most useful free source on field mapping practice. The syllabus
    reaches it only through two individual presentations, `immw20` and `immw12`.
    Find the proceedings index and work it properly for lit-2.
17. Magnet Technology conference papers.
18. IEEE Transactions on Magnetics, plus Sensors and Metals for measurement and
    aging papers.
19. Instrument vendor application notes: Lake Shore, Metrolab, Senis, Magcam.
20. Magnet supplier handbooks: Arnold, Vacuumschmelze, Dexter. Free, and they
    carry the working point and temperature curves classes 04 and 05 need.
21. CERN and ESRF magnetic measurement system documentation.

---

## Promotion rules

- A tier 3 item moves up when a class that cites it is scheduled.
- A tier 1 item that turns out narrower than its title suggests gets demoted,
  and the `contains` line in `library/verified.log` records why. That line is
  the point of the log.
- Every source read adds its own references here. Do not chase citations mid
  class. Add and move on.
