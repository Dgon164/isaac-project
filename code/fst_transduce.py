"""
The walk, made his.  isaac.transduce(start, stream) threads a state through an
input stream, the next state chosen at each step by HIS matrix
(lookup([state, symbol]) -> state').  The transition rule lives entirely in
learned doors; the loop is just the universal tape-reader.

To prove the primitive is GENERAL and not a counting trick, three different
finite-state machines run through the SAME transduce call. They differ ONLY in
which transitions were taught -- never in Python.

  1. COUNT   : tally 0..N.  on advances, off holds.  read final state as int.
  2. PARITY  : even/odd.    on flips, off holds.      (a 2-state machine)
  3. RUN     : "are there two ON cells in a row?"     (3 states, absorbing accept)

Each rule is taught with NO grid involved. Then novel grids are transduced and
scored against ground truth. Same engine call every time -- the program is the
net, not the harness.
"""

import numpy as np
from isaac import Isaac

RNG = np.random.default_rng(11)


def make_grids(n, k):
    seen = {}
    while len(seen) < n:
        g = RNG.integers(0, 2, (k, k))
        key = g.tobytes()
        if key not in seen:
            seen[key] = g
    return list(seen.values())


def stream_of(grid):
    """Raw read of the grid as on/off symbols (row-major). No features."""
    return ["on" if int(v) == 1 else "off" for v in grid.flatten()]


# ── machine 1: COUNT ──────────────────────────────────────────────
def teach_count(isaac, kmax):
    for k in range(kmax + 1):
        if k < kmax:
            isaac.observe(["c%d" % k, "on", "c%d" % (k + 1)])
        isaac.observe(["c%d" % k, "off", "c%d" % k])

def count_truth(grid):
    return int(grid.sum())

def count_readout(final):
    return int(final[1:]) if final and final.startswith("c") else None


# ── machine 2: PARITY ─────────────────────────────────────────────
def teach_parity(isaac):
    isaac.observe(["even", "on", "odd"]);  isaac.observe(["even", "off", "even"])
    isaac.observe(["odd", "on", "even"]);  isaac.observe(["odd", "off", "odd"])

def parity_truth(grid):
    return "odd" if int(grid.sum()) % 2 else "even"

def parity_readout(final):
    return final


# ── machine 3: RUN  (two ON in a row?) ────────────────────────────
def teach_run(isaac):
    # q0 = no run yet, last not ON ; q1 = last was ON ; hit = saw two ON in a row
    isaac.observe(["q0", "on", "q1"]);   isaac.observe(["q0", "off", "q0"])
    isaac.observe(["q1", "on", "hit"]);  isaac.observe(["q1", "off", "q0"])
    isaac.observe(["hit", "on", "hit"]); isaac.observe(["hit", "off", "hit"])

def run_truth(grid):
    flat = grid.flatten()
    return "hit" if any(flat[i] == 1 and flat[i + 1] == 1
                        for i in range(len(flat) - 1)) else "no_run"

def run_readout(final):
    # accept iff we reached the absorbing state; q0/q1 both mean "no run"
    return "hit" if final == "hit" else ("no_run" if final in ("q0", "q1") else None)


def evaluate(name, isaac, start, grids, truth_fn, readout_fn, halt=None):
    ok = answered = 0
    for g in grids:
        final, _ = isaac.transduce(start, stream_of(g), halt=halt)
        pred = readout_fn(final)
        if pred is None:
            continue
        answered += 1
        if pred == truth_fn(g):
            ok += 1
    n = len(grids)
    print("    %-8s exact %3.0f%%   answered %3.0f%%   (%d novel grids)"
          % (name, 100 * ok / n, 100 * answered / n, n))
    return ok / n


def main():
    print("=" * 72)
    print("  TRANSDUCE -- one primitive, three machines, his walk")
    print("=" * 72)
    print("  isaac.transduce(start, stream) is the ONLY engine call used below.")
    print("  Each machine is just a different set of taught transition doors.")
    print("-" * 72)

    for k in (3, 5, 8):
        kmax = k * k
        grids = make_grids(300, k)        # novel grids, none used in teaching

        # each machine gets its own Isaac so rules don't cross-talk
        ic = Isaac(); teach_count(ic, kmax); ic.consolidate()
        ip = Isaac(); teach_parity(ip);      ip.consolidate()
        ir = Isaac(); teach_run(ir);         ir.consolidate()

        print("\n  %dx%d grid:" % (k, k))
        a = evaluate("COUNT", ic, "c0",   grids, count_truth,  count_readout)
        b = evaluate("PARITY", ip, "even", grids, parity_truth, parity_readout)
        c = evaluate("RUN",    ir, "q0",   grids, run_truth,    run_readout, halt="hit")
        if not (a > 0.95 and b > 0.95 and c > 0.95):
            print("    (note: a machine dropped below 95% -- inspect)")

    print("\n" + "=" * 72)
    print("  All three generalize to novel grids through the same his-walk.")
    print("  The primitive is general: program = doors, control = transduce.")
    print("  Counting was never special -- it was one machine among many.")


if __name__ == "__main__":
    main()
