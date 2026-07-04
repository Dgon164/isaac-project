"""
Snake: an open chain that follows its own path
----------------------------------------------
Simulation (game-snake / train-on-rails rule): the head wanders with a
fixed step size and bounded turning; every other link steps into the
position its predecessor just left. No loop closure, no rigid body --
a new species for the perceiver.

What perception should find, from trajectories alone:
  1. adjacent distances LOCKED (segment length)         -- rigid links
  2. next-adjacent distances BOUNDED                    -- hidden turn limit,
     recoverable: d(i,i+2)^2 = 2 s^2 (1 + cos(turn))    -> max turn angle
  3. LAG STRUCTURE: traj_j(t) == traj_i(t - (j-i))      -- "my present is
     your past" -> one path generator drives everything
  4. THE PATH ITSELF: union of all trajectories collapses onto a single
     curve = the head's path. The invisible rail, reconstructed.
"""

import math
import random
from engine import observe

random.seed(11)

N = 8            # links
S = 1.0          # step / segment length
TURN_MAX = math.radians(30)   # hidden: head never turns more than this per step
FRAMES = 900


def simulate_snake():
    # start stretched along x, head at the right end (index 0 = head)
    body = [[-k * S, 0.0] for k in range(N)]
    heading = 0.0
    frames = []
    for _ in range(FRAMES):
        heading += random.uniform(-TURN_MAX, TURN_MAX)
        new_head = [body[0][0] + S * math.cos(heading),
                    body[0][1] + S * math.sin(heading)]
        body = [new_head] + [body[k][:] for k in range(N - 1)]  # follow the leader
        frames.append([p[:] for p in body])
    return frames


def line(c="-", n=64):
    print(c * n)


line("=")
print(f"SNAKE: {N} links, step {S}, hidden turn limit {math.degrees(TURN_MAX):.0f} deg/step")
line("=")
frames = simulate_snake()

# ------------------------------------------------------------ 1. ledger
ledgers = observe(frames)
scale = max(led.mean for led in ledgers.values())
print(f"self-calibrated scale = {scale:.3f}\n")

adjacent = [(i, i + 1) for i in range(N - 1)]
skip_one = [(i, i + 2) for i in range(N - 2)]

print("adjacent pairs:")
for p in adjacent:
    led = ledgers[p]
    tag = "LOCKED" if led.std < 1e-3 * scale else "varies"
    print(f"  d{p} = {led.mean:.3f} +/- {led.std:.1e}   {tag}")
    assert tag == "LOCKED"
seg = ledgers[(0, 1)].mean
print(f"-> serial chain of rigid links, segment length {seg:.3f}")

# ------------------------------------------------ 2. hidden turn limit
print()
line()
print("NEXT-ADJACENT PAIRS: bounded -> hidden turning constraint")
line()
for p in skip_one[:3]:
    ds = [math.dist(f[p[0]], f[p[1]]) for f in frames]
    lo, hi = min(ds), max(ds)
    # d^2 = 2 s^2 (1 + cos(turn)); hi -> straight, lo -> max turn
    turn_inferred = math.acos(max(min(lo * lo / (2 * seg * seg) - 1, 1), -1))
    print(f"  d{p}: range [{lo:.3f}, {hi:.3f}]  "
          f"-> max bend here = {math.degrees(turn_inferred):5.2f} deg "
          f"(truth {math.degrees(TURN_MAX):.0f})")
ds = [math.dist(f[0], f[2]) for f in frames]
turn_inferred = math.acos(max(min(min(ds) ** 2 / (2 * seg * seg) - 1, 1), -1))
assert abs(turn_inferred - TURN_MAX) < math.radians(3)
print("-> joint limits recovered from fold bounds, same trick as the crank")

# --------------------------------------------------- 3. lag structure
print()
line()
print("LAG DETECTION: is anyone living in someone else's past?")
line()

def lag_match(i, j, max_lag=12):
    """Find integer lag L minimizing mean distance traj_j(t) vs traj_i(t-L)."""
    best_lag, best_err = None, float("inf")
    for L in range(0, max_lag + 1):
        errs = [math.dist(frames[t][j], frames[t - L][i])
                for t in range(max_lag, len(frames))]
        e = sum(errs) / len(errs)
        if e < best_err:
            best_err, best_lag = e, L
    return best_lag, best_err

print("  pair      best lag   residual")
ok = True
for j in [1, 2, 4, 7]:
    L, e = lag_match(0, j)
    print(f"  (0,{j})        {L:2d}       {e:.2e}")
    ok &= (L == j and e < 1e-9)
assert ok
print("-> every link's present = the head's past, lag = chain position.")
print("   ONE generator. The whole 16-dimensional motion is a single curve.")

# ------------------------------------------------ 4. reconstruct the path
print()
line()
print("THE INVISIBLE RAIL: reconstruct the path from the union of motion")
line()
head_path = [tuple(f[0]) for f in frames]
# every position ever occupied by ANY link should lie on the head's path
worst = 0.0
for t in range(N, len(frames)):
    for k in range(1, N):
        p = frames[t][k]
        d = min(math.dist(p, hp) for hp in head_path[max(0, t - k - 2): t])
        worst = max(worst, d)
print(f"  worst distance from any link position to the head's path: {worst:.2e}")
assert worst < 1e-9
print(f"  path length observed: {len(head_path) * S:.0f} units; the perceiver")
print("  can now treat the PATH as an object: a 1-D curve constraint that")
print("  was never drawn, never visible, and is now fully mapped.")

print()
line("=")
print("PASS: chain structure, joint limits, follow-the-leader causality,")
print("and the hidden path all recovered from trajectories alone.")
line("=")
