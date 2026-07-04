"""
Maps, archetypes, and the hidden center
---------------------------------------
Part 1 -- MAP + EGO-MOTION: an agent wanders a room seeing landmarks only
          in its OWN frame (rotated, translated, every frame different).
          The perceiver must discover: the scene is one rigid clique, the
          coherent motion is therefore SELF-motion, and recover both the
          map and its own trajectory. (SLAM's soul, ledger-style.)

Part 2 -- CUBE: a tumbling cube's distance spectrum quantizes into exactly
          3 tiers (1 : sqrt2 : sqrt3). Tier-1 adjacency yields the role
          vocabulary: corner (degree 3), edge (12), face (4-cycles, 6) --
          and Euler's V - E + F = 2 as a checksum on the observation.

Part 3 -- SPHERE: points on a tumbling globe. Fit the invisible center,
          find every point equidistant -> "lies on a sphere". Distinguish
          from the cube (whose corners ALSO lie on a sphere) by spectrum
          character: discrete tiers = polyhedron, continuum = smooth.
"""

import math
import random
from itertools import combinations

random.seed(4)


def dist(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def procrustes2d(a, b):
    """Optimal rotation+translation mapping a->b; returns (theta, tx, ty, rms)."""
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
    return th, ca, cb, math.sqrt(r2 / n)


def line(c="-", n=66):
    print(c * n)


# =============================================== PART 1: MAP + EGO-MOTION
line("=")
print("PART 1 -- the room is a rigid clique; therefore I am the one moving")
line("=")
LANDMARKS = [[random.uniform(0, 12), random.uniform(0, 9)] for _ in range(12)]
poses = []
x, y, th = 6.0, 4.0, 0.0
frames = []
for t in range(140):
    th += random.uniform(-0.25, 0.25)
    x = min(max(x + random.uniform(-0.4, 0.4), 0), 12)
    y = min(max(y + random.uniform(-0.4, 0.4), 0), 9)
    poses.append((x, y, th))
    c, s = math.cos(-th), math.sin(-th)
    obs = [[c * (L[0] - x) - s * (L[1] - y),
            s * (L[0] - x) + c * (L[1] - y)] for L in LANDMARKS]
    frames.append(obs)

# perceiver: landmark-landmark ledger
locked = 0
for (i, j) in combinations(range(12), 2):
    ds = [dist(f[i], f[j]) for f in frames]
    mean = sum(ds) / len(ds)
    std = math.sqrt(sum((d - mean) ** 2 for d in ds) / len(ds))
    if std < 1e-9:
        locked += 1
print(f"landmark pair ledger: {locked}/66 locked -> the WHOLE SCENE is one")
print("rigid clique. Everything 'out there' moves together, coherently.")

# frame-to-frame coherence: one rigid transform explains each frame
worst_fit = 0.0
recovered = []
for t in range(len(frames)):
    thr, ca, cb, rms = procrustes2d(frames[0], frames[t])
    worst_fit = max(worst_fit, rms)
    recovered.append((thr, ca, cb))
print(f"one rigid transform per frame explains ALL apparent motion "
      f"(worst residual {worst_fit:.2e})")
print("-> parsimonious verdict: the scene is still; the OBSERVER moved.")

# recover the agent's own trajectory (relative to its frame-0 pose)
err = 0.0
for t in range(len(frames)):
    # true pose of frame t expressed in frame-0 coordinates
    x0, y0, th0 = poses[0]
    xt, yt, tht = poses[t]
    c0, s0 = math.cos(-th0), math.sin(-th0)
    true_rel = (c0 * (xt - x0) - s0 * (yt - y0),
                s0 * (xt - x0) + c0 * (yt - y0))
    # perceiver's estimate: where must I be so the map fits this view?
    thr, ca, cb, _ = procrustes2d(frames[t], frames[0])
    # my position in frame-0 coords = image of my origin under the fit
    c, s = math.cos(thr), math.sin(thr)
    ex = cb[0] - (c * ca[0] - s * ca[1])
    ey = cb[1] - (s * ca[0] + c * ca[1])
    err = max(err, math.hypot(ex - true_rel[0], ey - true_rel[1]))
print(f"self-localization vs ground truth, worst error over 140 frames: {err:.2e}")
assert err < 1e-6
print("MAP + trajectory recovered. Localization = Procrustes against the map.\n")

# ====================================================== PART 2: THE CUBE
line("=")
print("PART 2 -- a tumbling cube names its own corners, edges, and faces")
line("=")
S = 2.0
cube = [[S * a, S * b, S * c] for a in (0, 1) for b in (0, 1) for c in (0, 1)]
ctr = [S / 2] * 3


def rodrigues(p, o, u, ang):
    n = math.sqrt(sum(x * x for x in u)); u = [x / n for x in u]
    v = [p[i] - o[i] for i in range(3)]
    c, s = math.cos(ang), math.sin(ang)
    d = sum(u[i] * v[i] for i in range(3))
    cr = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
    return [o[i] + v[i] * c + cr[i] * s + u[i] * d * (1 - c) for i in range(3)]


cframes = []
pts = [p[:] for p in cube]
for _ in range(80):
    axis = [random.gauss(0, 1) for _ in range(3)]
    ang = random.uniform(-0.4, 0.4)
    pts = [rodrigues(p, ctr, axis, ang) for p in pts]
    cframes.append([p[:] for p in pts])

# distance spectrum (means over frames; all locked since rigid)
pair_d = {(i, j): sum(dist(f[i], f[j]) for f in cframes) / len(cframes)
          for (i, j) in combinations(range(8), 2)}
vals = sorted(pair_d.values())
# cluster into tiers: split where the gap is large
tiers, cur = [], [vals[0]]
for v in vals[1:]:
    if v - cur[-1] > 0.2:
        tiers.append(cur); cur = [v]
    else:
        cur.append(v)
tiers.append(cur)
tier_means = [sum(t) / len(t) for t in tiers]
print(f"distance spectrum: {len(pair_d)} pairs -> {len(tiers)} tiers")
for k, (t, m) in enumerate(zip(tiers, tier_means)):
    print(f"  tier {k}: {len(t):2d} pairs at {m:.4f}  (ratio {m/tier_means[0]:.4f})")
assert len(tiers) == 3
assert abs(tier_means[1] / tier_means[0] - math.sqrt(2)) < 0.01
assert abs(tier_means[2] / tier_means[0] - math.sqrt(3)) < 0.01
print("  ratios 1 : sqrt2 : sqrt3 -> this object is a CUBE archetype")

adj = {i: set() for i in range(8)}
edges = []
for (i, j), d in pair_d.items():
    if abs(d - tier_means[0]) < 0.1:
        adj[i].add(j); adj[j].add(i); edges.append((i, j))
degs = sorted(len(a) for a in adj.values())
faces = 0
for quad in combinations(range(8), 4):
    sub = [(a, b) for (a, b) in combinations(quad, 2) if b in adj[a]]
    if len(sub) == 4 and all(sum(1 for (a, b) in sub if v in (a, b)) == 2 for v in quad):
        faces += 1
V, E, F = 8, len(edges), faces
print(f"  roles: {V} CORNERS (each degree {degs[0]}), {E} EDGES, {F} FACES")
print(f"  Euler checksum: V - E + F = {V - E + F}")
assert degs == [3] * 8 and E == 12 and F == 6 and V - E + F == 2
print("  corner/edge/face vocabulary emerged from spectrum tiers alone.\n")

# ==================================================== PART 3: THE GLOBE
line("=")
print("PART 3 -- the globe: an invisible center, equidistant from everything")
line("=")
R = 3.0
ctr_true = [1.0, 0.5, -0.3]
sph = []
while len(sph) < 20:
    v = [random.gauss(0, 1) for _ in range(3)]
    n = math.sqrt(sum(x * x for x in v))
    sph.append([R * x / n + ctr_true[k] for k, x in enumerate(v)])
sframes = []
pts = [p[:] for p in sph]
for _ in range(60):
    axis = [random.gauss(0, 1) for _ in range(3)]
    pts = [rodrigues(p, ctr_true, axis, random.uniform(-0.3, 0.3)) for p in pts]
    sframes.append([p[:] for p in pts])

# hidden-center fit: minimize variance of center-distances (gradient descent)
c_est = [sum(p[d] for p in sframes[0]) / 20 for d in range(3)]
for it in range(20000):
    ds = [dist(p, c_est) for p in sframes[0]]
    mean_d = sum(ds) / len(ds)
    grad = [0.0, 0.0, 0.0]
    for p, dd in zip(sframes[0], ds):
        w = (dd - mean_d) / (dd or 1e-12)
        for k in range(3):
            grad[k] += w * (c_est[k] - p[k])
    step = 0.02 if it < 10000 else 0.002
    for k in range(3):
        c_est[k] -= step * grad[k]
ds = [dist(p, c_est) for p in sframes[0]]
mean_r = sum(ds) / len(ds)
spread = math.sqrt(sum((d - mean_r) ** 2 for d in ds) / len(ds))
print(f"fitted hidden center: ({c_est[0]:.3f}, {c_est[1]:.3f}, {c_est[2]:.3f})"
      f"   truth ({ctr_true[0]:.1f}, {ctr_true[1]:.1f}, {ctr_true[2]:.1f})")
print(f"distance to center: {mean_r:.4f} +/- {spread:.2e}   (truth R = {R})")
assert dist(c_est, ctr_true) < 0.05 and abs(mean_r - R) < 0.05

# discriminator: spectrum character (cube corners are ALSO on a sphere!)
svals = sorted(dist(sframes[0][i], sframes[0][j])
               for (i, j) in combinations(range(20), 2))
gaps = [svals[k + 1] - svals[k] for k in range(len(svals) - 1)]
biggest_gap = max(gaps) / (svals[-1] - svals[0])
cube_gap = max(tiers[1][0] - tiers[0][-1], tiers[2][0] - tiers[1][-1]) / \
           (tier_means[2] - tier_means[0])
print(f"spectrum character -- largest normalized gap:")
print(f"  sphere sample: {biggest_gap:.3f}   cube: {cube_gap:.3f}")
assert cube_gap > 3 * biggest_gap
print("  discrete tiers = POLYHEDRON (crystalline); continuum = SMOOTH surface")

print()
line("=")
print("PASS: the room precipitated as a map and self-motion was inferred;")
print("the cube named its corners, edges, faces and passed Euler's checksum;")
print("the globe surrendered its invisible center and its smoothness.")
line("=")
