"""Compute the SI to CGS conversions used throughout this course.

Nothing here is a looked-up constant except mu0 and the SI prefixes. Every
conversion factor is derived from the definitions so the derivation is visible
and checkable, per the numerical rigor rules in CLAUDE.md.

Run:
    python3 tools/conversions.py
"""

import math

# The only inputs.
MU0 = 4e-7 * math.pi        # H/m, conventional value. See the note at the end.
GAUSS = 1e-4                # T, definition of the gauss
CM = 1e-2                   # m, definition of the centimetre
ERG = 1e-7                  # J, definition of the erg


def rule(title):
    print("\n" + title)
    print("-" * len(title))


print("Inputs")
print("-" * 6)
print("mu0   = 4*pi*1e-7      = %.12e H/m" % MU0)
print("gauss = 1e-4 T, cm = 1e-2 m, erg = 1e-7 J")

rule("Flux density B, and polarization J")
# 1 T = 1/GAUSS gauss, straight from the definition of the gauss.
t_to_g = 1.0 / GAUSS
print("1 T   = 1/1e-4                         = %g G" % t_to_g)
print("1 mT  = 1e-3 T                         = %g G" % (t_to_g * 1e-3))
print("1 G   = 1e-4 T                         = %g mT" % (GAUSS * 1e3))

rule("Field strength H")
# In vacuum, CGS writes B(G) = H(Oe). So 1 Oe is the H that produces 1 G:
#     H = B / mu0 = (1 gauss) / mu0
oe_to_am = GAUSS / MU0
print("1 Oe  = (1 G)/mu0 = 1e-4/(4*pi*1e-7)   = %.10f A/m" % oe_to_am)
print("      = 1000/(4*pi) exactly            = %.10f A/m" % (1000 / (4 * math.pi)))
print("1 A/m = mu0/(1 G)                      = %.10e Oe" % (1 / oe_to_am))
print("      = 4*pi*1e-3 exactly              = %.10e Oe" % (4 * math.pi * 1e-3))
print("1 kA/m= 1e3 A/m                        = %.6f Oe" % (1e3 / oe_to_am))

rule("Magnetization M, same units as H")
# 1 emu of moment is 1 erg/G. Per cm^3 that is an A/m.
emu_moment = ERG / GAUSS                      # J/T = A m^2
emu_per_cc = emu_moment / CM ** 3             # A/m
print("1 emu (moment) = 1 erg/G               = %g A m^2" % emu_moment)
print("1 A m^2                                = %g emu" % (1 / emu_moment))
print("1 emu/cm^3                             = %g A/m" % emu_per_cc)
print("1 emu/cm^3, written CGS style as 4*pi*M= %.6f G" % (4 * math.pi))

rule("Magnetic flux")
# Wb = T m^2, Mx = G cm^2
mx = GAUSS * CM ** 2
print("1 Mx  = 1 G cm^2                       = %g Wb" % mx)
print("1 Wb                                   = %g Mx" % (1 / mx))

rule("Energy product BH")
# 1 G Oe = (1e-4 T)(oe_to_am A/m) = J/m^3
g_oe = GAUSS * oe_to_am
print("1 G Oe                                 = %.10f J/m^3" % g_oe)
print("1 MGOe = 1e6 G Oe                      = %.4f kJ/m^3" % (1e6 * g_oe / 1e3))
print("1 kJ/m^3                               = %.6f MGOe" % (1e3 / (1e6 * g_oe)))

rule("Demagnetizing factor, the trap")
print("SI:  H_d = -N M          with  sum(N_x,N_y,N_z) = 1")
print("CGS: H_d = -N' M         with  sum(N'x,N'y,N'z) = 4*pi = %.6f" % (4 * math.pi))
print("N' = 4*pi*N, so a factor of %.6f separates two numbers both called N."
      % (4 * math.pi))

rule("Round trip check")
# Take a plausible remanence and push it through both directions.
br_t = 1.32
br_g = br_t * t_to_g
print("Br = %.3f T -> %.0f G -> %.6f T" % (br_t, br_g, br_g * GAUSS))
hcj_ka = 875.0
hcj_oe = hcj_ka * 1e3 / oe_to_am
print("HcJ = %.1f kA/m -> %.2f Oe -> %.6f kA/m"
      % (hcj_ka, hcj_oe, hcj_oe * oe_to_am / 1e3))
bh_kj = 330.0
bh_mgoe = bh_kj * 1e3 / (1e6 * g_oe)
print("BHmax = %.1f kJ/m^3 -> %.4f MGOe -> %.6f kJ/m^3"
      % (bh_kj, bh_mgoe, bh_mgoe * 1e6 * g_oe / 1e3))
print("\nThe three values above are round trip test inputs, not a real part.")
print("The reference part is not chosen yet. See shared/reference-part.md.")

rule("Note on mu0")
print("Before 2019, mu0 was exactly 4*pi*1e-7 H/m by definition of the ampere.")
print("The 2019 SI redefinition made mu0 an experimentally determined quantity.")
print("It is no longer exact, and the current value must be read from CODATA")
print("rather than assumed. The offset is far below anything this bench can")
print("resolve: a Hall probe of 0.1 percent class accuracy is many orders of")
print("magnitude coarser. Use 4*pi*1e-7 throughout. Do not quote CODATA digits")
print("in any class until the NIST page has actually been fetched.")
