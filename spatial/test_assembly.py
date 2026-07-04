"""
Assembly by inverse perception
------------------------------
A hidden four-bar draws a coupler curve. The designer receives ONLY the
curve -- a bag of target points, no lengths, no mechanism, no hint --
and must ASSEMBLE a machine that draws it.

The loop is perception reversed:
    propose lengths -> Grashof pre-screen (free rejection)
                    -> simulate (forward solver)
                    -> perceive the drawn curve
                    -> compare to target (symmetric chamfer distance)
                    -> keep / refine
Random exploration first, coordinate refinement second. The judge is the
same machinery that did all of today's perception.
"""

import math
import random
from engine import Mechanism

random.seed(42)


def build(crank, coupler, rocker, ground):
    """Assemble a four-bar from four lengths. Returns None if it cannot
    close at the start pose."""
    x = (ground**2 + coupler**2 - rocker**2 + crank**2)  # rough feasibility
    # place crank tip at angle 0; solve rocker-tip by circle intersection
    p1 = [crank, 0.0]
    d = math.dist(p1, [ground, 0.0])
    if d > coupler + rocker or d < abs(coupler - rocker):
        return None
    a = (coupler**2 - rocker**2 + d**2) / (2 * d)
    h2 = coupler**2 - a**2
    if h2 < 0:
        return None
    h = math.sqrt(h2)
    ux, uy = (ground - p1[0]) / d, (0.0 - p1[1]) / d
    p2 = [p1[0] + a * ux - h * uy, p1[1] + a * uy + h * ux]
    m = Mechanism(points=[[0.0, 0.0], p1, p2, [ground, 0.0]])
    m.locked[(0, 1)] = crank
    m.locked[(1, 2)] = coupler
    m.locked[(2, 3)] = rocker
    m.pin(0); m.pin(3)
    return m


def grashof_crank_rocker(crank, coupler, rocker, ground):
    lens = sorted([crank, coupler, rocker, ground])
    return (lens[0] + lens[3] <= lens[1] + lens[2]) and \
           (min(crank, coupler, rocker, ground) == crank)


def coupler_curve(crank, coupler, rocker, ground, steps=48):
    if not grashof_crank_rocker(crank, coupler, rocker, ground):
        return None
    m = build(crank, coupler, rocker, ground)
    if m is None:
        return None
    pts = []
    for k in range(steps):
        th = 2 * math.pi * k / steps
        m.drive(1, crank * math.cos(th), crank * math.sin(th), sweeps=50)
        pts.append(((m.points[1][0] + m.points[2][0]) / 2,
                    (m.points[1][1] + m.points[2][1]) / 2))
    return pts


def chamfer(a, b):
    """Symmetric mean nearest-point distance between two point sets."""
    def one_way(p, q):
        return sum(min(math.dist(x, y) for y in q) for x in p) / len(p)
    return 0.5 * (one_way(a, b) + one_way(b, a))


def line(c="-", n=64):
    print(c * n)


# ------------------------------------------------- the hidden target
HIDDEN = (2.0, 7.0, 6.0, 8.0)
target = coupler_curve(*HIDDEN)
line("=")
print("DESIGN BRIEF: draw this curve. (48 points. Nothing else given.)")
line("=")
xs = [p[0] for p in target]; ys = [p[1] for p in target]
print(f"target curve bbox: x [{min(xs):.2f},{max(xs):.2f}]  "
      f"y [{min(ys):.2f},{max(ys):.2f}]\n")

# ------------------------------------------------- stage 1: explore
print("stage 1 -- random exploration over length space")
best, best_err = None, float("inf")
tried = rejected = 0
for _ in range(400):
    cand = tuple(round(random.uniform(1.0, 10.0), 2) for _ in range(4))
    tried += 1
    if not grashof_crank_rocker(*cand):
        rejected += 1
        continue                      # free rejection: no simulation spent
    curve = coupler_curve(*cand, steps=24)
    if curve is None:
        rejected += 1
        continue
    err = chamfer(curve, target)
    if err < best_err:
        best_err, best = err, cand
print(f"  {tried} proposals, {rejected} rejected before simulation "
      f"(Grashof / closure screen)")
print(f"  best so far: lengths {best}, chamfer error {best_err:.3f}")

# ------------------------------------------------- stage 2: refine
print("\nstage 2 -- coordinate refinement (perceive, compare, nudge)")
cur, cur_err = list(best), best_err
step = 0.4
while step > 0.01:
    improved = False
    for i in range(4):
        for delta in (+step, -step):
            cand = cur[:]
            cand[i] = round(cand[i] + delta, 4)
            if cand[i] <= 0.2 or not grashof_crank_rocker(*cand):
                continue
            curve = coupler_curve(*cand, steps=32)
            if curve is None:
                continue
            err = chamfer(curve, target)
            if err < cur_err:
                cur, cur_err = cand, err
                improved = True
    if not improved:
        step *= 0.5
print(f"  refined: lengths {tuple(round(v,3) for v in cur)}, "
      f"chamfer error {cur_err:.4f}")

# ------------------------------------------------- verdict
print()
line()
print("VERDICT")
line()
final = coupler_curve(*cur)
final_err = chamfer(final, target)
scalefac = max(max(xs) - min(xs), max(ys) - min(ys))
print(f"hidden mechanism : {HIDDEN}")
print(f"assembled machine: {tuple(round(v,3) for v in cur)}")
print(f"curve mismatch   : {final_err:.4f}  ({100*final_err/scalefac:.2f}% of curve size)")
assert final_err < 0.05 * scalefac, "assembly does not draw the target"
same = all(abs(a - b) < 0.15 for a, b in zip(cur, HIDDEN))
print("note: " + ("the designer rediscovered the hidden mechanism itself."
                  if same else
                  "the designer found a DIFFERENT mechanism drawing the same "
                  "curve -- a design cognate. Function, not blueprint, was "
                  "the spec, and function is what got matched."))
print()
line("=")
print("PASS: given only a curve, the system assembled a machine that draws")
print("it -- propose, screen, simulate, perceive, compare. Design is")
print("perception with the arrow reversed.")
line("=")
