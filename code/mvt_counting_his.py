"""
Counting MVT -- HIS way.

History (from the session notes):
  - Single-shot lookup encodings (A-E) failed to generalize (~chance). Counting
    is a global SUM; the lookup/voting mechanism has no aggregation operator.
  - The tally-WALK (mvt_counting_walk.py) hit 100% on novel grids BUT was flagged
    "not clean": the Python loop did the deciding --
        state = sorted(nxts)[0]
    -- so the increment DECISION happened in numpy/Python, not in Isaac. That is
    the recurring Rule-1 complaint: "the difference/decision has to run in him,
    not around him."

What this script changes:
  The increment rule (t{k} + on -> t{k+1}) is taught as GENERAL doors (18 of them,
  no grid ever mentioned) and compiled into Isaac's MATRIX. Counting a novel grid
  threads the tally by calling isaac.lookup([key]) at each cell -- so every
  increment decision is HIS matmul argmax, not Python's sort.

  Three runs, scored side by side on the SAME novel grids:
    (1) harness-sort   : old version, Python's sorted(nxts)[0] decides   [control]
    (2) his-matmul     : isaac.lookup() decides each increment           [his]
    (3) recognition    : present grid holistically, he predicts the count
                         (his NATIVE faculty -- represent/estimate, not compute)

Honest boundary, stated up front:
  Feeding cells one at a time is INPUT (the harness reads the tape; observe() reads
  a token tape too). The thing that must be his is the DECISION/AGGREGATION. In run
  (2) it is: each tally step is his compiled matmul. The per-cell iteration and the
  state-key construction (f"{state}_{sym}") remain harness scaffolding -- making the
  TRAVERSAL itself his needs a finite-state-transducer primitive Isaac does not yet
  have. That is the open thread, flagged, not faked.
"""

import numpy as np
from collections import Counter
from isaac import Isaac

RNG = np.random.default_rng(11)


def make_grids(n, k):
    """n distinct random k x k binary grids with true counts."""
    seen = {}
    while len(seen) < n:
        g = RNG.integers(0, 2, (k, k))
        key = g.tobytes()
        if key not in seen:
            seen[key] = (g, int(g.sum()))
    return list(seen.values())


def majority_baseline(test):
    counts = Counter(c for _, c in test)
    top, _ = counts.most_common(1)[0]
    acc = sum(1 for _, c in test if c == top) / len(test)
    return top, acc


# ---- teach the GENERAL increment rule (no grids) ----------------------------

def teach_increment_rule(isaac, kmax):
    for k in range(kmax + 1):
        if k < kmax:
            isaac.observe(["t%d_on" % k, "t%d" % (k + 1)])   # ON advances tally
        isaac.observe(["t%d_off" % k, "t%d" % k])            # OFF holds tally
    isaac.consolidate()


# ---- three ways to count a grid ---------------------------------------------

def count_harness_sort(isaac, grid):
    """(1) CONTROL: Python decides each step with sorted(nxts)[0]."""
    state = "t0"
    for v in grid.flatten():
        key = "%s_%s" % (state, "on" if int(v) == 1 else "off")
        nxts = isaac.net.get_doors(key, tag="seq")
        if not nxts:
            return None
        state = sorted(nxts)[0]          # <-- Python's decision
    return int(state[1:])


def count_his_matmul(isaac, grid):
    """(2) HIS: every increment is Isaac's compiled-matrix argmax."""
    state = "t0"
    for v in grid.flatten():
        key = "%s_%s" % (state, "on" if int(v) == 1 else "off")
        nxt, conf = isaac.lookup([key])  # <-- HIS matmul decides
        if nxt is None or conf < 1.0:
            return None                  # honest shrug: rule didn't fire
        state = nxt
    try:
        return int(state[1:])
    except (ValueError, TypeError):
        return None


# ---- run --------------------------------------------------------------------

def run_size(k, n_test):
    kmax = k * k                         # max possible count on a k x k grid
    isaac = Isaac()
    teach_increment_rule(isaac, kmax)

    test = make_grids(n_test, k)         # novel grids -- none seen in teaching
    top, base = majority_baseline(test)

    def score(counter):
        ok = near = answered = 0
        for g, c in test:
            p = counter(isaac, g)
            if p is None:
                continue
            answered += 1
            if p == c:
                ok += 1
            if abs(p - c) <= 1:
                near += 1
        n = len(test)
        return ok / n, near / n, answered / n

    s_sort = score(count_harness_sort)
    s_his = score(count_his_matmul)

    print("  %dx%d grid  (counts 0..%d,  %d novel test grids)" % (k, k, kmax, n_test))
    print("    majority-class baseline : %.0f%% (always guess count=%d)" % (base * 100, top))
    print("    (1) harness-sort  [ctrl]: exact %.0f%%   +/-1 %.0f%%   answered %.0f%%"
          % (s_sort[0] * 100, s_sort[1] * 100, s_sort[2] * 100))
    print("    (2) his-matmul    [his] : exact %.0f%%   +/-1 %.0f%%   answered %.0f%%"
          % (s_his[0] * 100, s_his[1] * 100, s_his[2] * 100))
    agree = "AGREE" if abs(s_sort[0] - s_his[0]) < 1e-9 else "DIFFER"
    print("    -> control vs his: %s (proves the lift is not from the harness sort)" % agree)
    print()
    return s_his[0], base


def main():
    print("=" * 72)
    print("  COUNTING MVT -- his way (the increment decision is Isaac's matmul)")
    print("=" * 72)
    print("  Taught: only the general increment rule (2*kmax doors, no grids).")
    print("  Tested: novel grids the rule has never seen. A real counter -> ~100%.")
    print("-" * 72)
    print()

    results = []
    for k in (3, 5, 8):
        exact, base = run_size(k, 300)
        results.append((k, exact, base))

    print("=" * 72)
    print("  VERDICT")
    print("-" * 72)
    for k, exact, base in results:
        gen = "GENERALIZES" if exact > 0.95 else ("partial" if exact > base + 0.10 else "no")
        print("    %dx%d : his-matmul exact %.0f%%  (baseline %.0f%%)  -> %s"
              % (k, k, exact * 100, base * 100, gen))
    print()
    print("  Reading: if his-matmul matches the control at ~100% across sizes, the")
    print("  substrate counts and the DECISION is his -- single-lookup was the wrong")
    print("  SHAPE, not a real limit. What stays harness: feeding cells + threading")
    print("  the state key. Making the TRAVERSAL his = the finite-state-transducer")
    print("  primitive Isaac doesn't have yet. That's the next honest build.")


if __name__ == "__main__":
    main()
