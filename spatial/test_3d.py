"""
Into the third dimension
------------------------
Part 1 -- the solver is dimension-blind: the same ten-line projection loop,
          with points now 3-vectors, drops a rigid tetrahedron onto a floor.
          Distances must hold at machine precision. No code changes beyond
          "loop over coordinates".

Part 2 -- rigidity done right for 3D: rigid part = PAIRWISE-locked CLIQUE
          (connectivity is not enough -- two plates sharing an edge are
          connected but hinged). Then the taxonomy gift:

              clique overlap 3+  ->  WELD   (one body)
              clique overlap 2   ->  HINGE  (shared pair = the axis)
              clique overlap 1   ->  BALL   (shared point = the socket)

          Three assemblies of two tetrahedra each, moved through random
          poses. The perceiver, from trajectories alone, must name the
          joint and locate it.
"""

import math
import random
from itertools import combinations

random.seed(9)


# ------------------------------------------------------ N-D primitives
def dist(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def rodrigues(p, axis_pt, axis_dir, angle):
    """Rotate 3D point p about the line (axis_pt, axis_dir) by angle."""
    ux, uy, uz = axis_dir
    n = math.sqrt(ux * ux + uy * uy + uz * uz)
    ux, uy, uz = ux / n, uy / n, uz / n
    v = [p[i] - axis_pt[i] for i in range(3)]
    c, s = math.cos(angle), math.sin(angle)
    dotp = ux * v[0] + uy * v[1] + uz * v[2]
    cross = [uy * v[2] - uz * v[1], uz * v[0] - ux * v[2], ux * v[1] - uy * v[0]]
    return [axis_pt[i] + v[i] * c + cross[i] * s + [ux, uy, uz][i] * dotp * (1 - c)
            for i in range(3)]


def line(c="-", n=66):
    print(c * n)


# ================================================= PART 1: solver in 3D
line("=")
print("PART 1 -- same solver, third coordinate: tetrahedron drop")
line("=")
tet = [[0.0, 0.0, 3.0], [1.0, 0.0, 3.8], [0.5, 0.9, 3.5], [0.5, 0.3, 4.4]]
n = len(tet)
cons = [(i, j, dist(tet[i], tet[j])) for i in range(n) for j in range(i + 1, n)]
prev = [p[:] for p in tet]
worst = 0.0
for step in range(300):
    for k in range(n):
        vel = [(tet[k][d] - prev[k][d]) * 0.98 for d in range(3)]
        prev[k] = tet[k][:]
        tet[k] = [tet[k][0] + vel[0], tet[k][1] + vel[1],
                  tet[k][2] + vel[2] - 9.8 * 0.02 ** 2]
    for _ in range(50):
        for p in tet:
            p[2] = max(p[2], 0.0)          # floor first
        for (i, j, r) in cons:             # rigidity gets the last word
            dvec = [tet[j][d] - tet[i][d] for d in range(3)]
            d = math.sqrt(sum(x * x for x in dvec)) or 1e-12
            corr = 0.5 * (d - r) / d
            for dd in range(3):
                tet[i][dd] += corr * dvec[dd]
                tet[j][dd] -= corr * dvec[dd]
    worst = max(worst, max(abs(dist(tet[i], tet[j]) - r) for (i, j, r) in cons))
print(f"dropped, bounced, settled: worst distance drift over 300 steps = {worst:.2e}")
assert worst < 1e-6
print("-> the projection loop never knew it was in 2D. Now it's in 3D.\n")


# ============================================ PART 2: joints from cliques
def make_tet(offset):
    base = [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.5, 0.9, 0.0], [0.5, 0.3, 0.8]]
    return [[p[d] + offset[d] for d in range(3)] for p in base]


def build_assembly(joint):
    """Two tetrahedra sharing 3 / 2 / 1 vertices = weld / hinge / ball."""
    A = make_tet([0, 0, 0])
    if joint == "weld":
        shared = [0, 1, 2]
    elif joint == "hinge":
        shared = [0, 1]
    else:
        shared = [0]
    # B reuses A's shared vertices, adds its own for the rest
    B_extra = [[A[0][0] - 0.2 - 0.7 * k, A[0][1] - 0.8, A[0][2] + 0.5 + 0.3 * k]
               for k in range(4 - len(shared))]
    pts = [p[:] for p in A] + [p[:] for p in B_extra]
    body_A = list(range(4))
    body_B = shared + list(range(4, 4 + len(B_extra)))
    return pts, body_A, body_B, shared


def animate(pts, body_B, shared, joint, frames_n=160):
    """Move body B through random legal poses about the shared geometry."""
    frames = []
    cur = [p[:] for p in pts]
    for _ in range(frames_n):
        if joint == "weld":
            pass                                   # nothing legal to move
        elif joint == "hinge":
            axis_pt = cur[shared[0]]
            axis_dir = [cur[shared[1]][d] - cur[shared[0]][d] for d in range(3)]
            ang = random.uniform(-0.3, 0.3)
            for i in body_B:
                if i in shared:
                    continue
                cur[i] = rodrigues(cur[i], axis_pt, axis_dir, ang)
        else:                                      # ball: random axis each frame
            axis_pt = cur[shared[0]]
            axis_dir = [random.gauss(0, 1) for _ in range(3)]
            ang = random.uniform(-0.3, 0.3)
            for i in body_B:
                if i in shared:
                    continue
                cur[i] = rodrigues(cur[i], axis_pt, axis_dir, ang)
        frames.append([p[:] for p in cur])
    return frames


def perceive_joints(frames):
    """Trajectories in, joint verdict out. No other inputs."""
    n = len(frames[0])
    # 1. locked-pair ledger
    locked = set()
    scale = 0.0
    for (i, j) in combinations(range(n), 2):
        ds = [dist(f[i], f[j]) for f in frames]
        mean = sum(ds) / len(ds)
        scale = max(scale, mean)
        std = math.sqrt(sum((d - mean) ** 2 for d in ds) / len(ds))
        if std < 1e-6 * max(mean, 1e-9) or std < 1e-9:
            locked.add((i, j))
    # 2. rigid parts = maximal PAIRWISE-locked cliques (greedy growth)
    cliques = []
    for seed in range(n):
        c = {seed}
        for cand in range(n):
            if cand in c:
                continue
            if all((min(cand, m), max(cand, m)) in locked for m in c):
                c.add(cand)
        if len(c) >= 3 and not any(c <= q for q in cliques):
            cliques = [q for q in cliques if not q <= c] + [c]
    # 3. joint taxonomy from clique overlap
    verdicts = []
    for a, b in combinations(range(len(cliques)), 2):
        ov = cliques[a] & cliques[b]
        kind = {0: "separate", 1: "BALL", 2: "HINGE"}.get(len(ov), "WELD")
        verdicts.append((sorted(cliques[a]), sorted(cliques[b]), sorted(ov), kind))
    if len(cliques) == 1:
        verdicts.append((sorted(cliques[0]), None, None, "WELD (single body)"))
    return cliques, verdicts


line("=")
print("PART 2 -- joint taxonomy from clique overlap (perceiver, 3D)")
line("=")
expected = {"weld": "WELD", "hinge": "HINGE", "ball": "BALL"}
for joint in ["weld", "hinge", "ball"]:
    pts, bA, bB, shared = build_assembly(joint)
    frames = animate(pts, bB, shared, joint)
    cliques, verdicts = perceive_joints(frames)
    print(f"\n--- assembly built with a {joint.upper()} ({len(shared)} shared pts) ---")
    print(f"  rigid cliques found: {[sorted(c) for c in cliques]}")
    for (ca, cb, ov, kind) in verdicts:
        if cb is None:
            print(f"  verdict: {kind}")
        else:
            print(f"  cliques {ca} + {cb} overlap {ov} -> {kind}")
    top = verdicts[0][3]
    assert expected[joint] in top, f"{joint} misread as {top}"
    if joint == "hinge":
        ov = verdicts[0][2]
        assert set(ov) == set(shared), "hinge axis mislocated"
        print(f"  hinge AXIS located: the shared pair {ov}")
    if joint == "ball":
        ov = verdicts[0][2]
        assert set(ov) == set(shared), "socket mislocated"
        print(f"  ball SOCKET located: shared point {ov}")

print()
line("=")
print("PASS: solver dimension-blind at machine precision; rigid parts as")
print("pairwise-locked cliques; WELD / HINGE / BALL read off, with the axis")
print("and socket located, purely from set intersection of cliques.")
line("=")
