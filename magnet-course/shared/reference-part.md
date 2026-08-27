# The reference part

The specific magnet used in every worked example in all 35 classes, and the
control sample measured every session.

## Status: not chosen. Three candidates required, zero named.

`KICKOFF.md` phase 4 requires three candidates, each **a specific purchasable
part with a datasheet URL you fetched**. No URL could be fetched in this session.
All 40 library sources failed, and so would any vendor datasheet. See
`library/verified.log`.

Naming three plausible part numbers from memory would satisfy the shape of the
request and destroy the thing it protects. The whole point of the sentence
"every worked example in all 35 classes uses this part, so a poor choice
propagates everywhere" is that this decision has to be right. A remembered part
number is a guess about a real object's dimensions, grade, coating, price, and
published temperature coefficients, and every one of those has to be true for
the worked examples to be true.

So this file holds everything the decision needs except the candidates: the
criteria, the weighting, a tension in the requirement that needs settling first,
the search plan, and a blank template. Fill it in on the first session with
network access. It is the second of two things blocking class material, per
`PROGRESS.md`.

---

## A tension worth settling before searching

The syllabus asks one part to do two jobs, and they pull in different
directions.

**Job one, the worked example part.** `CLAUDE.md` says every worked example uses
it. Worked examples run through demagnetization curves, working points, thermal
aging, corrosion, and the loss taxonomy. That argues for a part *representative*
of what the course is about, which is mostly sintered NdFeB: the material with
the largest temperature coefficients, the corrosion problem, and the aging
behaviour the bench exists to detect.

**Job two, the session control.** Class 14 defines the reference magnet as the
sample that never changes duty and separates instrument drift from real change.
That argues for the part that is *least* likely to change at all: highest
thermal stability, best corrosion resistance, and a working point far from the
knee. A control that ages is not a control.

A part that ages interestingly and a part that does not age are not the same
part. If one object has to do both, job two wins, because a drifting control
makes every other measurement in the programme unreadable, while a dull worked
example is merely dull.

**Recommendation: split the roles into two parts.**

- **The worked example part.** Sintered NdFeB, a grade whose datasheet publishes
  both `alpha_Br` and `beta_HcJ`. Simple geometry. This is the part in the
  prose.
- **The control part.** SmCo, chosen for thermal stability and because it needs
  no coating, so there is no coating to fail. It appears in class 14 and in the
  session checklist, and nowhere else.

The cost is one extra magnet and one extra column in the session log. The
benefit is that neither role compromises the other. Raise this before buying
anything: it is a change to what `CLAUDE.md` asks for, so it is logged in
`CHANGES.md` if adopted.

If the answer is one part only, choose SmCo and accept less representative
worked examples.

---

## Criteria, weighted

Weights reflect how expensive a mistake is. A part that is wrong on a heavy
criterion cannot be fixed later without rewriting every class that used it.

| # | criterion | weight | why it carries that weight |
|---|---|---|---|
| 1 | Published temperature coefficients for **both** `Br` and `HcJ` | 5 | Classes 05, 24, 25 and 26 need both. `beta_HcJ` is the one usually missing from a retailer listing, and it is the one that governs whether the working point crosses the knee. Without it, unit 6 has no numbers. |
| 2 | Analytically exact geometry | 5 | Class 21 models the part in Magpylib and class 23 subtracts model from measurement. A cuboid or an axially magnetized cylinder has a closed form solution, so the predicted map carries no meshing error. A ring, an arc segment, or a chamfered part puts modelling error into every residual for the life of the programme. |
| 3 | Stability over years | 5 | The control role. A part that drifts on its own makes the whole multi-year dataset uninterpretable, and you would not find out for a year. |
| 4 | Dimensions published with tolerances | 4 | The tolerance stack in class 13 and the lift-off budget both start from the part. A nominal dimension with no tolerance is a hole in the uncertainty budget in class 12. |
| 5 | Large enough to map at useful resolution | 4 | Needs enough points across the face that a map is a map. See the sizing note below. |
| 6 | Grade and supplier stated, not just "N52" | 4 | A grade letter from an unnamed factory is not a specification. Repurchasing an identical part in year three requires knowing who made this one. |
| 7 | Inexpensive | 3 | Buy several from the same batch: one control, one worked example, spares, and one to deliberately abuse in unit 6. Cheap makes that easy. |
| 8 | Coating specified, or no coating needed | 3 | Class 27 covers coating failure. An unspecified coating cannot be assessed. Uncoated SmCo sidesteps this entirely, which is a point in its favour for the control role. |
| 9 | Available in a second geometry, same grade | 2 | Lets class 04 compute two different permeance coefficients on the same material, which is the cheapest way to make that class concrete. |
| 10 | In stock, from a supplier likely to exist in five years | 2 | Replacing a lost control sample mid programme. |

## Sizing note

Not a hard rule, a starting point to check against the real probe once class 06
and class 15 have settled the active area and the grid.

The face needs enough sample points that a contour map has structure to show. At
a 0.5 mm step, a 25 mm face gives about 50 points across, which is comfortable.
At 12 mm it gives 24, which is thin but workable. Below about 10 mm the map
starts to be dominated by the probe geometry rather than the magnet.

Working the other way: the part should be large compared with the probe active
area, or class 06's active area averaging correction becomes the dominant term
rather than a correction. That argues for the larger end.

Against that, field strength at the probe and the force on the fixture both grow
with size, and a large NdFeB part is genuinely dangerous to handle. Something in
the 20 mm to 25 mm range, a few millimetres thick, is the region to search
first. **Confirm against the probe's active area before buying**, since the
ratio is what matters, not the absolute size.

---

## Search plan

Run this on the first session with network access.

1. Search vendors that publish full grade data sheets rather than retailer
   listings. The research checklist names Arnold, Vacuumschmelze and Dexter as
   suppliers whose handbooks are free and carry the curves. Start there, and
   with the suppliers behind `arnoldmeas` and `pmg88`, since those documents are
   already in the library.
2. For each candidate, fetch the datasheet and cache it into `library/pdf/`
   under a key like `refpart-<vendor>-<grade>`. Add it to `library/sources.json`
   like any other source. A datasheet the worked examples depend on is a source,
   not a shopping link.
3. Reject any part whose datasheet does not state `beta_HcJ`. That single filter
   removes most retailer listings and is the fastest way to shorten the list.
4. Check the geometry against criterion 2 before anything else, because a part
   that cannot be modelled exactly fails no matter how good its data is.
5. Fill in the template below for three survivors, score them, and recommend one
   for each role.
6. Then, and only then, mark this file settled and start class 06.

---

## Candidate template

Copy this block three times and fill it in. Leave a field blank rather than
guessing. A blank is information; a plausible number is not.

```
### Candidate N: <vendor> <part number>

Material and grade:
Geometry and nominal dimensions:
Dimensional tolerance:
Magnetization direction:
Coating:
Datasheet URL:
Datasheet fetched:            <date, and cached as library/pdf/KEY.pdf>
Br at 20 C:
HcB at 20 C:
HcJ at 20 C:
BHmax:
alpha_Br (%/K):               <over what temperature range>
beta_HcJ (%/K):               <over what temperature range>
Max service temperature:      <and at what permeance coefficient, since the
                               number is meaningless without one>
Price, and price per unit at quantity 5:
Supplier and lead time:

Scores, 1 to 5 against each weighted criterion:
  1 temperature coefficients   [ ]
  2 exact geometry             [ ]
  3 stability                  [ ]
  4 tolerances published       [ ]
  5 mappable size              [ ]
  6 grade and supplier stated  [ ]
  7 cost                       [ ]
  8 coating                    [ ]
  9 second geometry available  [ ]
  10 availability              [ ]
  Weighted total:

What the datasheet does not say:
```

That last line matters more than the scores. Class 10 is about reading a probe
datasheet like a metrologist and spotting what the vendor left out. The same
discipline applies here, and the reference part is the one component where an
unstated condition propagates into all 35 classes.

---

## When this file is settled

Update `PROGRESS.md`, remove the blocking note there, and record the decision
and its reasoning in this file rather than only the outcome. In two years the
argument will matter more than the conclusion.
