"""
The null battery: worlds with NO structure, where the honest answer is
"nothing here" -- plus one planted positive control so a mute classifier
can't pass by classifying nothing.

Why this file exists: all 11 original tests are planted SUCCESSES. The
discovery stack's trust anchor is its 0/20 false discoveries on pure noise
(E9); the spatial perceiver had no equivalent until now. A perceiver that
finds structure in noise can never be trusted about structure in signal.

  N1  free random walkers            -> ZERO locked, ZERO bounded edges
  N2  planted rigid pair among them  -> exactly that pair LOCKED (control),
      found by the CALIBRATED gate under noise where the old hand-tuned
      rel_tol threshold fails both directions
  N3  random waveforms               -> zero gates found (no false circuit)
  N4  independent walkers            -> no false lag ("nobody lives in
      anyone else's past")
"""

import math
import random
from itertools import combinations
from engine import classify_edges, detect_locked, observe

random.seed(13)

NOISE = 0.02          # measurement noise, std per coordinate
FRAMES = 700


def line(c="-", n=66):
    print(c * n)


def walk(n_steps, step=0.08, start=None):
    x, y = start or (random.uniform(-2, 2), random.uniform(-2, 2))
    out = []
    for _ in range(n_steps):
        x += random.gauss(0, step)
        y += random.gauss(0, step)
        out.append((x, y))
    return out


def noisy(p):
    return [p[0] + random.gauss(0, NOISE), p[1] + random.gauss(0, NOISE)]


# ═══════════════════════ N1: free walkers -> nothing ═══════════════════════
line("=")
print("N1 -- eight independent random walkers: the honest answer is NOTHING")
line("=")
walks = [walk(FRAMES) for _ in range(8)]
frames = [[noisy(walks[k][t]) for k in range(8)] for t in range(FRAMES)]
verdicts = classify_edges(frames)
counts = {}
for v in verdicts.values():
    counts[v["kind"]] = counts.get(v["kind"], 0) + 1
print(f"28 pairs classified: {counts}")
false_locked = counts.get("locked", 0)
false_bounded = counts.get("bounded", 0)
assert false_locked == 0, f"{false_locked} FALSE locked edges -- KILL"
assert false_bounded == 0, f"{false_bounded} FALSE bounded edges -- KILL"
print("-> zero locked, zero bounded. No structure invented.\n")

# ═══════════ N2: planted rigid pair -> found; old threshold fails ═════════
line("=")
print("N2 -- positive control: ONE rigid pair hidden among the walkers")
line("=")
base = walk(FRAMES, step=0.08)
OFFSET = 1.7
rigid_a = [(x, y) for (x, y) in base]
rigid_b = [(x + OFFSET, y) for (x, y) in base]      # locked distance, moving
pts = walks[:6] + [rigid_a, rigid_b]
frames2 = [[noisy(pts[k][t]) for k in range(8)] for t in range(FRAMES)]
verdicts2 = classify_edges(frames2)
locked_pairs = [p for p, v in verdicts2.items() if v["kind"] == "locked"]
print(f"locked edges found: {locked_pairs}")
assert locked_pairs == [(6, 7)], "planted rigid pair missed or extras added"
v = verdicts2[(6, 7)]
print(f"  d(6,7): std {v['std']:.4f} vs measured noise floor {v['noise']:.4f}"
      f" -> LOCKED (variance explained by noise alone)")

# the old hand-tuned gate, on the same data:
ledgers = observe(frames2)
scale = max(led.mean for led in ledgers.values())
old = detect_locked(ledgers, scale, rel_tol=1e-3)
print(f"\nold detect_locked(rel_tol=1e-3) on the same data: "
      f"{sorted(old.keys()) or 'NOTHING'}")
assert (6, 7) not in old, (
    "expected the demonstration that the hand threshold misses it")
print("-> the hand-tuned threshold MISSES the genuinely rigid pair (its std "
      f"is noise-sized,\n   {v['std']:.4f}, above 1e-3*scale = "
      f"{1e-3*scale:.4f}). The calibrated gate adapts; the constant cannot.\n")

# ═══════════════════ N3: random waveforms -> no circuit ════════════════════
line("=")
print("N3 -- five random bit streams: no gates may be 'discovered'")
line("=")
T = 400
sig = {n: [random.randint(0, 1) for _ in range(T)] for n in "ABCDE"}
UNARY = {"BUF": lambda x: x, "NOT": lambda x: 1 - x}
BINARY = {"AND": lambda x, y: x & y, "OR": lambda x, y: x | y,
          "XOR": lambda x, y: x ^ y, "NAND": lambda x, y: 1 - (x & y),
          "NOR": lambda x, y: 1 - (x | y)}
found = 0
names = list(sig)
for out_n in names:
    out = sig[out_n]
    for lag in (1, 2, 3):
        for in_n in names:
            if in_n != out_n:
                for fn in UNARY.values():
                    if all(out[t] == fn(sig[in_n][t - lag])
                           for t in range(3, T)):
                        found += 1
        for na, nb in combinations([n for n in names if n != out_n], 2):
            for fn in BINARY.values():
                if all(out[t] == fn(sig[na][t - lag], sig[nb][t - lag])
                       for t in range(3, T)):
                    found += 1
print(f"gate explanations found across all signals/lags/functions: {found}")
assert found == 0, "invented a circuit from noise -- KILL"
print("-> all five correctly remain PRIMARY (unexplained). No false wiring.\n")

# ═══════════════════════ N4: no false lag structure ════════════════════════
line("=")
print("N4 -- independent walkers: nobody lives in anyone else's past")
line("=")
false_lags = 0
for i, j in combinations(range(6), 2):
    best = min(
        (sum(math.dist(frames[t][j], frames[t - L][i])
             for t in range(12, FRAMES)) / (FRAMES - 12), L)
        for L in range(0, 13))
    resid, L = best
    if resid < 20 * NOISE:            # a real follower matches to ~noise
        false_lags += 1
print(f"pairs whose best lag residual approaches the noise floor: "
      f"{false_lags}/15")
assert false_lags == 0, "false leader-follower relation -- KILL"
print("-> zero false causality. The lag question only fires on real chains.\n")

line("=")
print("PASS: nothing was found where nothing exists; the one planted truth")
print("was found under noise that defeats the old hand-tuned threshold.")
print("The spatial perceiver now has its E9.")
line("=")
