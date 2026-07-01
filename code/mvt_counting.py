"""
Minimum Viable Test — can Isaac learn to count pixels on a 3x3 grid
and generalize to NOVEL grids?

This gates the whole visual curriculum (per the handoff addendum).

We do NOT trust a single encoding. The addendum's literal sketch observes
the count token as its own isolated single-token sequence, so no door ever
connects grid -> count. That is structurally broken. So we test several
HONEST encodings (no feature extraction, only tokenization + position tags),
and measure generalization to grids never seen in training, against the
chance/majority-class baseline.

Counts of a random 3x3 binary grid follow Binomial(9, 0.5):
  count 4 and 5 are each ~24.6%  ->  majority-class baseline ~= 24.6%
A real counter scores ~100%. "Learning" must clearly beat ~25%.
"""

import numpy as np
from collections import Counter
from isaac import Isaac

RNG = np.random.default_rng(7)


def make_grids(n, k=3):
    """n random k x k binary grids, deduplicated, with their true counts."""
    seen = {}
    while len(seen) < n:
        g = RNG.integers(0, 2, (k, k))
        key = g.tobytes()
        if key not in seen:
            seen[key] = (g, int(g.sum()))
    return list(seen.values())


def majority_baseline(test):
    """Accuracy of always predicting the most common count in the test set."""
    counts = Counter(c for _, c in test)
    top = counts.most_common(1)[0][0]
    acc = sum(1 for _, c in test if c == top) / len(test)
    return top, acc


# ───────────────────────── encodings ──────────────────────────
# Each returns (observe_fn, query_fn).
#   observe_fn(isaac, grid, count) -> teaches one example
#   query_fn(isaac, grid)          -> returns predicted count (int) or None
#
# Answer tokens are always "count_N". The query asks Isaac to produce that.

def _pred_count(ans):
    """Turn a predicted token like 'count_4' into the int 4."""
    if isinstance(ans, str) and ans.startswith("count_"):
        try:
            return int(ans.split("_")[1])
        except (IndexError, ValueError):
            return None
    return None


def enc_A_literal(isaac, grid, count):
    """The addendum's literal sketch: rows, then an isolated count token.
    Expected to be broken — nothing binds grid to count."""
    isaac.observe_matrix(grid)
    isaac.observe([f"count_{count}"])

def qry_A(isaac, grid):
    # There is no real context to query with. Try the obvious thing.
    ans, _ = isaac.lookup(["count"])
    return _pred_count(ans)


def enc_B_flat(isaac, grid, count):
    """Whole grid flattened into ONE sequence, count appended.
    A door forms only from the LAST cell value to the count."""
    toks = [str(int(v)) for v in grid.flatten()] + [f"count_{count}"]
    isaac.observe(toks)

def qry_B(isaac, grid):
    ctx = [str(int(v)) for v in grid.flatten()]
    ans, _ = isaac.lookup(ctx)
    p = _pred_count(ans)
    if p is not None:
        return p
    pn = isaac.predict_next(ctx)
    return _pred_count(pn["prediction"]) if pn else None


def enc_C_postag(isaac, grid, count):
    """Position-tagged cells in one sequence, count appended.
    Cell i carries its position: 'c{i}_{val}'."""
    flat = grid.flatten()
    toks = [f"c{i}_{int(v)}" for i, v in enumerate(flat)] + [f"count_{count}"]
    isaac.observe(toks)

def qry_C(isaac, grid):
    flat = grid.flatten()
    ctx = [f"c{i}_{int(v)}" for i, v in enumerate(flat)]
    ans, _ = isaac.lookup(ctx)
    p = _pred_count(ans)
    if p is not None:
        return p
    pn = isaac.predict_next(ctx)
    return _pred_count(pn["prediction"]) if pn else None


def enc_D_assoc(isaac, grid, count):
    """Associative: count is a successor of EVERY position-tagged cell.
    Each cell token accumulates doors to the counts it co-occurs with.
    This is the best shot at 'voting' toward the right count."""
    flat = grid.flatten()
    for i, v in enumerate(flat):
        isaac.observe([f"c{i}_{int(v)}", f"count_{count}"])

def qry_D(isaac, grid):
    flat = grid.flatten()
    ctx = [f"c{i}_{int(v)}" for i, v in enumerate(flat)]
    # predict_next is the pure voting mechanism — the right tool here
    pn = isaac.predict_next(ctx)
    if pn:
        p = _pred_count(pn["prediction"])
        if p is not None:
            return p
    ans, _ = isaac.lookup(ctx)
    return _pred_count(ans)


def enc_E_onbag(isaac, grid, count):
    """UPPER-BOUND / leaky baseline: present each ON pixel as a generic
    'on' token (positions discarded), then the count. This nearly hands
    Isaac the answer (input length == count). Included only to show the
    ceiling and prove the mechanism CAN bind when the signal is trivial."""
    n_on = int(grid.sum())
    toks = ["on"] * n_on + [f"count_{count}"] if n_on else ["off", f"count_{count}"]
    isaac.observe(toks)

def qry_E(isaac, grid):
    n_on = int(grid.sum())
    ctx = ["on"] * n_on if n_on else ["off"]
    ans, _ = isaac.lookup(ctx)
    p = _pred_count(ans)
    if p is not None:
        return p
    pn = isaac.predict_next(ctx)
    return _pred_count(pn["prediction"]) if pn else None


ENCODINGS = [
    ("A  literal (addendum sketch)", enc_A_literal, qry_A),
    ("B  flat grid + count",          enc_B_flat,    qry_B),
    ("C  position-tagged + count",    enc_C_postag,  qry_C),
    ("D  associative (cell->count)",  enc_D_assoc,   qry_D),
    ("E  on-bag [leaky upper bound]", enc_E_onbag,   qry_E),
]


def run_encoding(name, enc, qry, train, test):
    isaac = Isaac()
    for g, c in train:
        enc(isaac, g, c)
    isaac.consolidate()

    def score(dataset):
        ok = 0
        near = 0  # within +/-1, tells us if it's "sort of" counting
        got = 0
        for g, c in dataset:
            p = qry(isaac, g)
            if p is not None:
                got += 1
                if p == c:
                    ok += 1
                if abs(p - c) <= 1:
                    near += 1
        n = len(dataset)
        return ok / n, near / n, got / n

    tr_acc, tr_near, tr_got = score(train)
    te_acc, te_near, te_got = score(test)
    return {
        "name": name,
        "train_exact": tr_acc, "train_near": tr_near, "train_answered": tr_got,
        "test_exact": te_acc, "test_near": te_near, "test_answered": te_got,
    }


def main():
    # Disjoint train/test — test grids are guaranteed novel.
    all_grids = make_grids(400)
    train = all_grids[:250]
    test = all_grids[250:]

    top, base = majority_baseline(test)
    print("=" * 70)
    print("  MINIMUM VIABLE TEST — count pixels on a 3x3 grid")
    print("=" * 70)
    print(f"  train grids: {len(train)}   test grids (novel): {len(test)}")
    print(f"  majority-class baseline: always predict count={top}  "
          f"-> {base:.1%}")
    print(f"  (a real counter scores ~100%; 'learning' must clearly beat "
          f"{base:.0%})")
    print("=" * 70)
    print()
    header = (f"  {'encoding':<32} {'train':>7} {'TEST':>7} "
              f"{'test±1':>7} {'answ%':>6}")
    print(header)
    print("  " + "-" * 62)
    for name, enc, qry in ENCODINGS:
        r = run_encoding(name, enc, qry, train, test)
        flag = ""
        if r["test_exact"] > base + 0.10:
            flag = "  <-- beats baseline"
        print(f"  {r['name']:<32} {r['train_exact']:>6.0%} "
              f"{r['test_exact']:>6.0%} {r['test_near']:>6.0%} "
              f"{r['test_answered']:>5.0%}{flag}")
    print()
    print(f"  baseline to beat (TEST exact): {base:.0%}")
    print("  train = memorization,  TEST = generalization to novel grids")
    print("  test±1 = predicted within 1 of true count (partial structure)")


if __name__ == "__main__":
    main()
