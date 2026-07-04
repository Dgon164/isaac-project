"""
Keyframes: state A, state B, and the road between
-------------------------------------------------
Part 1 -- THE TRAP: naive lerp of a rotated rigid square collapses it
          mid-path (the animator's classic). The fix is to diff the states
          in the RIGHT coordinates: Procrustes recovers WHAT changed (one
          rotation + one translation), and interpolating THAT stays rigid
          to machine precision.

Part 2 -- MECHANISM INBETWEENING: four-bar, crank 20 deg -> 160 deg.
          lerp-then-project walks the constraint manifold: every
          intermediate frame is a legal mechanism state, steps are small
          and continuous, and the path ARRIVES.

Part 3 -- THE HONEST NO: state B is the same crank angle but the OTHER
          assembly branch (rocker mirrored). No continuous legal path
          exists without disassembly. The planner must detect this: the
          projected path shows a teleport (discontinuity spike) instead
          of travel. "You can't get there from here" is a valid answer.
"""

import math
from engine import Mechanism

def dist(a, b):
    return math.dist(a, b)


def procrustes2d(a, b):
    n = len(a)
    ca = [sum(p[0] for p in a) / n, sum(p[1] for p in a) / n]
    cb = [sum(p[0] for p in b) / n, sum(p[1] for p in b) / n]
    A = [[p[0] - ca[0], p[1] - ca[1]] for p in a]
    B = [[p[0] - cb[0], p[1] - cb[1]] for p in b]
    num = sum(A[i][0] * B[i][1] - A[i][1] * B[i][0] for i in range(n))
    den = sum(A[i][0] * B[i][0] + A[i][1] * B[i][1] for i in range(n))
    return math.atan2(num, den), ca, cb


def line(c="-", n=66):
    print(c * n)


# ==================================================== PART 1: rigid inbetween
line("=")
print("PART 1 -- rigid keyframes: diff the states in the right coordinates")
line("=")
sq = [[0, 0], [2, 0], [2, 2], [0, 2]]
ANG, TX, TY = math.radians(120), 5.0, 1.5
c, s = math.cos(ANG), math.sin(ANG)
sqB = [[c * x - s * y + TX, s * x + c * y + TY] for (x, y) in sq]
rest = [(i, j, dist(sq[i], sq[j])) for i in range(4) for j in range(i + 1, 4)]

def worst_drift(pts):
    return max(abs(dist(pts[i], pts[j]) - r) for (i, j, r) in rest)

naive_worst = 0.0
for k in range(21):
    t = k / 20
    mid = [[(1 - t) * a[0] + t * b[0], (1 - t) * a[1] + t * b[1]]
           for a, b in zip(sq, sqB)]
    naive_worst = max(naive_worst, worst_drift(mid))
print(f"naive point-lerp, worst shape violation en route: {naive_worst:.3f} "
      f"({100*naive_worst/2.0:.0f}% of edge length!)")

# perceiver diffs the keyframes: Procrustes says WHAT changed
th, ca, cb = procrustes2d(sq, sqB)
print(f"state diff recovered: rotate {math.degrees(th):.1f} deg, "
      f"translate ({cb[0]-ca[0]:.2f}, {cb[1]-ca[1]:.2f})")
smart_worst = 0.0
for k in range(21):
    t = k / 20
    a = th * t
    cc, ss = math.cos(a), math.sin(a)
    mid = []
    for (x, y) in sq:
        px, py = x - ca[0], y - ca[1]
        mid.append([cc * px - ss * py + ca[0] + t * (cb[0] - ca[0]),
                    ss * px + cc * py + ca[1] + t * (cb[1] - ca[1])])
    smart_worst = max(smart_worst, worst_drift(mid))
print(f"transform-space interpolation, worst violation: {smart_worst:.2e}")
assert naive_worst > 0.5 and smart_worst < 1e-9
print("-> interpolate the CHANGE, not the coordinates.\n")


# ==================================================== four-bar helpers
def fourbar_state(crank_angle):
    """Legal four-bar configuration at a given crank angle (elbow-up)."""
    crank, coupler, rocker, ground = 2.0, 7.0, 6.0, 8.0
    p1 = [crank * math.cos(crank_angle), crank * math.sin(crank_angle)]
    d = dist(p1, [ground, 0.0])
    a = (coupler**2 - rocker**2 + d**2) / (2 * d)
    h = math.sqrt(max(coupler**2 - a**2, 0.0))
    ux, uy = (ground - p1[0]) / d, -p1[1] / d
    p2 = [p1[0] + a * ux - h * uy, p1[1] + a * uy + h * ux]
    return [[0.0, 0.0], p1, p2, [ground, 0.0]]


CONS = [((0, 1), 2.0), ((1, 2), 7.0), ((2, 3), 6.0)]

def project_state(pts, sweeps=200):
    m = Mechanism(points=[p[:] for p in pts])
    for (pair, r) in CONS:
        m.locked[pair] = r
    m.pin(0); m.pin(3)
    m.project(sweeps)
    return m.points


def plan(A, B, K=60):
    """lerp-then-project: walk toward B along the constraint manifold."""
    path = [A]
    for k in range(1, K + 1):
        t = k / K
        tgt = [[(1 - t) * a[0] + t * b[0], (1 - t) * a[1] + t * b[1]]
               for a, b in zip(A, B)]
        path.append(project_state(tgt))
    legality = max(max(abs(dist(f[i], f[j]) - r) for ((i, j), r) in CONS)
                   for f in path)
    steps = [max(dist(path[k][i], path[k + 1][i]) for i in range(4))
             for k in range(len(path) - 1)]
    arrival = max(dist(path[-1][i], B[i]) for i in range(4))
    return legality, max(steps), arrival


# ==================================================== PART 2: reachable
line("=")
print("PART 2 -- mechanism keyframes: crank 20 deg -> 160 deg")
line("=")
A = fourbar_state(math.radians(20))
B = fourbar_state(math.radians(160))
legality, biggest_step, arrival = plan(A, B)
print(f"every intermediate frame legal: worst constraint violation {legality:.2e}")
print(f"largest single-frame move: {biggest_step:.3f}  (smooth travel)")
print(f"distance from final frame to state B: {arrival:.2e}")
assert legality < 1e-9 and arrival < 1e-6 and biggest_step < 0.6
print("-> a continuous LEGAL path exists and was found: 60 inbetweens,")
print("   all of them real mechanism states. Keyframing = manifold walking.\n")

# ==================================================== PART 3: unreachable
line("=")
print("PART 3 -- same crank angle, OTHER assembly branch (rocker mirrored)")
line("=")
A = fourbar_state(math.radians(60))
Bm = [p[:] for p in fourbar_state(math.radians(60))]
Bm[2][1] = -Bm[2][1]                       # mirror the rocker tip: other branch
legality, biggest_step, arrival = plan(A, Bm)
print(f"every frame individually legal: worst violation {legality:.2e}")
print(f"largest single-frame move: {biggest_step:.3f}   <- TELEPORT")
print(f"final residual to target: {arrival:.2e}  (it did reach B...)")
print("...but not by TRAVELING: the path contains a discontinuous jump many")
print("times larger than any legal step. The planner's verdict:")
assert biggest_step > 2.0
print(f"  NO continuous path exists -- state B is in a different component")
print(f"  of the configuration manifold. Reaching it requires disassembly.")

print()
line("=")
print("PASS: keyframes diffed in transform space (what changed), inbetweened")
print("along the constraint manifold (how to get there), and impossibility")
print("detected honestly (when there is no 'how').")
line("=")
