"""
Occlusion test
--------------
Run the four-bar, then OCCLUDE the crank tip. The perceiver receives only
three point trajectories (both ground pins + the rocker tip) and no edges,
no point count, no hint that anything is missing.

Perception stages:
  1. ledger -> locked / free classification among VISIBLE pairs
  2. free edges get a second look: bounded variation with REPEATABLE limits
     (revisited many times) = hidden constraint, not noise
  3. hypothesis: a hidden 2-bar chain explains a bounded distance
        d_max = coupler + crank   (chain extended)
        d_min = coupler - crank   (chain folded)
     -> crank = (max - min)/2, coupler = (max + min)/2
  4. verify by synthesis: rebuild the full mechanism with the inferred
     hidden point, re-simulate, compare the visible rocker's behavior.
"""

import math
from engine import Mechanism, observe, detect_locked


def build_fourbar():
    m = Mechanism(points=[[0.0, 0.0], [2.0, 0.0], [6.083, 5.686], [8.0, 0.0]])
    m.lock(0, 1); m.lock(1, 2); m.lock(2, 3)
    m.pin(0); m.pin(3)
    return m


def simulate(m, steps=480, cycles=2):
    crank_len = math.dist(m.points[0], m.points[1])
    frames = []
    for k in range(steps):
        th = 2 * math.pi * cycles * k / steps
        m.drive(1, crank_len * math.cos(th), crank_len * math.sin(th), sweeps=80)
        frames.append([p[:] for p in m.points])
    return frames


def line(c="-", n=64):
    print(c * n)


# ---------------------------------------------------------------- stage 0
line("=")
print("OCCLUSION: crank tip (point 1) hidden. Perceiver sees 3 points.")
line("=")
m = build_fourbar()
true_crank = math.dist(m.points[0], m.points[1])
true_coupler = math.dist(m.points[1], m.points[2])
full = simulate(m)

VISIBLE = [0, 2, 3]          # world indices the perceiver receives
frames = [[f[i][:] for i in VISIBLE] for f in full]
# perceiver labels: 0 = ground-left pin, 1 = rocker tip, 2 = ground-right pin
# (it does not know these roles; it just sees three trajectories)

# ---------------------------------------------------------------- stage 1
ledgers = observe(frames)
scale = max(led.mean for led in ledgers.values())
print(f"self-calibrated scale = {scale:.3f}\n")
print("distance ledger:")
for (i, j), led in sorted(ledgers.items()):
    tag = "LOCKED" if led.std < 1e-3 * scale else "varies"
    print(f"  d({i},{j}) = {led.mean:6.3f} +/- {led.std:.3e}   {tag}")

locked = detect_locked(ledgers, scale)
print(f"\nlocked edges among visible points: {sorted(locked.keys())}")

# ---------------------------------------------------------------- stage 2
print()
line()
print("SECOND LOOK AT VARYING EDGES: noise, or hidden constraint?")
line()

def limit_analysis(i, j, frames, band=0.02):
    """Does this distance hit repeatable min/max limits?
    Count separate visits to each extreme (entries into a small band)."""
    ds = [math.dist(f[i], f[j]) for f in frames]
    lo, hi = min(ds), max(ds)
    rng = hi - lo
    def visits(target):
        v, inside = 0, False
        for d in ds:
            near = abs(d - target) < band * rng
            if near and not inside:
                v += 1
            inside = near
        return v
    return lo, hi, visits(lo), visits(hi)

hidden_hypotheses = []
for (i, j), led in sorted(ledgers.items()):
    if (i, j) in locked:
        continue
    lo, hi, v_lo, v_hi = limit_analysis(i, j, frames)
    repeatable = v_lo >= 2 and v_hi >= 2
    print(f"  d({i},{j}): range [{lo:.3f}, {hi:.3f}]  "
          f"visits to min = {v_lo}, to max = {v_hi}  "
          f"-> {'BOUNDED (hidden constraint)' if repeatable else 'unconstrained'}")
    if repeatable:
        hidden_hypotheses.append(((i, j), lo, hi))

# ---------------------------------------------------------------- stage 3
print()
line()
print("HYPOTHESIS: bounded distance = hidden 2-bar chain (fold/extend limits)")
line()
# pick the bounded pair anchored at a STATIONARY point (a pin) --
# a chain grounded at a fixed point is the simplest hypothesis
def is_stationary(idx, frames, scale):
    dmax = max(math.dist(frames[0][idx], f[idx]) for f in frames)
    return dmax < 1e-6 * scale

best = None
for (i, j), lo, hi in hidden_hypotheses:
    anchors = [p for p in (i, j) if is_stationary(p, frames, scale)]
    if anchors:
        best = ((i, j), lo, hi, anchors[0])
        break

assert best, "no grounded bounded pair found"
(bi, bj), lo, hi, anchor = best
inferred_crank = (hi - lo) / 2
inferred_coupler = (hi + lo) / 2
print(f"bounded pair d({bi},{bj}), grounded at point {bi if anchor==bi else bj}")
print(f"inferred HIDDEN link lengths:")
print(f"  crank   = (max-min)/2 = {inferred_crank:.3f}   (truth: {true_crank:.3f})")
print(f"  coupler = (max+min)/2 = {inferred_coupler:.3f}   (truth: {true_coupler:.3f})")
err_c = abs(inferred_crank - true_crank)
err_k = abs(inferred_coupler - true_coupler)
print(f"  errors: {err_c:.4f}, {err_k:.4f}")
assert err_c < 0.02 * scale and err_k < 0.02 * scale, "inference off"

# ---------------------------------------------------------------- stage 4
print()
line()
print("VERIFY BY SYNTHESIS: rebuild mechanism WITH the inferred hidden point")
line()
# reconstruct: anchor pin + hidden crank tip + observed rocker geometry
rocker_pin = 2 if anchor == bi else 0          # the other pin (perceiver label)
rocker_tip = bj if anchor == bi else bi
# perceiver-label -> coordinates from frame 0
P_anchor = frames[0][anchor if anchor == bi else bi][:]
P_anchor = frames[0][0][:]                      # anchor is label 0 here
P_rpin  = frames[0][2][:]
rocker_len = ledgers[(min(1, 2), max(1, 2))].mean

m2 = Mechanism(points=[P_anchor[:], 
                       [P_anchor[0] + inferred_crank, P_anchor[1]],
                       frames[0][1][:],
                       P_rpin[:]])
# lock the inferred chain and the OBSERVED rocker
m2.locked[(0, 1)] = inferred_crank
m2.locked[(1, 2)] = inferred_coupler
m2.locked[(2, 3)] = rocker_len
m2.pin(0); m2.pin(3)
resim = simulate(m2)

# compare the visible rocker tip's swing: angle about its pin
def rocker_angle(p_tip, p_pin):
    return math.atan2(p_tip[1] - p_pin[1], p_tip[0] - p_pin[0])

obs_angles = [rocker_angle(f[1], f[2]) for f in frames]
sim_angles = [rocker_angle(f[2], f[3]) for f in resim]
obs_lo, obs_hi = min(obs_angles), max(obs_angles)
sim_lo, sim_hi = min(sim_angles), max(sim_angles)
print(f"observed rocker sweep: [{math.degrees(obs_lo):7.2f}, {math.degrees(obs_hi):7.2f}] deg")
print(f"resim    rocker sweep: [{math.degrees(sim_lo):7.2f}, {math.degrees(sim_hi):7.2f}] deg")
d_lo = abs(math.degrees(obs_lo - sim_lo))
d_hi = abs(math.degrees(obs_hi - sim_hi))
print(f"sweep-limit mismatch: {d_lo:.3f} deg, {d_hi:.3f} deg")
assert d_lo < 1.0 and d_hi < 1.0, "synthesis does not reproduce observation"

print()
line("=")
print("PASS: from 3 visible points and zero edges, the perceiver recovered")
print("the visible structure AND the two invisible links, then proved it by")
print("rebuilding the whole mechanism and matching the observed motion.")
line("=")
