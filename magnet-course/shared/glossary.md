# Glossary

Stub. One entry for every term the syllabus and the research checklist already
use without defining. Definitions are operational: what the thing is, and what
it means for the bench.

## Status

These are working definitions, written to be replaced. `CLAUDE.md` says a claim
with no source and no derivation gets derived or deleted, and no source in this
repository has been fetched yet. So:

- Entries that are pure definition or naming stand as written.
- Entries marked **[confirm]** carry a claim that needs a source before any class
  leans on it. Usually a number, a mechanism, or a contested definition.
- No entry here carries a citation, because there is nothing yet to cite.

Add a term the first time a class uses it. Tighten an entry when the source that
settles it has been read, and note in `CHANGES.md` if the tightened version
contradicts a class already written.

Symbols and units live in `shared/notation.md`. This file does not repeat them.

---

**Active area** The region of the sensor that actually responds to the field.
Not a point. A Hall element averages the field over its area, so in a steep
gradient the reading is not the field at the nominal position.

**Active area averaging** The error from that averaging. Grows with the second
derivative of the field across the element, so it is worst near a pole edge and
at small lift-off. Class 06 quantifies it.

**Aliasing** Sampling a field on a grid too coarse for its spatial frequency
content, so fine structure reappears as false coarse structure. In a field map it
looks like a plausible feature, which is what makes it dangerous.

**AlNiCo** Aluminium nickel cobalt magnet family. High remanence, low coercivity,
excellent thermal stability. Easy to demagnetize by accident.

**AMR, GMR, TMR** Anisotropic, giant, and tunnelling magnetoresistance. Sensor
families that change resistance with field. Cheap, small, easy to array.
**[confirm]** linearity and hysteresis limits before using any of them for
absolute values.

**Backlash** Lost motion when a mechanical axis reverses direction. Makes a
scan taken left to right disagree with the same scan taken right to left.

**Bucking** Wiring rotating coil windings so a wanted large signal cancels,
leaving the small one you actually want to measure. **[confirm]** against the
Jain lecture set.

**Coercivity (HcB)** The reverse field that drives B to zero. Smaller than HcJ.
Does not tell you whether the magnet has been permanently damaged.

**Coil constant** The factor relating measured volt seconds to the quantity you
want, for a given coil geometry and turns count. Either computed from geometry
or calibrated against a known field. Both routes need checking against each
other.

**Contour interval** The spacing between contour lines on a map. Fixed once, in
class 19, and never changed, so maps from different years stay comparable.

**Control chart** A trend plot with limits derived from measured repeatability,
used to decide whether a change is real. Limits set by guesswork either cry wolf
or hide the effect.

**Demagnetization curve** The second quadrant of the hysteresis loop, where a
permanent magnet operates. Usually drawn twice, as the normal curve (B against
H) and the intrinsic curve (J against H).

**Demagnetizing factor** Geometry dependent factor relating a body's own
magnetization to the internal field opposing it. **Different numbers in SI and
CGS under the same name.** See the trap section in `shared/notation.md`.

**Dipole moment** The total moment of a part, in A m^2. What a Helmholtz coil
measures. A single number for a whole magnet, with no spatial information.

**Energy product (BHmax)** The largest product of B and H in the second
quadrant. A figure of merit for the material, not a description of any
particular magnet in any particular circuit.

**Ferrite** Ceramic magnet family, usually strontium or barium. Cheap, low
remanence, very good corrosion resistance, large temperature coefficient.

**Field continuation** Predicting the field on one plane from a measurement on
another, using the fact that the field satisfies Laplace's equation in the
source free region between them. **[confirm]** the noise amplification behaviour:
projecting away from the magnet is stable, projecting toward it is not.

**Fluxgate** Magnetometer using a driven saturable core. Far more sensitive than
a Hall probe, and saturates at a far lower field. For stray field and shielding
work, not for magnet faces.

**Fluxmeter** Instrument that integrates a coil voltage to give flux change.
Drifts, because integrating any offset gives a ramp.

**Hall effect** A current carrying conductor in a transverse field develops a
transverse voltage. The basis of the workhorse field probe.

**Helmholtz coil** A pair of coaxial coils separated by their radius, giving a
uniform region between them. Used here in reverse: extract a sample from the
centre and integrate the flux change to get its moment. The sample sees no
applied field, so the measurement cannot demagnetize it, which is what makes it
usable on the same part for years.

**Homing** Driving an axis to a repeatable reference position at the start of a
session. Without it, position coordinates are not comparable between sessions.

**Hysteresigraph** Instrument that measures a closed circuit B-H loop on a
specimen. A sample test, not a part test, because it needs a specific specimen
shape.

**Intrinsic coercivity (HcJ)** The reverse field that drives the polarization J
to zero. The number that governs whether loss is recoverable. Larger than HcB.

**Intrinsic curve** J against H. Shows what the material is doing, separately
from the flux the circuit carries.

**Irreversible loss** Loss that does not come back when the cause is removed,
but that remagnetizing restores. Distinct from reversible and from structural.

**Kinematic mount** A fixture constraining exactly six degrees of freedom, no
more, so a part returns to the same pose every time without being forced.
Overconstraint is what makes an ordinary fixture unrepeatable.

**Knee** The point where the intrinsic curve turns down from square. Operate
past it and the loss is irreversible. Moves with temperature, usually the wrong
way. **[confirm]** definitions of the knee differ between sources, so state
which one you used.

**Lift-off** Distance from the sensor active area to the magnet surface.
Dominates near field mapping error, because the field gradient there is steep.
**[confirm]** the magnitude with the reference part, in class 13.

**Load line** A straight line from the origin with slope equal to the permeance
coefficient. Its intersection with the normal demagnetization curve is the
working point.

**Magnetic viscosity** Slow, roughly logarithmic decrease of polarization with
time at constant temperature and constant working point. Thermal activation over
an energy barrier distribution. The effect the aging programme is built to
detect. **[confirm]** magnitude and timescale. This is the single most important
number in the course and currently rests on one unfetched source.

**Magneto-optical film** A film that renders pole layout visible via the Faraday
effect. Qualitative. Good for gross defects and pole geometry, no use for
numbers.

**NdFeB** Neodymium iron boron. Highest energy product in common use. Corrodes
readily, so it is nearly always coated. Large negative temperature coefficients.

**NMR teslameter** Measures field by proton resonance frequency. The most
accurate field measurement available, and it needs a uniform field over the
sample, which is why it is a calibration reference rather than a mapping tool.

**NV centre** Nitrogen vacancy defect in diamond, used for microscale field
imaging. Research instrument. In this course, scoped only to establish why it is
out of scope.

**Orthogonality** How close two scanner axes are to ninety degrees. An error
here shears the map, which looks like a real asymmetry in the magnet.

**Permeameter** Instrument for measuring the properties of a specimen in a
closed magnetic circuit.

**Permeance coefficient (Pc)** The slope of the load line. Set by the geometry
of the magnet and its magnetic circuit, not by the material. The same magnet
sits at a different working point in a different assembly, and therefore ages
differently. Sign convention is provisional, see `shared/notation.md`.

**Planar Hall effect** A spurious Hall voltage produced by the field component
in the plane of the sensor. Means probe orientation matters even for the
component you are not trying to measure.

**Polarization (J)** `mu0 M`, in tesla. The material's own contribution to B,
in the same unit as B.

**Pull force tester** Production gate that measures the force to detach a magnet
from a steel plate. Fast, coarse, blind to pole geometry.

**Quiver plot** A vector field rendered as arrows. Shows direction well, hides
magnitude structure.

**Recoil line** The minor loop path a magnet follows when the working point
moves after an excursion past the knee. Its slope is the recoil permeability.

**Recoil permeability** Slope of the recoil line, relative. Near 1.05 for
sintered NdFeB. **[confirm]** the value and the conditions it applies under.

**Reference magnet** A stable sample that never changes duty and is measured
every session. Separates instrument drift from real change in the samples under
study. Not chosen yet, see `shared/reference-part.md`.

**Registration** Aligning two maps taken at different times so they can be
subtracted. Alignment error looks exactly like a real change, which is why this
step decides whether differencing means anything.

**Remanence (Br)** Flux density remaining at zero applied field, in a closed
circuit. A material property. Not what you measure at the face of a magnet in
air.

**Repeatability** Spread of repeated measurements under unchanged conditions.
Different from accuracy, and it is the one that decides whether a trend is
readable. Unit 3 exists for this.

**Residual** Measured map minus predicted map. Where the information is, once
the expected field has been taken out.

**Reversible loss** Change that comes back on its own when the cause, usually
temperature, is removed. Not damage.

**Search coil** A pickup coil that produces a voltage proportional to the rate
of change of flux through it. Measures flux change, never field.

**SmCo** Samarium cobalt. Lower energy product than NdFeB, much better thermal
stability and corrosion resistance. The usual choice when stability matters more
than strength.

**Soak** Holding a part at elevated temperature for a set time, to force
whatever irreversible loss is going to happen before the part goes into service.
**[confirm]** standard soak times and temperatures.

**SQUID** Superconducting quantum interference device. Extremely sensitive
magnetometer for small research samples.

**Stabilization** The deliberate application of a soak, or of a reverse field,
so that later behaviour is predictable. A stabilized magnet has already lost
what it was going to lose.

**Straightness** How far an axis deviates from a straight line as it travels.
Turns into a position error that varies across the map.

**Structural loss** Loss from metallurgical or physical change: corrosion,
cracking, oxidation. Remagnetizing does not restore it, because the material
itself has changed.

**Traceability** An unbroken chain of calibrations linking your reading to a
national standard, each with stated uncertainty. Expensive. Class 11 decides how
much of it is worth buying.

**Type A evaluation** Uncertainty evaluated from the statistics of repeated
measurements.

**Type B evaluation** Uncertainty evaluated by any other means: datasheet
figures, calibration certificates, judgement about a distribution.

**Uncertainty budget** The itemised list of every uncertainty contribution and
how they combine. Class 12. Without one, no claim about a trend can be defended.

**VSM** Vibrating sample magnetometer. Vibrates a small sample near pickup coils
to measure moment. Research sample sizes.

**Working point** Where the magnet actually sits on its demagnetization curve
inside its fixture, set by the permeance coefficient. Aging depends on it, so a
loose magnet and an assembled magnet are not the same experiment.
