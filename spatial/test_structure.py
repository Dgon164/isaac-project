"""
The loop, end to end:
  1. Build mechanisms from locked distances only (four-bar, door).
  2. Run them with constraint projection (the physics is 10 lines).
  3. Hand ONLY the point trajectories to the perceiver.
  4. Perceiver recovers: locked edges, rigid parts, joints, DOF.
  5. Cross-check observed DOF against Gruebler's count.
"""

import math
from engine import (Mechanism, observe, detect_locked, rigid_clusters,
                    find_joints, gruebler_2d, observed_dof)


def line(char="-", n=64):
    print(char * n)


# ============================================================ FOUR-BAR
def build_fourbar():
    """Grashof crank-rocker (s + l <= p + q -> 2 + 8 <= 7 + 6), so the crank
       CAN fully rotate. Points:
       0: ground-left (pin)   1: crank tip
       2: rocker tip          3: ground-right (pin)
       Links: ground(0-3), crank(0-1) len 2, coupler(1-2) ~7, rocker(2-3) ~6."""
    m = Mechanism(points=[[0.0, 0.0], [2.0, 0.0], [6.083, 5.686], [8.0, 0.0]])
    m.lock(0, 1)   # crank
    m.lock(1, 2)   # coupler
    m.lock(2, 3)   # rocker
    m.pin(0)
    m.pin(3)
    return m


def run_fourbar():
    line("=")
    print("FOUR-BAR LINKAGE")
    line("=")
    m = build_fourbar()
    crank_len = math.dist(m.points[0], m.points[1])

    # ---- forward: drive the crank through a full revolution --------------
    frames = []
    steps = 240
    for k in range(steps):
        th = 2 * math.pi * k / steps
        m.drive(1, crank_len * math.cos(th), crank_len * math.sin(th), sweeps=80)
        frames.append([p[:] for p in m.points])

    # sanity: constraint drift after a full cycle
    worst = 0.0
    for (i, j), rest in m.locked.items():
        for f in frames:
            worst = max(worst, abs(math.dist(f[i], f[j]) - rest))
    print(f"forward sim: {steps} frames, worst constraint drift = {worst:.2e}")

    # coupler curve: the midpoint of link 1-2 traces the signature curve
    cx = [ (f[1][0]+f[2][0])/2 for f in frames ]
    cy = [ (f[1][1]+f[2][1])/2 for f in frames ]
    print(f"coupler-curve bounding box: x [{min(cx):.2f},{max(cx):.2f}] "
          f"y [{min(cy):.2f},{max(cy):.2f}]  (a point would be a bug)")

    # ---- inverse: perceiver sees ONLY the trajectories -------------------
    line()
    print("PERCEIVER (input: point positions per frame, nothing else)")
    ledgers = observe(frames)
    scale = max(led.mean for led in ledgers.values())   # self-calibrated scale
    print(f"self-calibrated scale = {scale:.3f}")

    print("\ndistance ledger (mean +/- std):")
    for (i, j), led in sorted(ledgers.items()):
        tag = "LOCKED" if led.std < 1e-3 * scale else "free"
        print(f"  d({i},{j}) = {led.mean:6.3f} +/- {led.std:.2e}   {tag}")

    locked = detect_locked(ledgers, scale)
    truth = set(m.locked.keys())
    found = set(locked.keys())
    print(f"\nlocked edges recovered: {sorted(found)}")
    print(f"ground truth:           {sorted(truth)}")
    extra = found - truth
    # note: ground link 0-3 is BOTH pinned, so d(0,3) never varies ->
    # the perceiver should ALSO call it locked. That's correct perception:
    # the ground IS a link.
    print(f"extra vs truth: {sorted(extra)}  "
          f"(0,3) is the ground link -- correctly perceived as rigid")
    assert truth <= found, "missed a locked edge!"

    clusters = rigid_clusters(4, locked)
    print(f"\nrigid parts precipitated: {[sorted(c) for c in clusters]}")

    # links share vertices in this representation -> count joints as shared
    # vertices between locked edges = vertices with degree >= 2
    deg = {}
    for (i, j) in locked:
        deg[i] = deg.get(i, 0) + 1
        deg[j] = deg.get(j, 0) + 1
    joints = [v for v, d in deg.items() if d >= 2]
    n_links = len(locked)          # each locked edge is a bar
    n_joints = sum(d - 1 for d in deg.values() if d >= 2)
    print(f"bars (links) = {n_links}, revolute joints = {n_joints}")

    dof = gruebler_2d(n_links, n_joints)
    print(f"Gruebler predicts DOF = {dof}")

    # observed DOF: bar angles should all be functions of one parameter
    bar_clusters = [set(e) for e in locked if e != (0, 3)]
    obs = observed_dof(frames, [set((0, 3))] + bar_clusters, ref_cluster=0)
    print(f"observed DOF from motion = {obs}")
    assert dof == 1 and obs == 1, "DOF mismatch!"
    print("\nPASS: shape -> structure -> mechanism, checksum agrees.")
    return frames


# ============================================================ DOOR
def build_door():
    """A door: rigid rectangle (4 pts, cross-braced) hinged at one edge.
       Points 0,1 = hinge edge (pinned), 2,3 = swinging edge."""
    m = Mechanism(points=[[0.0, 0.0], [0.0, 3.0], [2.0, 3.0], [2.0, 0.0]])
    # rigid panel: perimeter + one diagonal brace = rigid in 2D
    for a, b in [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)]:
        m.lock(a, b)
    m.pin(0)
    m.pin(1)
    return m


def run_door():
    line("=")
    print("DOOR (rigid panel on a hinge)")
    line("=")
    m = build_door()
    # a door pinned at TWO points of a rigid panel cannot move at all in 2D.
    # kid-level knowledge: a door hinges about a LINE (2D: a point).
    # unpin one hinge point -> swings.
    del m.pinned[1]
    # swing it by driving corner 3 through an arc
    r = math.dist(m.points[0], m.points[3])
    frames = []
    for k in range(90):
        th = math.radians(k)            # 0..90 degrees, opening the door
        m.drive(3, r * math.cos(th), -r * math.sin(th))
        frames.append([p[:] for p in m.points])

    worst = 0.0
    for (i, j), rest in m.locked.items():
        for f in frames:
            worst = max(worst, abs(math.dist(f[i], f[j]) - rest))
    print(f"forward sim: 90 frames, worst constraint drift = {worst:.2e}")

    ledgers = observe(frames)
    scale = max(led.mean for led in ledgers.values())
    locked = detect_locked(ledgers, scale)
    clusters = rigid_clusters(4, locked)
    print(f"locked edges recovered: {sorted(locked.keys())}")
    print(f"rigid parts precipitated: {[sorted(c) for c in clusters]}")
    assert len(clusters) == 1 and clusters[0] == {0, 1, 2, 3}, \
        "door should precipitate as ONE rigid part"
    # every pairwise distance is locked -> fully rigid body. The only motion
    # left is rotation about the pinned point: that IS "a door".
    print("all 6 pairwise distances locked -> one rigid body")
    print("motion observed anyway -> the free parameter is orientation about")
    print("the fixed point: PERCEIVED AS A HINGE.")
    print("\nPASS: 'door' = rigid part + one anchored point + one angle.")
    return frames


if __name__ == "__main__":
    f1 = run_fourbar()
    print()
    f2 = run_door()
    line("=")
    print("ALL TESTS PASSED")
