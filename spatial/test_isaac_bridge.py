"""
THE BRIDGE: spatial perception -> Isaac's net. (Step 4 — the integration
the WRITEUP names: "emitted relations -> typed edges -> crystallizer, so
verdicts become owned concepts.")

The rule being honored: coordinates are scratch, relations are storage.
The perceiver watches trajectories in scratch space; ONLY relations cross
into Isaac — locked/bounded edges, parts (pairwise-locked cliques), hinges
(clique overlaps), anchors (stationary points), and a scale-free SIGNATURE
(sorted locked-length ratios). Nothing coordinate-shaped is stored.

What must then work, and is tested:
  B1  Isaac ANSWERS structural questions from his fact index (who is locked
      to whom; what parts exist; where the hinges are; what is anchored)
  B2  RECOGNITION ACROSS POSE AND SCALE: the same mechanism, rebuilt 2.7x
      bigger, rotated 40 deg, translated, re-perceived from scratch ->
      the signature matches (relations are invariant; coordinates lied)
  B3  DISCRIMINATION: a door is not a four-bar (different part structure,
      different signature)
  B4  THE NULL GATE HOLDS AT THE BRIDGE: random walkers teach Isaac
      NOTHING. Perception that cannot refuse would poison the net.
"""

import math
import os
import random
import sys
from itertools import combinations

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))  # repo isaac.py
from engine import Mechanism, classify_edges, noise_floor_of
from isaac import Isaac

random.seed(21)
NOISE = 0.003


def line(c="-", n=66):
    print(c * n)


# ─────────────────────────── perceive → relations ───────────────────────────
def perceive(frames):
    """Trajectories -> the relation bundle (no coordinates escape)."""
    n = len(frames[0])
    verdicts = classify_edges(frames)
    locked = {p: v for p, v in verdicts.items() if v["kind"] == "locked"}
    bounded = [p for p, v in verdicts.items() if v["kind"] == "bounded"]
    # parts = maximal PAIRWISE-locked cliques (the 3D-correct rule). Grow
    # from every locked EDGE, not from single points -- a greedy grab from
    # seed 2 absorbs point 1 and the sibling bar (2,3) is never formed
    # (caught by this test's own four-bar, 2026-07-03).
    cliques = []
    for (a, b) in locked:
        c = {a, b}
        for cand in range(n):
            if cand not in c and all(
                    (min(cand, m), max(cand, m)) in locked for m in c):
                c.add(cand)
        if not any(c <= q for q in cliques):
            cliques = [q for q in cliques if not q <= c] + [c]
    # hinges = points shared between parts
    hinges = sorted({min(a & b) for a, b in combinations(cliques, 2)
                     if len(a & b) == 1})
    # anchors = points whose coordinate variation is explained by
    # measurement noise alone (same calibrated variance-ratio gate as
    # locked edges -- a bare displacement threshold dies to noise)
    scale = max((v["mean"] for v in verdicts.values()), default=1.0)
    anchors = []
    for i in range(n):
        still = True
        for d in range(len(frames[0][0])):
            cs = [f[i][d] for f in frames]
            mu = sum(cs) / len(cs)
            std = math.sqrt(sum((c - mu) ** 2 for c in cs) / len(cs))
            nf = noise_floor_of(cs)
            if std > max(nf * (1 + 4 / math.sqrt(len(cs))), 1e-9 * scale):
                still = False
                break
        if still:
            anchors.append(i)
    # scale-free identity: sorted locked-length ratios
    lens = sorted(v["mean"] for v in locked.values())
    sig = tuple(round(x / lens[-1], 3) for x in lens) if lens else ()
    return dict(locked=sorted(locked), bounded=sorted(bounded),
                parts=[sorted(c) for c in cliques], hinges=hinges,
                anchors=anchors, signature=sig)


def emit(isaac, label, rel):
    """Relations -> the net. Facts via teach() (indexed AND observed, so
    doors form); the signature as meta on a scene node."""
    taught = 0
    for (i, j) in rel["locked"]:
        isaac.teach(f"{label}.p{i}", "locked_to", f"{label}.p{j}"); taught += 1
    for (i, j) in rel["bounded"]:
        isaac.teach(f"{label}.p{i}", "bounded_with", f"{label}.p{j}"); taught += 1
    for k, part in enumerate(rel["parts"]):
        for i in part:
            isaac.teach(f"{label}.part{k}", "contains", f"{label}.p{i}"); taught += 1
    for h in rel["hinges"]:
        isaac.teach(label, "hinge_at", f"{label}.p{h}"); taught += 1
    for a in rel["anchors"]:
        isaac.teach(label, "anchored_at", f"{label}.p{a}"); taught += 1
    if rel["signature"]:
        isaac.net.add_door("scene", f"scene:{label}", tag="scene")
        isaac.net.set_meta(f"scene:{label}", "spatial_signature",
                           list(rel["signature"]))
        isaac.net.set_meta(f"scene:{label}", "structure",
                           dict(n_parts=len(rel["parts"]),
                                part_sizes=sorted(len(p) for p in rel["parts"]),
                                n_hinges=len(rel["hinges"])))
    return taught


def same_structure(isaac, la, lb, tol=0.02):
    """Isaac compares two scenes HE holds: signature + structure match."""
    sa = isaac.net.get_meta(f"scene:{la}", "spatial_signature")
    sb = isaac.net.get_meta(f"scene:{lb}", "spatial_signature")
    ta = isaac.net.get_meta(f"scene:{la}", "structure")
    tb = isaac.net.get_meta(f"scene:{lb}", "structure")
    if None in (sa, sb, ta, tb) or len(sa) != len(sb):
        return False
    return (max(abs(x - y) for x, y in zip(sa, sb)) < tol
            and ta["part_sizes"] == tb["part_sizes"]
            and ta["n_hinges"] == tb["n_hinges"])


# ───────────────────────────── the worlds ─────────────────────────────
def noisy_frames(m, drive_pt, r, pin, cycles=3, steps=720, phase=0.0):
    frames = []
    for k in range(steps):
        th = 2 * math.pi * cycles * k / steps + phase
        m.drive(drive_pt, pin[0] + r * math.cos(th), pin[1] + r * math.sin(th),
                sweeps=60)
        frames.append([[c + random.gauss(0, NOISE) for c in p]
                       for p in m.points])
    return frames


def fourbar(scale=1.0, rot=0.0, tx=0.0, ty=0.0):
    base = [[0.0, 0.0], [2.0, 0.0], [6.083, 5.686], [8.0, 0.0]]
    c, s = math.cos(rot), math.sin(rot)
    pts = [[scale * (c * x - s * y) + tx, scale * (s * x + c * y) + ty]
           for (x, y) in base]
    m = Mechanism(points=pts)
    m.lock(0, 1); m.lock(1, 2); m.lock(2, 3)
    m.pin(0); m.pin(3)
    return m, pts[0], 2.0 * scale, rot


def door_world():
    m = Mechanism(points=[[0.0, 0.0], [0.0, 3.0], [2.0, 3.0], [2.0, 0.0]])
    for a, b in [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)]:
        m.lock(a, b)
    m.pin(0)
    frames = []
    r = math.dist(m.points[0], m.points[3])
    for k in range(360):
        th = math.radians(80 * (0.5 - 0.5 * math.cos(2 * math.pi * k / 180)))
        m.drive(3, r * math.cos(-th), r * math.sin(-th), sweeps=50)
        frames.append([[c + random.gauss(0, NOISE) for c in p]
                       for p in m.points])
    return frames


# ═══════════════════════════════ B1: teach + ask ═══════════════════════════
line("=")
print("B1 -- perceive a four-bar; Isaac answers structural questions")
line("=")
isaac = Isaac()
m, pin, r, _ = fourbar()
relA = perceive(noisy_frames(m, 1, r, pin))
n_taught = emit(isaac, "fourbarA", relA)
print(f"relations taught: {n_taught}  "
      f"(locked {len(relA['locked'])}, parts {len(relA['parts'])}, "
      f"hinges {len(relA['hinges'])}, anchors {len(relA['anchors'])})")

q1 = isaac.fact_index[("fourbarA.p0", "locked_to")]
q2 = isaac.fact_index[("fourbarA", "hinge_at")]
q3 = isaac.fact_index[("fourbarA", "anchored_at")]
print(f"  'what is p0 locked to?'  -> {q1}")
print(f"  'where are the hinges?'  -> {q2}")
print(f"  'what is anchored?'      -> {q3}")
assert "fourbarA.p1" in q1 and "fourbarA.p3" in q1   # crank + ground link
assert len(relA["parts"]) == 4                        # 4 bars incl. ground
assert len(relA["hinges"]) == 4                       # 4 revolute pins
assert set(q3) == {"fourbarA.p0", "fourbarA.p3"}
print("-> the perception wall, crossed: watched motion became owned,")
print("   queryable knowledge. 4 bars found incl. the undeclared ground.\n")

# ═══════════════════ B2: recognition across pose and scale ═════════════════
line("=")
print("B2 -- same mechanism, 2.7x bigger, rotated 40 deg, translated")
line("=")
m2, pin2, r2, _ = fourbar(scale=2.7, rot=math.radians(40), tx=5, ty=-3)
relB = perceive(noisy_frames(m2, 1, r2, pin2, phase=1.1))
emit(isaac, "fourbarB", relB)
print(f"  signature A: {relA['signature']}")
print(f"  signature B: {relB['signature']}")
match = same_structure(isaac, "fourbarA", "fourbarB")
print(f"  Isaac's verdict: {'SAME structure' if match else 'different'}")
assert match, "pose/scale broke recognition -- the wall is NOT crossed"
print("-> every coordinate changed; every relation held. Recognized.\n")

# ═══════════════════════ B3: a door is not a four-bar ══════════════════════
line("=")
print("B3 -- discrimination: the door")
line("=")
relD = perceive(door_world())
emit(isaac, "door", relD)
print(f"  door: parts {[len(p) for p in relD['parts']]} "
      f"(one rigid panel), signature {relD['signature']}")
assert len(relD["parts"]) == 1 and len(relD["parts"][0]) == 4
assert not same_structure(isaac, "fourbarA", "door")
print("-> one rigid 4-point panel vs four linked bars: NOT the same thing.\n")

# ══════════════════════ B4: the null gate at the bridge ════════════════════
line("=")
print("B4 -- random walkers must teach Isaac NOTHING")
line("=")
walks = []
for _ in range(5):
    x, y = random.uniform(-2, 2), random.uniform(-2, 2)
    w = []
    for _ in range(500):
        x += random.gauss(0, 0.08); y += random.gauss(0, 0.08)
        w.append([x + random.gauss(0, NOISE), y + random.gauss(0, NOISE)])
    walks.append(w)
frames_null = [[walks[k][t] for k in range(5)] for t in range(500)]
relN = perceive(frames_null)
facts_before = sum(len(v) for v in isaac.fact_index.values())
taught = emit(isaac, "nothing", relN)
facts_after = sum(len(v) for v in isaac.fact_index.values())
print(f"  perceived: locked {len(relN['locked'])}, bounded "
      f"{len(relN['bounded'])}, parts {len(relN['parts'])}")
print(f"  facts taught: {taught} (index {facts_before} -> {facts_after})")
assert taught == 0 and facts_before == facts_after
print("-> perception that can refuse: no structure, no facts, net unpoisoned.")

print()
line("=")
print("PASS: relations crossed the bridge; coordinates did not. Isaac")
print("answers, recognizes across pose+scale, discriminates, and refuses.")
line("=")
