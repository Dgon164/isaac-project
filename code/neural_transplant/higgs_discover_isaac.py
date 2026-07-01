"""
HIGGS UNSUPERVISED STRUCTURE DISCOVERY — ISAAC ONLY. No sklearn learner anywhere.
The ONLY non-Isaac steps are (1) loading the CSV and (2) binning each number into
a glyph token -- that is his tokenization (defining what a node is, the allowed
pre-net op). EVERY prediction below is HIS matrix: observe -> compile -> the
matmul W_norm @ x. We measure how well HIS matrix predicts each feature from the
others (redundancy), then check unsupervised whether the features HE finds most
determined are the 7 known physicist-derived invariant masses. Labels (signal/
background) are never used. No tuning to flatter him -- one run, reported as-is.

Run:  PYTHONUTF8=1 python -u higgs_discover_isaac.py
"""
import sys, time
sys.path.insert(0, "..")
import numpy as np
from sklearn.datasets import fetch_openml          # data load ONLY (I/O, not cognition)
from isaac import Isaac

BINS, NTR, NTE, RORD, MAXCTX = 6, 5000, 400, 3, 4


def load_named():
    d = fetch_openml(data_id=23512, as_frame=False)
    X = np.asarray(d.data, dtype=np.float32); ok = ~np.isnan(X).any(1)
    return X[ok], list(d.feature_names)


def glyphs_of(row, edges):
    return [f"{j}_{int(np.digitize(v, edges[j]))}" for j, v in enumerate(row)]


def main():
    X, names = load_named()
    Xtr, Xte = X[:NTR], X[NTR:NTR + NTE]
    n = X.shape[1]
    edges = [np.quantile(Xtr[:, j], np.linspace(0, 1, BINS + 1)[1:-1]) for j in range(n)]
    hi = list(range(n - 7, n))                       # known derived = last 7 (validation only)
    Gtr = [glyphs_of(r, edges) for r in Xtr]
    Gte = [glyphs_of(r, edges) for r in Xte]

    # --- HIS processing: feed events (no labels) in a few orderings; compile his matrix ---
    isaac = Isaac()
    rng = np.random.default_rng(0)
    print(f"feeding {NTR} events x {RORD} orderings into his matrix...")
    t = time.time()
    for g in Gtr:
        for _ in range(RORD):
            isaac.observe([g[k] for k in rng.permutation(n)])
    isaac.compile(max_context=MAXCTX)
    c = isaac._compiled; W = c["W_norm"]; didx = c["didx"]
    print(f"  his matrix: {W.shape}, {len(c['frames'])} frames, {time.time()-t:.0f}s")

    # delta indices for each feature's glyphs (what HE could predict for feature j)
    jdelta = {j: [didx[d] for d in c["deltas"] if d.startswith(f"{j}_")] for j in range(n)}

    def his_predict_bin(ctx_tokens, j):
        """HIS matmul: encode context -> W_norm @ x -> argmax restricted to feature j."""
        x = isaac._encode(ctx_tokens)
        if x is None: return None
        nz = np.nonzero(x)[0]
        if len(nz) == 0 or not jdelta[j]: return None
        y = W[np.ix_(jdelta[j], nz)] @ x[nz]            # sparse, his matrix
        return jdelta[j][int(y.argmax())]

    # --- how determined is each feature by the others, as HE predicts it ---
    print("measuring his predictability of each feature from the rest...")
    pred_acc = np.full(n, np.nan); base_acc = np.zeros(n)
    for j in range(n):
        # his baseline: most-frequent glyph of j among training (his prior)
        gj = [g[j] for g in Gtr]
        base = max(set(gj), key=gj.count); base_acc[j] = np.mean([ge[j] == base for ge in Gte])
        hits = tot = 0
        for g in Gte:
            true = g[j]
            for _ in range(2):                          # 2 orderings of the OTHER features
                ctx = [g[k] for k in rng.permutation(n) if k != j]
                p = his_predict_bin(ctx, j)
                if p is not None:
                    tot += 1; hits += (c["deltas"][p] == true)
        pred_acc[j] = hits / tot if tot else np.nan

    lift = pred_acc - base_acc                            # how much HIS matrix beats its own prior
    order = np.argsort(-np.where(np.isnan(lift), -9, lift))
    print("=" * 70)
    print("  ISAAC's view: how determined each feature is by the others")
    print("  (his matmul prediction vs his own prior; high lift = a derived feature)")
    print("=" * 70)
    print(f"  {'rank':>4} {'feature':<26}{'his_acc':>8}{'prior':>7}{'lift':>7}")
    for r, j in enumerate(order):
        tag = "  <-- KNOWN derived" if j in hi else ""
        print(f"  {r+1:>4} {names[j]:<26}{pred_acc[j]:>8.3f}{base_acc[j]:>7.3f}{lift[j]:>7.3f}{tag}")

    topk = set(order[:7].tolist()); hit = len(topk & set(hi))
    print("\n  VALIDATION (signal/background labels never used):")
    print(f"  of the 7 features HE finds most determined, {hit}/7 ARE the known")
    print(f"  derived invariant masses. (top-7 he chose: {[names[j] for j in order[:7]]})")
    print("\n  This is Isaac's matrix doing the discovery. Reported as-is.")


if __name__ == "__main__":
    main()
