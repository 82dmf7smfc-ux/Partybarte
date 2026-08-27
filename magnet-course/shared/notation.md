# Notation, units, and sign conventions

One scheme, used by all 35 classes. If you need a symbol that is not here, add
it here first, then use it. That ordering is what stops a 35 part build from
drifting.

## Status: provisional on one point

`KICKOFF.md` phase 3 says to base the symbols and sign conventions on the CAS
lecture notes, so that this course matches the literature rather than inventing a
private scheme. **The CAS notes could not be fetched.** See
`library/verified.log`.

What that does and does not affect:

- **Unit conversions are settled.** They follow from the definitions of the
  gauss, the centimetre, and the erg, and they are derived in
  `tools/conversions.py` rather than looked up. They cannot be wrong in a way
  that fetching CAS would fix.
- **Symbol choices are settled enough.** B, H, M, J, Br, HcB, HcJ are close to
  universal in this field, and the syllabus itself uses them in class 03.
- **The sign and subscript convention for the second quadrant is provisional.**
  Specifically: whether the permeance coefficient is quoted signed or as a
  magnitude, and whether the demagnetizing field is written H_d or H_m. Both are
  marked below. Confirm against `hall`, `bahrdt` and `arnoldunder` before class
  04, which is the first class that depends on it.

Nothing else in the course is blocked by this. Work in any order you like.

## Quantities and symbols

| symbol | quantity | SI unit | CGS unit | notes |
|---|---|---|---|---|
| `B` | magnetic flux density | T | G | What a Hall probe reads. The one you measure. |
| `H` | magnetic field strength | A/m | Oe | What the circuit applies. Negative in the second quadrant. |
| `M` | magnetization | A/m | emu/cm^3 | Moment per unit volume. Same SI unit as H. |
| `J` | magnetic polarization | T | G | `J = mu0 M`. Same unit as B, which is the point of it. |
| `m` | magnetic moment | A m^2 | emu | What a Helmholtz coil measures. |
| `Phi` | magnetic flux | Wb | Mx | What a search coil integrates to. |
| `mu0` | permeability of free space | H/m | dimensionless, = 1 | See the note below. |
| `mu_r` | relative permeability | dimensionless | dimensionless | |
| `mu_rec` | recoil permeability | dimensionless | dimensionless | Slope of the recoil line, near 1.05 for sintered NdFeB. Verify before use. |
| `Br` | remanence | T | G | B at H = 0 on the normal curve. |
| `HcB` | coercivity | A/m | Oe | H where B = 0. The smaller of the two. |
| `HcJ` | intrinsic coercivity | A/m | Oe | H where J = 0. The one that governs irreversible loss. |
| `BHmax` | maximum energy product | kJ/m^3 | MGOe | Largest `|B H|` in the second quadrant. |
| `Hk` | knee field | A/m | Oe | Where the intrinsic curve departs from square. Definitions of "departs" differ, so state which one you used. |
| `N` | demagnetizing factor | dimensionless | dimensionless | **Different numbers in SI and CGS. See the trap below.** |
| `Pc` | permeance coefficient | dimensionless | dimensionless | Load line slope. Also written `B_d/H_d`. |
| `alpha_Br` | reversible temperature coefficient of Br | %/K | %/K | Negative for NdFeB. |
| `beta_HcJ` | reversible temperature coefficient of HcJ | %/K | %/K | Negative, and larger in magnitude than alpha. |
| `T` | temperature | K, and degrees C where a datasheet uses them | | Always say which. |
| `z` | lift-off, probe active area to magnet surface | mm | | The dimension that dominates a near field map. |

Subscripts: `d` for the working point in the demagnetizing quadrant, as in `B_d`
and `H_d`. `r` for remanent. `k` for knee.

## The two constitutive relations

SI, Sommerfeld convention, which is what this course uses:

```
B = mu0 (H + M)
J = mu0 M
B = mu0 H + J
```

CGS, Gaussian:

```
B = H + 4 pi M
```

The `4 pi` is not decoration. It is why a CGS demagnetizing factor and an SI
demagnetizing factor are different numbers under the same name, and it is the
single most common way a magnetics calculation goes silently wrong.

In free space, `M = 0`, so CGS gives `B = H` and a field of 1 G is a field of
1 Oe. The two quantities are numerically equal and get used interchangeably in
conversation. They are not the same quantity. The moment you are inside a
material, or inside a fixture with iron in it, treating them as interchangeable
gives an answer that is wrong by a factor you will not spot.

## Conversions

Computed by `tools/conversions.py`, captured in `shared/conversions.out`. Do not
retype these from another document. Rerun the script.

| from | to | factor |
|---|---|---|
| 1 T | G | 10^4 |
| 1 mT | G | 10 |
| 1 G | mT | 0.1 |
| 1 Oe | A/m | 79.5774715459, exactly 1000/(4 pi) |
| 1 A/m | Oe | 1.2566370614e-2, exactly 4 pi x 10^-3 |
| 1 kA/m | Oe | 12.566371 |
| 1 emu (moment) | A m^2 | 10^-3 |
| 1 A m^2 | emu | 10^3 |
| 1 emu/cm^3 | A/m | 10^3 |
| 1 Mx | Wb | 10^-8 |
| 1 Wb | Mx | 10^8 |
| 1 MGOe | kJ/m^3 | 7.9577 |
| 1 kJ/m^3 | MGOe | 0.125664 |

Every one of these is derived in the script from three definitions, `1 G = 1e-4
T`, `1 cm = 1e-2 m`, `1 erg = 1e-7 J`, plus `mu0`. None is a remembered number.

### Writing convention

SI first, CGS in parentheses on first use in each class, per `CLAUDE.md`:

> The remanence is 1.32 T (13.2 kG).

Units on every quantity, including intermediate steps. A bare number in a
calculation is a defect.

## The demagnetizing factor trap

```
SI:   H_d = -N M       with   N_x + N_y + N_z = 1
CGS:  H_d = -N' M      with   N'_x + N'_y + N'_z = 4 pi = 12.566371
```

Both are called N. Both appear in tables. A sphere is `N = 1/3` in SI and
`N' = 4 pi / 3 = 4.18879` in CGS. Take a value from the wrong table and the
answer is off by 12.57 with nothing in the units to warn you, because the
quantity is dimensionless in both systems.

Rule for this course: **always SI, always check that the three factors sum to
1.** If a table's factors sum to 12.57, it is a CGS table. Divide by `4 pi`.

## Sign conventions

Provisional, pending the CAS notes. Marked so that a later session can correct
one place rather than 35.

- The second quadrant is where a permanent magnet works. `H_d < 0` and `B_d > 0`
  there. The field inside the magnet opposes its own magnetization, which is
  why it is called demagnetizing.
- `H_d` is used for the internal field at the working point. Some texts write
  `H_m`. **Provisional.**
- The permeance coefficient is quoted here as a **positive magnitude**:

  ```
  Pc = B_d / (mu0 |H_d|)      SI
  Pc = B_d / |H_d|            CGS, since mu0 = 1 there
  ```

  Quoted this way a longer, thinner magnet has a larger `Pc` and sits higher up
  the curve. Written with the sign carried through, `Pc` is negative, and some
  sources do it that way. **Provisional. Confirm before class 04.** Whichever
  convention wins, state it in class 04 and never mix them.
- The load line through the origin has slope `Pc`, and the working point is
  where it crosses the normal demagnetization curve. Note that `Pc` computed in
  SI and `Pc` computed in CGS are the same number, because `mu0` cancels. This
  is the one place the two systems agree, and it is worth saying out loud
  because it makes `Pc` safe to take from an old CGS datasheet.

## The mu0 note

`mu0 = 4 pi x 10^-7 H/m` throughout this course.

Before 2019 that was exact, fixed by the definition of the ampere. The 2019 SI
redefinition made `mu0` an experimentally determined quantity, so it is no
longer exact and the current value has to come from CODATA.

This changes nothing on this bench. The offset is far below what a Hall probe of
0.1 percent class accuracy can resolve. Use `4 pi x 10^-7`.

Do not quote CODATA digits in any class until `nistunc` or an equivalent NIST
page has actually been fetched. Writing an unverified constant to ten
significant figures is the most convincing way to be wrong.

## Naming and formatting

- Symbols in prose are written in backticks: `B_d`, `HcJ`.
- Numbers carry units and a stated uncertainty wherever one is known.
- Temperatures state the scale: 20 degrees C, or 293 K, never a bare 20.
- Class files name calculated values the same way `worked.py` names the
  variables, so the reader can find the line that produced a number.
