"""
States of matter as invariance signatures
-----------------------------------------
Three 5x5 particle blobs dropped into the same box, same integrator,
differing ONLY in constraint type:

  RIGID : all pairwise distances locked (projected hard)
  SOFT  : neighbor distances sprung (projected at low stiffness -> breathe
          and revert)
  LIQUID: no pair constraints at all; only non-overlap (min distance)
          + container walls + gravity

The perceiver receives trajectories only and must classify each material
using two ledgers:
  1. neighbor permanence  -- are your first neighbors still your neighbors?
  2. distance character   -- locked / sprung(mean-reverting) / free
  plus one aggregate invariant:
  3. local density        -- mean nearest-neighbor spacing (incompressibility)
"""

import math
import random

random.seed(3)

DT = 0.05
GRAV = -9.8
FLOOR, XMIN, XMAX = 0.0, 0.0, 14.0
STEPS = 500
REST = 0.5           # lattice spacing


def make_blob(cx, cy, n=5):
    pts = []
    for r in range(n):
        for c in range(n):
            pts.append([cx + c * REST, cy + r * REST])
    return pts


def neighbor_pairs(pts, cutoff=REST * 1.5):
    prs = []
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            if math.dist(pts[i], pts[j]) < cutoff:
                prs.append((i, j, math.dist(pts[i], pts[j])))
    return prs


def simulate(kind):
    pts = make_blob({"rigid": 1.0, "soft": 5.5, "liquid": 10.0}[kind], 2.5)
    n = len(pts)
    prev = [p[:] for p in pts]
    if kind == "rigid":
        cons = [(i, j, math.dist(pts[i], pts[j]))
                for i in range(n) for j in range(i + 1, n)]
        stiff = 1.0
    elif kind == "soft":
        cons = neighbor_pairs(pts, REST * 1.9)   # neighbors + diagonals
        stiff = 0.22                             # weak springs: breathe
    else:
        cons = []                                # liquid: no structure at all
        stiff = 0.0
    frames = []
    for step in range(STEPS):
        g = GRAV if step < 280 else 0.0     # load, settle... then RELEASE
        # verlet
        for k in range(n):
            vx = pts[k][0] - prev[k][0]
            vy = pts[k][1] - prev[k][1]
            prev[k] = pts[k][:]
            pts[k][0] += vx * 0.99
            pts[k][1] += vy * 0.99 + g * DT * DT
        # constraints
        for _ in range(6):
            for (i, j, rest) in cons:
                dx = pts[j][0] - pts[i][0]
                dy = pts[j][1] - pts[i][1]
                d = math.hypot(dx, dy) or 1e-12
                corr = stiff * 0.5 * (d - rest) / d
                pts[i][0] += corr * dx; pts[i][1] += corr * dy
                pts[j][0] -= corr * dx; pts[j][1] -= corr * dy
            # non-overlap for everyone (liquid's ONLY internal rule)
            for i in range(n):
                for j in range(i + 1, n):
                    dx = pts[j][0] - pts[i][0]
                    dy = pts[j][1] - pts[i][1]
                    d = math.hypot(dx, dy)
                    if d < REST * 0.9 and d > 1e-12:
                        corr = 0.5 * (REST * 0.9 - d) / d
                        pts[i][0] -= corr * dx; pts[i][1] -= corr * dy
                        pts[j][0] += corr * dx; pts[j][1] += corr * dy
            # container
            for p in pts:
                p[1] = max(p[1], FLOOR)
                p[0] = min(max(p[0], XMIN), XMAX)
        frames.append([p[:] for p in pts])
    return frames


# ------------------------------------------------------------- perceiver
def knn(frame, i, k=4):
    ds = sorted(range(len(frame)), key=lambda j: math.dist(frame[i], frame[j]))
    return set(ds[1:k + 1])


def classify(frames):
    n = len(frames[0])
    # judge over the WHOLE trajectory -- material shows itself under load
    # (a soft body at rest is indistinguishable from a rigid one)
    t0, t1 = frames[0], frames[-1]

    # 1. neighbor permanence: first-neighbors at start still there at end?
    keep = sum(len(knn(t0, i) & knn(t1, i)) / 4.0 for i in range(n)) / n

    # 2. distance character on initially-neighboring pairs, across the drop
    pairs = [(i, j) for i in range(n) for j in list(knn(t0, i)) if j > i]
    rels, drifts = [], []
    for (i, j) in pairs:
        ds = [math.dist(f[i], f[j]) for f in frames]
        mean = sum(ds) / len(ds)
        std = math.sqrt(sum((d - mean) ** 2 for d in ds) / len(ds))
        rels.append(std / mean)
        # drift = post-release rest length vs the PRISTINE unloaded length
        # (frame 0, before any load). Elastic returns; plastic stays moved.
        drifts.append(abs(sum(ds[-40:]) / 40 - ds[0]) / mean)
    rel = sum(rels) / len(rels)
    drift = sum(drifts) / len(drifts)

    # 3. incompressibility: nearest-neighbor spacing stable once settled
    def spacing(f):
        return sum(min(math.dist(f[i], f[j]) for j in range(n) if j != i)
                   for i in range(n)) / n
    mid, end = frames[STEPS // 2], frames[-1]
    dens_change = abs(spacing(end) - spacing(mid)) / spacing(mid)

    if keep > 0.85 and rel < 0.005:
        verdict = "RIGID"
    elif keep > 0.85:
        verdict = "SOFT (elastic)" if drift < rel else "PLASTIC"
    else:
        verdict = "FLUID (incompressible)" if dens_change < 0.15 else "GAS-like"
    return keep, rel, drift, dens_change, verdict


def line(c="-", n=66):
    print(c * n)


line("=")
print("THREE BLOBS, ONE DROP TEST -- perceiver sees trajectories only")
line("=")
print(f"{'material':8} {'nbr-keep':>9} {'dist std/mean':>14} "
      f"{'mean drift':>11} {'density chg':>12}   verdict")
line()
expected = {"rigid": "RIGID", "soft": "SOFT (elastic)", "liquid": "FLUID (incompressible)"}
for kind in ["rigid", "soft", "liquid"]:
    frames = simulate(kind)
    keep, rel, drift, dens, verdict = classify(frames)
    print(f"{kind:8} {keep:9.2f} {rel:14.4f} {drift:11.4f} {dens:12.3f}   {verdict}")
    assert verdict == expected[kind], f"{kind} misclassified as {verdict}"

# extra observations worth printing: the liquid takes the container's shape
frames = simulate("liquid")
final = frames[-1]
ys = sorted(p[1] for p in final)
surface_spread = ys[-1] - ys[-6]     # how level is the top?
print()
print(f"liquid free surface: top-5 particle heights within {surface_spread:.2f} units")
print("-> it found its own level. Nobody told it to; no pair constraint exists.")
print()
line("=")
print("PASS: rigid, soft, and fluid distinguished by which invariants held:")
print("  RIGID  = neighbors permanent + distances locked")
print("  SOFT   = neighbors permanent + distances breathe and revert")
print("  FLUID  = neighbors churn     + local density conserved")
line("=")
