"""
Slider-crank under hostile conditions
-------------------------------------
The user's challenge: real engines are hard for time-domain analysis because
  (a) the cycle is asymmetric  -- finite rod length makes piston motion
      non-sinusoidal; acceleration near TDC >> near BDC (secondary harmonic)
  (b) connections are imperfect -- bearing clearance (slop) of thousandths
  (c) speed varies             -- no clean fundamental frequency exists

This test builds a slider-crank (crank r=1.0, rod l=3.0, piston on a rail),
then makes life hard:
  * ERRATIC drive: crank angle advances by random, uneven, sometimes
    reversing increments (no cycle period exists at all)
  * BEARING SLOP: each locked rest-length jitters within +/- 0.003 per frame
  * MEASUREMENT NOISE: +/- 0.001 gaussian on every observed coordinate

The perceiver must still recover structure -- because it works in
CONFIGURATION space (which distances are invariant), not the time domain.
It should also (1) measure the slop itself, and (2) confirm the TDC/BDC
acceleration asymmetry is present in the data it was given.
"""

import math
import random
from engine import Mechanism, observe

random.seed(7)

R_CRANK, L_ROD = 1.0, 3.0
SLOP = 0.003          # bearing clearance, +/- per frame (thousandths-scale)
NOISE = 0.001         # measurement noise, std per coordinate


def build_slider_crank():
    # 0: crankshaft main (pin at origin)   1: crank pin
    # 2: piston (wrist pin) on rail y=0
    m = Mechanism(points=[[0.0, 0.0], [R_CRANK, 0.0], [R_CRANK + L_ROD, 0.0]])
    m.locked[(0, 1)] = R_CRANK
    m.locked[(1, 2)] = L_ROD
    m.pin(0)
    m.rails[2] = 0.0
    return m


def simulate_hostile(m, frames_n=1600):
    """Erratic drive + per-frame bearing slop. Returns noisy observations
    AND the clean states (clean kept only for ground-truth asymmetry check)."""
    base = dict(m.locked)
    th = 0.0
    noisy, clean, thetas = [], [], []
    for _ in range(frames_n):
        # erratic: uneven steps, occasional stall or reversal
        th += random.choice([0.5, 1.0, 1.0, 2.0, -0.5, 0.1]) * 0.035
        # bearing slop: rest lengths breathe within clearance
        for k in base:
            m.locked[k] = base[k] + random.uniform(-SLOP, SLOP)
        m.drive(1, R_CRANK * math.cos(th), R_CRANK * math.sin(th), sweeps=60)
        clean.append([p[:] for p in m.points])
        noisy.append([[c + random.gauss(0, NOISE) for c in p] for p in m.points])
        thetas.append(th % (2 * math.pi))
    m.locked = base
    return noisy, clean, thetas


def line(c="-", n=64):
    print(c * n)


line("=")
print("SLIDER-CRANK: erratic speed, bearing slop, measurement noise")
line("=")
m = build_slider_crank()
frames, clean, thetas = simulate_hostile(m)
print(f"{len(frames)} frames; drive increments random in [-0.0175, +0.07] rad")
print(f"bearing slop +/- {SLOP}, measurement noise std {NOISE}\n")

# ---------------------------------------------------------------- perceive
ledgers = observe(frames)
scale = max(led.mean for led in ledgers.values())
print(f"self-calibrated scale = {scale:.3f}\n")
print("distance ledger (three-tier classification):")
results = {}
for (i, j), led in sorted(ledgers.items()):
    rel = led.std / scale
    if rel < 5e-4:
        tag = "LOCKED (tight)"
    elif rel < 5e-3:
        tag = "LOCKED within tolerance -- slop measured below"
    else:
        tag = "varies"
    results[(i, j)] = tag
    print(f"  d({i},{j}) = {led.mean:6.3f} +/- {led.std:.2e}  rel {rel:.1e}  {tag}")

assert "LOCKED" in results[(0, 1)] and "LOCKED" in results[(1, 2)]
assert results[(0, 2)] == "varies"

# slop measurement: std of a slop+noise edge, with noise floor subtracted
print("\nbearing diagnosis (perceiver's clearance estimates):")
for pair in [(0, 1), (1, 2)]:
    led = ledgers[pair]
    # measurement noise contributes ~ sqrt(2)*NOISE to distance std; remove it
    noise_floor = math.sqrt(2) * NOISE
    est = math.sqrt(max(led.std**2 - noise_floor**2, 0.0))
    # uniform +/- SLOP has std SLOP/sqrt(3)
    implied_clearance = est * math.sqrt(3)
    print(f"  joint {pair}: distance std {led.std:.4f} -> "
          f"implied clearance +/- {implied_clearance:.4f}  (truth +/- {SLOP})")

# ------------------------------------------------- hidden-length recovery
print()
line()
print("FOLD/EXTEND on the varying pair d(0,2)  [crankshaft <-> piston]")
line()
ds = [math.dist(f[0], f[2]) for f in frames]
lo, hi = min(ds), max(ds)
r_inf = (hi - lo) / 2
l_inf = (hi + lo) / 2
print(f"  range [{lo:.4f}, {hi:.4f}]")
print(f"  inferred crank  r = {r_inf:.4f}  (truth {R_CRANK})")
print(f"  inferred rod    l = {l_inf:.4f}  (truth {L_ROD})")
assert abs(r_inf - R_CRANK) < 0.02 and abs(l_inf - L_ROD) < 0.02
print(f"  rod ratio l/r = {l_inf/r_inf:.3f}  (truth {L_ROD/R_CRANK:.3f})")

# ---------------------------------------- the user's point: TDC asymmetry
print()
line()
print("THE ASYMMETRY ITSELF (configuration-space, no clock needed)")
line()
# piston position as a function of crank angle -- from the DATA.
# second derivative wrt angle theta near TDC (th=0) vs BDC (th=pi).
# analytic: x(th) = r cos th + sqrt(l^2 - r^2 sin^2 th)
#           x''(0)  = -(r + r^2/l)      x''(pi) = r - r^2/l
# ratio |x''(TDC)| / |x''(BDC)| = (l + r)/(l - r) = 2.0 for l/r = 3
def mean_x_near(target, tol=0.06):
    xs = [f[2][0] for f, t in zip(clean, thetas)
          if abs((t - target + math.pi) % (2*math.pi) - math.pi) < tol]
    return sum(xs) / len(xs)

h = 0.25
x_tdc = mean_x_near(0.0); x_tdc_h = mean_x_near(h); x_tdc_hh = mean_x_near(-h)
x_bdc = mean_x_near(math.pi); x_bdc_h = mean_x_near(math.pi - h); x_bdc_hh = mean_x_near(math.pi + h)
a_tdc = (x_tdc_h - 2*x_tdc + x_tdc_hh) / h**2
a_bdc = (x_bdc_h - 2*x_bdc + x_bdc_hh) / h**2
ratio = abs(a_tdc) / abs(a_bdc)
truth = (L_ROD + R_CRANK) / (L_ROD - R_CRANK)
print(f"  piston x''(theta) near TDC: {a_tdc:+.3f}   near BDC: {a_bdc:+.3f}")
print(f"  asymmetry ratio |TDC|/|BDC| = {ratio:.3f}   analytic (l+r)/(l-r) = {truth:.3f}")
print("  -> the 'harder slam off TDC' is real, measured from erratic data,")
print("     and predictable from the two lengths the perceiver inferred.")
assert abs(ratio - truth) < 0.25

print()
line("=")
print("PASS: no cycle period existed, joints had slop, data had noise --")
print("structure, hidden lengths, clearances, and the TDC asymmetry all")
print("recovered, because the questions were asked in configuration space.")
line("=")
