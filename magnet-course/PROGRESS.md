# Progress

Status of all 35 classes. Update at the end of every session, per `CLAUDE.md`.

Generated from the `UNITS` array in `syllabus/magnet-bench-syllabus.html` on
2026-08-25. Class ids, titles and durations are copied from the syllabus rather
than typed, so they cannot drift from it.

A class is `complete` only when every item in the definition of done in
`CLAUDE.md` is true. Anything less is `in progress`, whatever it looks like.

Total contact time in the syllabus: 3630 minutes, about 60 hours.

## Directory naming

One rule, no exceptions, so all 35 stay consistent:

    cNN-<first three significant words of the title, lowercased, hyphenated>

Significant means not one of: the, a, an, and, or, of, for, to, in, on, at,
with, from, is, are, it, its, that, this, what, which, where, how, as, by,
into. Hyphenated compounds such as `lift-off` count as one word. The
directory names in the tables below are the output of that rule and are
authoritative.

`CLAUDE.md` shows `c01-bench-spec` in its layout example. That is not what the
rule produces. See `CHANGES.md` item 8.

## Status table

### Unit 0: Orientation

| Directory | Title | Min | Status | Date | Words | Sources used | Open questions |
|---|---|---|---|---|---|---|---|
| `c01-bench-must-do` | What the bench must do, and what good means | 90 | not started | | | | |

### Unit 1: Physical foundations

| Directory | Title | Min | Status | Date | Words | Sources used | Open questions |
|---|---|---|---|---|---|---|---|
| `c02-units-quantities-b` | Units and quantities: B, H, M, J, and the CGS trap | 90 | not started | | | | |
| `c03-demagnetization-curve-intrinsic` | The demagnetization curve and the intrinsic curve | 90 | not started | | | | |
| `c04-working-point-permeance` | Working point, permeance coefficient, and load lines | 90 | not started | | | | |
| `c05-materials-map-ndfeb` | Materials map: NdFeB, SmCo, ferrite, AlNiCo | 90 | not started | | | | |

### Unit 2: Sensors and instruments

| Directory | Title | Min | Status | Date | Words | Sources used | Open questions |
|---|---|---|---|---|---|---|---|
| `c06-hall-sensors-physics` | Hall sensors: physics, planar effect, active area, offset | 120 | not started | | | | |
| `c07-search-coils-fluxmeters` | Search coils and fluxmeters | 120 | not started | | | | |
| `c08-helmholtz-coil-magnetometry` | Helmholtz coil magnetometry | 90 | not started | | | | |
| `c09-fluxgate-nmr-magnetoresistive` | Fluxgate, NMR, and magnetoresistive sensors | 90 | not started | | | | |
| `c10-reading-probe-datasheet` | Reading a probe datasheet like a metrologist | 90 | not started | | | | |

### Unit 3: Metrology discipline

| Directory | Title | Min | Status | Date | Words | Sources used | Open questions |
|---|---|---|---|---|---|---|---|
| `c11-calibration-traceability` | Calibration and traceability | 90 | not started | | | | |
| `c12-uncertainty-budgets-type` | Uncertainty budgets, type A and type B | 120 | not started | | | | |
| `c13-fixturing-lift-off-kinematic` | Fixturing, lift-off, and kinematic location | 120 | not started | | | | |
| `c14-reference-magnet-session` | The reference magnet and session control | 90 | not started | | | | |

### Unit 4: Mapping and imaging

| Directory | Title | Min | Status | Date | Words | Sources used | Open questions |
|---|---|---|---|---|---|---|---|
| `c15-points-maps-grids` | From points to maps: grids, sampling, aliasing | 90 | not started | | | | |
| `c16-scanner-kinematics-motion` | Scanner kinematics and motion control | 120 | not started | | | | |
| `c17-rotating-coils-harmonic` | Rotating coils and harmonic analysis | 120 | not started | | | | |
| `c18-field-continuation-plane` | Field continuation and plane to plane projection | 120 | not started | | | | |
| `c19-rendering-contour-intervals` | Rendering: contour intervals and the fixed scale rule | 90 | not started | | | | |
| `c20-imaging-alternatives-film` | Imaging alternatives: film, arrays, NV centres | 90 | not started | | | | |

### Unit 5: Modeling and residuals

| Directory | Title | Min | Status | Date | Words | Sources used | Open questions |
|---|---|---|---|---|---|---|---|
| `c21-analytic-modeling-magpylib` | Analytic modeling with Magpylib | 120 | not started | | | | |
| `c22-fea-femm-3d` | FEA with FEMM, and 3D with Radia | 120 | not started | | | | |
| `c23-predicted-minus-measured` | Predicted minus measured | 90 | not started | | | | |

### Unit 6: Aging and lifecycle

| Directory | Title | Min | Status | Date | Words | Sources used | Open questions |
|---|---|---|---|---|---|---|---|
| `c24-loss-taxonomy-reversible` | Loss taxonomy: reversible, irreversible, structural | 90 | not started | | | | |
| `c25-thermal-aging-stabilization` | Thermal aging and stabilization protocols | 120 | not started | | | | |
| `c26-magnetic-viscosity-long` | Magnetic viscosity and long term drift | 90 | not started | | | | |
| `c27-corrosion-coatings-mechanical` | Corrosion, coatings, and mechanical damage | 90 | not started | | | | |

### Unit 7: Bench build

| Directory | Title | Min | Status | Date | Words | Sources used | Open questions |
|---|---|---|---|---|---|---|---|
| `c28-bom-sourcing` | BOM and sourcing | 120 | not started | | | | |
| `c29-mechanical-build-alignment` | Mechanical build and alignment | 120 | not started | | | | |
| `c30-electronics-noise-grounding` | Electronics, noise, grounding, and shielding | 120 | not started | | | | |
| `c31-software-acquisition-file` | Software: acquisition, file format, metadata | 120 | not started | | | | |
| `c32-commissioning-acceptance-test` | Commissioning and acceptance test | 120 | not started | | | | |

### Unit 8: Running the program

| Directory | Title | Min | Status | Date | Words | Sources used | Open questions |
|---|---|---|---|---|---|---|---|
| `c33-baseline-campaign-archive` | Baseline campaign and archive | 120 | not started | | | | |
| `c34-trending-control-charts` | Trending and control charts | 90 | not started | | | | |
| `c35-reporting-purchase-proposal` | Reporting and the purchase proposal | 90 | not started | | | | |

## Blocked, pending network access

Session zero ran with outbound network egress denied. Four session zero
deliverables could not be produced, and none of them is safe to guess at. See
the header of `library/verified.log` for the evidence.

| Deliverable | Why it is blocked |
|---|---|
| `library/pdf/` cache | No source could be fetched. 40 sources, 30 hosts, all refused. |
| `library/export.bib` | Generated from verified entries. There are none. |
| `library/queue.md` contents | Seeded from bibliographies of sources nobody has opened. |
| `shared/notation.md` | `KICKOFF.md` requires it be based on the CAS lecture notes. Those could not be fetched. |
| `shared/glossary.md` | Follows notation. Terms are defined once and must match the sources. |
| `shared/reference-part.md` | Requires three candidate parts, each with a datasheet URL actually fetched. |

Every worked example in all 35 classes uses the reference part, so choosing it
without reading a datasheet would propagate one guess through the whole course.
It is deferred rather than guessed.

No class can meet the definition of done until this clears, for a second reason
as well: `CLAUDE.md` requires `worked.py` to use magpylib, and PyPI is refused
by the same policy.

## Open questions carried forward

Answers wanted from the author, raised at the end of session zero. Numbered
items refer to `CHANGES.md`.

1. Tier definitions for `library/queue.md`. A working definition is proposed in
   that file. Item 2.
2. The literature review specification that `KICKOFF.md` refers to. Item 3.
3. Whether `magcamieee` should stay in the syllabus at all. Item 5.
4. Commit and branch policy for classes. Item 7.

## Next session

Open network egress for the 30 hosts in `library/sources.json`, plus PyPI, then
run `library/fetch_sources.py`. Read what lands, write the `contents` line for
each source, seed the queue from the bibliographies, generate `export.bib`, and
then write `notation.md`, `glossary.md` and `reference-part.md`. That closes
kickoff phases 2 to 4. Class 06 follows, per `BUILD_PROMPTS.md`.
