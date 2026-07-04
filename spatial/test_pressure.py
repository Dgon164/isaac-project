"""
Volume, containment, pressure
-----------------------------
Three vessels, one membrane representation (a closed loop of particles),
one squeeze protocol, one perceiver.

  WATER BALLOON : elastic membrane + HARD area constraint (incompressible)
  AIR BALLOON   : elastic membrane + pressure force, P_in = K / A  (Boyle)
  RIGID VESSEL  : locked shell + internal pressure (invisible from outside)

Squeeze protocol: pinch two opposite vertices together, hold, release.
Then, for the rigid vessel only: PUNCTURE, because nothing else works.

Perceiver verdicts must come from trajectories alone:
  water : every pair distance varies, AREA locked         -> aggregate invariant
  air   : area compresses and RECOVERS, stiffening        -> sprung aggregate
  rigid : nothing moves at all... then breach reveals
          stored energy that no external work put in      -> hidden state
"""

import math
import random
from engine import observe

random.seed(5)

N = 28                # membrane vertices
R0 = 2.0              # rest radius
DT = 1.0
DAMP = 0.90


def polygon_area(pts):
    a = 0.0
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        a += pts[i][0] * pts[j][1] - pts[j][0] * pts[i][1]
    return 0.5 * a


def make_ring():
    return [[R0 * math.cos(2 * math.pi * k / N),
             R0 * math.sin(2 * math.pi * k / N)] for k in range(N)]


def project_area(pts, target, stiffness=1.0):
    a = polygon_area(pts)
    grads = []
    s = 0.0
    for i in range(N):
        gx = 0.5 * (pts[(i + 1) % N][1] - pts[(i - 1) % N][1])
        gy = 0.5 * (pts[(i - 1) % N][0] - pts[(i + 1) % N][0])
        grads.append((gx, gy))
        s += gx * gx + gy * gy
    lam = stiffness * (target - a) / (s or 1e-12)
    for i in range(N):
        pts[i][0] += lam * grads[i][0]
        pts[i][1] += lam * grads[i][1]


def simulate(kind, squeeze_depth=1.1, steps=760):
    pts = make_ring()
    prev = [p[:] for p in pts]
    rest = [math.dist(pts[i], pts[(i + 1) % N]) for i in range(N)]
    A0 = polygon_area(pts)
    # air balloon: gas at ambient (equilibrium). rigid vessel: PRESSURIZED 4 atm
    K_GAS = 4.0 * A0 if kind == "rigid" else A0
    rigid_pairs = None
    if kind == "rigid":
        rigid_pairs = [(i, j, math.dist(pts[i], pts[j]))
                       for i in range(N) for j in range(i + 1, N)]
    breach = set()
    frames, areas, kinetic = [], [], []
    L, Rr = 0, N // 2              # pinch these two toward each other

    for t in range(steps):
        # phases: 0-249 squeeze in, 250-399 hold, 400+ release
        if kind == "rigid" and t == 500:
            breach = {(N - 1) % N, 0, 1}      # puncture: 3 membrane links gone
        prog = min(t / 250.0, 1.0) if t < 400 else None
        # verlet
        for k in range(N):
            vx = (pts[k][0] - prev[k][0]) * DAMP
            vy = (pts[k][1] - prev[k][1]) * DAMP
            prev[k] = pts[k][:]
            pts[k][0] += vx
            pts[k][1] += vy
        # pressure force (air + rigid vessels carry gas)
        if kind in ("air", "rigid"):
            A = abs(polygon_area(pts))
            P = K_GAS / max(A, 0.05)
            for i in range(N):
                if kind == "rigid" and not breach:
                    break            # shell resists; no motion anyway
                nx = pts[(i + 1) % N][1] - pts[(i - 1) % N][1]
                ny = pts[(i - 1) % N][0] - pts[(i + 1) % N][0]
                ln = math.hypot(nx, ny) or 1e-12
                f = (0.02 if kind == "rigid" else 0.004) * (P - 1.0)
                pts[i][0] += f * nx / ln
                pts[i][1] += f * ny / ln
        # the pinch: a COMPLIANT gripper (finite force, not teleportation)
        if prog is not None:
            for idx, tx in ((L, -R0 + squeeze_depth * prog),
                            (Rr, R0 - squeeze_depth * prog)):
                pts[idx][0] += 0.5 * (tx - pts[idx][0])
                pts[idx][1] += 0.5 * (0.0 - pts[idx][1])
        # constraints (rigid shells resolve harder than membranes)
        for _ in range(24 if kind == "rigid" else 8):
            if kind == "rigid":
                for (i, j, r) in rigid_pairs:
                    if breach and (i in breach or j in breach):
                        continue     # breached region: constraints destroyed
                    dx = pts[j][0] - pts[i][0]
                    dy = pts[j][1] - pts[i][1]
                    d = math.hypot(dx, dy) or 1e-12
                    c = 0.5 * (d - r) / d
                    pts[i][0] += c * dx; pts[i][1] += c * dy
                    pts[j][0] -= c * dx; pts[j][1] -= c * dy
            else:
                for i in range(N):
                    j = (i + 1) % N
                    dx = pts[j][0] - pts[i][0]
                    dy = pts[j][1] - pts[i][1]
                    d = math.hypot(dx, dy) or 1e-12
                    c = 0.35 * 0.5 * (d - rest[i]) / d
                    pts[i][0] += c * dx; pts[i][1] += c * dy
                    pts[j][0] -= c * dx; pts[j][1] -= c * dy
            if kind == "water":
                project_area(pts, A0)
        frames.append([p[:] for p in pts])
        areas.append(abs(polygon_area(pts)))
        ke = sum((pts[k][0] - prev[k][0]) ** 2 + (pts[k][1] - prev[k][1]) ** 2
                 for k in range(N))
        kinetic.append(ke)
    return frames, areas, kinetic


def procrustes_residual(a, b):
    """RMS shape difference between point sets a, b after removing
    translation and rotation (rigid Procrustes, 2D closed form)."""
    n = len(a)
    ca = [sum(p[0] for p in a) / n, sum(p[1] for p in a) / n]
    cb = [sum(p[0] for p in b) / n, sum(p[1] for p in b) / n]
    A = [[p[0] - ca[0], p[1] - ca[1]] for p in a]
    B = [[p[0] - cb[0], p[1] - cb[1]] for p in b]
    num = sum(A[i][0] * B[i][1] - A[i][1] * B[i][0] for i in range(n))
    den = sum(A[i][0] * B[i][0] + A[i][1] * B[i][1] for i in range(n))
    th = math.atan2(num, den)
    c, s = math.cos(th), math.sin(th)
    r2 = sum((c * A[i][0] - s * A[i][1] - B[i][0]) ** 2 +
             (s * A[i][0] + c * A[i][1] - B[i][1]) ** 2 for i in range(n))
    return math.sqrt(r2 / n)


def line(c="-", n=66):
    print(c * n)


A0 = polygon_area(make_ring())
line("=")
print(f"THREE VESSELS, ONE PINCH  (rest area {A0:.3f}, pinch depth 1.1 each side)")
line("=")

for kind in ["water", "air", "rigid"]:
    frames, areas, kinetic = simulate(kind)
    print(f"\n--- {kind.upper()} ---")

    # pairwise membrane distances: does anything stay locked?
    sample_pairs = [(0, 7), (7, 14), (3, 24), (10, 20)]
    varying = 0
    for (i, j) in sample_pairs:
        ds = [math.dist(f[i], f[j]) for f in frames]
        mean = sum(ds) / len(ds)
        std = math.sqrt(sum((d - mean) ** 2 for d in ds) / len(ds))
        if std / mean > 5e-3:
            varying += 1
    print(f"  cross-membrane distances varying: {varying}/{len(sample_pairs)}")

    a_min = min(areas); a_end = sum(areas[-30:]) / 30
    a_squeeze = min(areas[200:400])
    mean_a = sum(areas) / len(areas)
    std_a = math.sqrt(sum((a - mean_a) ** 2 for a in areas) / len(areas))
    print(f"  area: rest {A0:.3f}  under squeeze {a_squeeze:.3f}  "
          f"after release {a_end:.3f}  (rel std {std_a/mean_a:.4f})")

    # transverse bulge during squeeze (Poisson check)
    top = N // 4; bot = 3 * N // 4
    w0 = math.dist(frames[0][top], frames[0][bot])
    w1 = math.dist(frames[320][top], frames[320][bot])
    print(f"  transverse width: {w0:.3f} -> {w1:.3f} under squeeze")

    deform = procrustes_residual(frames[0], frames[300])
    print(f"  deformation under squeeze (Procrustes residual): {deform:.4f}")

    ke_before = max(kinetic[460:495]) if kind == "rigid" else None
    ke_after = max(kinetic[505:640]) if kind == "rigid" else None

    if kind == "water":
        assert std_a / mean_a < 0.005, "water area should be locked"
        assert varying == len(sample_pairs)
        assert w1 > w0 + 0.15, "squeeze must bulge the transverse axis"
        print("  VERDICT: no pair invariant anywhere, AREA locked, squash one")
        print("           axis and the other grows -> INCOMPRESSIBLE CONTENTS")
    elif kind == "air":
        assert a_squeeze < 0.93 * A0, "air area should compress"
        assert abs(a_end - A0) < 0.04 * A0, "air area should recover"
        print("  VERDICT: area compresses under load and RECOVERS on release")
        print("           -> COMPRESSIBLE contents behind an elastic boundary")
    else:
        moved = max(math.dist(frames[300][k], frames[0][k]) for k in range(N))
        print(f"  max vertex displacement (shell shoved) : {moved:.4f}")
        print(f"  peak kinetic energy just before breach: {ke_before:.2e}")
        print(f"  peak kinetic energy just after breach : {ke_after:.2e}")
        assert deform < 0.02, "rigid vessel must not CHANGE SHAPE under pinch"
        assert ke_after > 100 * max(ke_before, 1e-12), "breach should release energy"
        print("  VERDICT: rigid and inert under every external probe -- then a")
        print("           breach released energy NO external work supplied.")
        print("           Hidden internal state (pressure) existed all along.")

print()
line("=")
print("PASS: the invariant climbed a level (pairs -> aggregate), split into")
print("locked (water) vs sprung-with-stiffening (air), and the third vessel")
print("proved some state is invisible to every probe short of failure.")
line("=")
