"""
Counting, reformulated as a SEQUENTIAL state walk.

The lookup encodings (A-E in mvt_counting.py) all fail to generalize because
counting is a global SUM and the lookup/voting mechanism has no aggregation
operator. But a door net CAN represent a finite-state machine, and counting
IS a finite-state machine:

    state = running tally.  see an ON cell -> advance tally.  OFF -> stay.

We teach Isaac ONLY the general increment rule (the successor function over
tallies 0..8) -- 18 transitions, none of which mention any specific grid.
Then counting a NOVEL grid is a deterministic walk whose END STATE is the
count. We never hand Isaac a grid's answer; he derives it by walking.

This is the same shape as Isaac's existing math: memorize a general table,
then compose. If this generalizes to novel grids, the lesson is precise:
the substrate supports counting, but only when the task is sequential/stateful,
not a single lookup. That directly motivates prioritizing prediction (also
sequential) over static single-shot recall.
"""

import numpy as np
from isaac import Isaac

RNG = np.random.default_rng(11)
KMAX = 9  # 3x3 grid -> counts 0..9


def make_grids(n, k=3):
    seen = {}
    while len(seen) < n:
        g = RNG.integers(0, 2, (k, k))
        key = g.tobytes()
        if key not in seen:
            seen[key] = (g, int(g.sum()))
    return list(seen.values())


def teach_increment_rule(isaac):
    """Teach ONLY the general successor function. No grids involved.
    Encode (state, input) as a single token so a door represents the
    transition:  't{K}_on' -> 't{K+1}',  't{K}_off' -> 't{K}'.
    """
    for k in range(KMAX + 1):
        # seeing an ON pixel advances the tally
        if k < KMAX:
            isaac.observe([f"t{k}_on", f"t{k+1}"])
        # seeing an OFF pixel keeps it (identity)
        isaac.observe([f"t{k}_off", f"t{k}"])
    isaac.consolidate()


def count_by_walk(isaac, grid):
    """Walk the grid cell-by-cell, advancing the tally via learned doors.
    Returns the final tally as an int. Isaac supplies every transition."""
    state = "t0"
    for v in grid.flatten():
        sym = "on" if int(v) == 1 else "off"
        key = f"{state}_{sym}"
        nxts = isaac.net.get_doors(key, tag="seq")
        if not nxts:
            return None  # rule missing -> Isaac can't take this step
        # deterministic: each key has exactly one taught successor
        state = sorted(nxts)[0]
    try:
        return int(state[1:])  # 't4' -> 4
    except ValueError:
        return None


def main():
    isaac = Isaac()
    teach_increment_rule(isaac)

    # Novel grids only — none were involved in teaching the rule.
    test = make_grids(300)
    ok = 0
    near = 0
    answered = 0
    for g, c in test:
        p = count_by_walk(isaac, g)
        if p is not None:
            answered += 1
            if p == c:
                ok += 1
            if abs(p - c) <= 1:
                near += 1
    n = len(test)

    print("=" * 70)
    print("  COUNTING AS A SEQUENTIAL TALLY WALK")
    print("=" * 70)
    print(f"  taught: the increment rule only ({2*KMAX} general transitions)")
    print(f"  tested: {n} NOVEL grids, none seen during teaching")
    print("-" * 70)
    print(f"  exact count correct : {ok}/{n}  = {ok/n:.1%}")
    print(f"  within +/-1         : {near}/{n}  = {near/n:.1%}")
    print(f"  answered (rule hit) : {answered}/{n}  = {answered/n:.1%}")
    print("=" * 70)
    if ok / n > 0.95:
        print("  RESULT: counting GENERALIZES when formulated as a state walk.")
        print("  The substrate can count; single-lookup was the wrong shape.")
    else:
        print("  RESULT: even the state-walk formulation did not generalize.")


if __name__ == "__main__":
    main()
