"""
WORKING MEMORY — his RAM, used live while processing.

The door-net is permanent ('what is true in general'). Scratch is the other
half: overwritable registers ('what is true right now / this run'). He can
write notes, keep tallies, append to lists, chain them, and -- because every
write is logged -- replay any computation to find where it went wrong.

Four things, exactly as specified:
  1. INCREMENT   count = count + 1, the action chosen by HIS net
  2. TRACKING    numeric registers updated in real time
  3. ASSOCIATIONS string notes / references held in registers
  4. STEP-TRACE  current value + full history, to rerun and locate an error
"""

import numpy as np
from isaac import Isaac

RNG = np.random.default_rng(11)


def stream_of(grid):
    return ["on" if int(v) == 1 else "off" for v in grid.flatten()]


# ──────────────────────────────────────────────────────────────────
# 1 + 2.  COUNTING VIA RAM — two doors, ANY N. The magnitude lives in
#         a register, not as N separate nodes in the graph.
# ──────────────────────────────────────────────────────────────────
def counting_via_ram():
    print("=" * 72)
    print("  1+2.  COUNTING IN RAM  ('on'->incr, 'off'->hold;  count = count+1)")
    print("=" * 72)
    isaac = Isaac()
    # teach the PROGRAM: what to DO when he sees each symbol. Two doors only.
    isaac.observe(["on", "incr"])
    isaac.observe(["off", "hold"])
    isaac.consolidate()

    for k in (3, 5, 8):
        grids = []
        seen = set()
        while len(grids) < 300:
            g = RNG.integers(0, 2, (k, k)); key = g.tobytes()
            if key not in seen:
                seen.add(key); grids.append(g)
        ok = 0
        for g in grids:
            total, _ = isaac.react(stream_of(g), target="count")  # his RAM tallies
            if total == int(g.sum()):
                ok += 1
        print(f"    {k}x{k} grid (counts 0..{k*k}): {100*ok/len(grids):3.0f}%  "
              f"exact on 300 novel grids   [2 doors, register holds the number]")

    # show one run's live trace
    g = RNG.integers(0, 2, (3, 3))
    print(f"\n    live trace on one 3x3 grid (true count {int(g.sum())}):")
    total, hist = isaac.react(stream_of(g), target="count", verbose=True)
    print(f"    final count register = {total}")
    print(f"    step-trace = {hist}")


# ──────────────────────────────────────────────────────────────────
# 3.  ASSOCIATIONS — registers holding notes / references, not numbers
# ──────────────────────────────────────────────────────────────────
def associations():
    print("\n" + "=" * 72)
    print("  3.  ASSOCIATIONS  (string notes / references in registers)")
    print("=" * 72)
    isaac = Isaac()
    s = isaac.scratch
    s.write("current_task", "count_pixels")
    s.write("note", "grid looked mostly empty")
    s.append("seen_shapes", "square")
    s.append("seen_shapes", "line")        # chain onto the list
    s.append("seen_shapes", "cross")
    s.write("ref", "grid#42")
    print("    current_task :", s.read("current_task"))
    print("    note         :", s.read("note"))
    print("    seen_shapes  :", s.read("seen_shapes"), " <- appended / chained")
    print("    ref          :", s.read("ref"))
    print("    whole working state:", s.snapshot())


# ──────────────────────────────────────────────────────────────────
# 4.  STEP-TRACE — current value + every step, to replay and find the
#     error. We run a tally that deliberately double-counts once, then
#     use the trace to locate exactly where it diverged from truth.
# ──────────────────────────────────────────────────────────────────
def find_the_error():
    print("\n" + "=" * 72)
    print("  4.  CURRENT + STEP VALUE  (replay the trace to find where it broke)")
    print("=" * 72)
    isaac = Isaac()
    s = isaac.scratch

    cells = [1, 0, 1, 1, 0, 1]              # true running tally: 1,1,2,3,3,4
    s.write("count", 0)
    for i, v in enumerate(cells):
        if v == 1:
            s.incr("count")
            if i == 2:                      # planted bug: double-count once
                s.incr("count")

    truth = [1, 1, 2, 3, 3, 4]
    got = s.history("count")[1:]            # drop the initial 0
    print(f"    input cells : {cells}")
    print(f"    truth tally : {truth}")
    print(f"    his trace   : {got}")
    # the trace lets us localize the divergence
    for i, (a, b) in enumerate(zip(truth, got)):
        if a != b:
            print(f"    -> diverged at step {i}: expected {a}, register held {b}")
            print(f"       (replaying the step-trace pinpoints the bad step)")
            break
    print(f"    final count register = {s.read('count')} (truth {truth[-1]})")


def main():
    counting_via_ram()
    associations()
    find_the_error()
    print("\n" + "=" * 72)
    print("  Working memory is his now: he writes/reads/increments/appends in")
    print("  real time, holds numbers OR notes, chains them, and keeps a step-")
    print("  trace he can replay. The state finally lives in HIM, not the loop.")


if __name__ == "__main__":
    main()
