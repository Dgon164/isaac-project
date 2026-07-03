"""
COVTYPE — door-weighted exemplars (the captured road, sharpened) + the
row-index leakage control.

Rebuild (2026-07-03) of the door-weighted variant whose numbers (94.4%
door-weighted k=1 over all train exemplars; 79.1% from the row index alone)
were recorded on 2026-07-02 but never committed. covtype_compounds.py holds
the committed baseline (plain 5-NN over 200k exemplars: 90.0%).

The weight is the DIFFERENTIA statistic, learned and readable: per feature,
the mean pairwise total-variation distance between the class-conditional
quantile-bin distributions — how much the classes actually disagree about
this door. No gradient, no net; one pass over the training half.

The control: covtype rows are ordered by geography. k=1 on the ORIGINAL ROW
INDEX alone — zero terrain features — measures how much any covtype benchmark
reads the map instead of the terrain.
"""
import os
import sys
import time
import numpy as np
from sklearn.datasets import fetch_covtype          # data loading only

rng = np.random.default_rng(3)
N_BINS = 16
N_TEST = 20_000       # same evaluation protocol as covtype_compounds.py


def differentia_weights(X, y):
    """Per-feature mean pairwise TV distance between class-conditional
    bin distributions. Readable: one number per door, in [0, 1]."""
    classes = np.unique(y)
    d = X.shape[1]
    W = np.zeros(d)
    for j in range(d):
        col = X[:, j]
        qs = np.percentile(col, np.linspace(0, 100, N_BINS + 1)[1:-1])
        B = np.searchsorted(qs, col)
        dists = np.stack([np.bincount(B[y == c], minlength=N_BINS) /
                          max(1, (y == c).sum()) for c in classes])
        tv = [0.5 * np.abs(dists[a] - dists[b]).sum()
              for a in range(len(classes)) for b in range(a + 1, len(classes))]
        W[j] = np.mean(tv)
    return W


def main():
    d = fetch_covtype()
    X, y = d.data.astype(np.float64), d.target.astype(int)
    idx = rng.permutation(len(y))
    k = int(0.7 * len(y))
    tr, te = idx[:k], idx[k:]
    Xtr, ytr, Xte, yte = X[tr], y[tr], X[te], y[te]
    print(f"covtype: train {len(ytr):,} test {len(yte):,} "
          f"(evaluating on the first {N_TEST:,} test rows)")

    # ---- learned door weights (readable)
    t0 = time.time()
    W = differentia_weights(Xtr, ytr)
    names = list(d.feature_names) if hasattr(d, "feature_names") else \
        [f"f{j}" for j in range(X.shape[1])]
    top = np.argsort(-W)[:6]
    print(f"door weights learned [{time.time()-t0:.0f}s] — top doors:")
    for j in top:
        print(f"   {names[j][:32]:32s} {W[j]:.2f}")

    # ---- door-weighted k=1 over ALL train exemplars
    t0 = time.time()
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9
    scale = (W / sd).astype(np.float32)
    A = ((Xtr - mu) * scale).astype(np.float32)
    B = ((Xte[:N_TEST] - mu) * scale).astype(np.float32)
    a2 = (A ** 2).sum(1)
    hits = 0
    for i in range(0, N_TEST, 500):
        chunk = B[i:i + 500]
        d2 = (chunk ** 2).sum(1)[:, None] - 2 * chunk @ A.T + a2[None, :]
        nn = d2.argmin(1)
        hits += (ytr[nn] == yte[i:i + len(chunk)]).sum()
    acc = hits / N_TEST
    print(f"door-weighted exemplars (k=1, {len(ytr):,} exemplars): "
          f"{acc*100:5.2f}%  [{time.time()-t0:.0f}s]")

    # ---- the leakage control: original row index ALONE
    t0 = time.time()
    order = np.argsort(tr)
    tr_sorted = tr[order]
    pos = np.searchsorted(tr_sorted, te[:N_TEST])
    pos = np.clip(pos, 0, len(tr_sorted) - 1)
    left = np.clip(pos - 1, 0, len(tr_sorted) - 1)
    use_left = (np.abs(tr_sorted[left] - te[:N_TEST])
                < np.abs(tr_sorted[pos] - te[:N_TEST]))
    nn_idx = np.where(use_left, tr_sorted[left], tr_sorted[pos])
    acc_row = (y[nn_idx] == yte[:N_TEST]).mean()
    print(f"row-index ALONE (k=1, zero terrain features): "
          f"{acc_row*100:5.2f}%  [{time.time()-t0:.0f}s]")

    print("\nACCOUNTING (captured tier, sharpened):")
    print(f"  committed baseline (plain 5-NN, 200k):  90.0%  "
          f"(covtype_compounds.py)")
    print(f"  door-weighted k=1, all exemplars:      {acc*100:5.1f}%")
    print(f"  spatial leakage floor (row index):     {acc_row*100:5.1f}%")


if __name__ == "__main__":
    main()
