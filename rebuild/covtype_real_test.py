"""
REAL-DATA TEST 1 — covtype (581,012 rows, 54 features, 7 classes).

The recorded wall (SESSION_HANDOFF_2026-06-22): axis-aligned boxes cap ~0.62
on covtype while a net reaches 0.82 — "no knob closes it". Head-to-head:
the same BoxDoors mechanism vs the rebuilt ProximityDoors, full dataset.
"""
import time
import numpy as np
from sklearn.datasets import fetch_covtype          # data loading ONLY
from doors_proximity import BoxDoors, ProximityDoors

rng = np.random.default_rng(3)


class ProximityDoorsCC:
    """Class-conditional variant: each class gets its OWN null-gated basis
    (the rotation where that class's structure goes axis-aligned), doors are
    per-dim densities in that basis (bin prob / bin width), plus log prior.
    Still observe + matmul: no fitted geometry anywhere."""

    def __init__(self, bins=32):
        self.bins = bins

    def fit(self, X, y):
        self.classes = np.unique(y)
        self.mu, self.sd = X.mean(0), X.std(0) + 1e-12
        Z = (X - self.mu) / self.sd
        self.R, self.edges, self.logdens, self.logprior = {}, {}, {}, {}
        self.lo, self.hi, self.scale, self.tail = {}, {}, {}, {}
        for c in self.classes:
            Zc = Z[y == c]
            n, d = Zc.shape
            C = np.corrcoef(Zc, rowvar=False)
            C = np.nan_to_num(C, nan=0.0)
            gate = np.abs(C) >= 3.0 / np.sqrt(n)
            np.fill_diagonal(gate, True)
            w, V = np.linalg.eigh(np.where(gate, C, 0.0))
            order = np.argsort(-w, kind="stable")
            R = V[:, order]
            U = Zc @ R
            qs = np.linspace(0, 100, self.bins + 1)[1:-1]
            edges = np.stack([np.percentile(U[:, j], qs) for j in range(d)])
            lo = np.percentile(U, 0.5, axis=0)
            hi = np.percentile(U, 99.5, axis=0)
            full = np.column_stack([lo, edges, hi])          # for bin widths
            width = np.diff(full, axis=1)
            scale = (hi - lo)[:, None]
            # discrete/constant coordinates carry probability MASS, not density:
            # a zero-width bin must not become an infinite-density spike.
            width = np.where(scale < 1e-9, 1.0,
                             np.maximum(width, scale / (self.bins * 4)))
            ld = np.empty((d, self.bins))
            for j in range(d):
                idx = np.searchsorted(edges[j], U[:, j])
                cnt = np.bincount(idx, minlength=self.bins).astype(float)
                p = (cnt + 1.0) / (cnt.sum() + self.bins)
                ld[j] = np.log(p) - np.log(width[j])
            scale_eff = np.where(scale[:, 0] < 1e-9, 1.0, scale[:, 0])
            self.R[c], self.edges[c], self.logdens[c] = R, edges, ld
            # outside the class's own support: Laplace-floor density plus a
            # distance penalty — being far from a class's range is evidence
            # AGAINST it (this is what hard-clamped bins gave away for free)
            self.lo[c], self.hi[c], self.scale[c] = lo, hi, scale_eff
            self.tail[c] = np.log(1.0 / (n + self.bins)) - np.log(scale_eff)
            self.logprior[c] = np.log(n / len(y))
        return self

    def predict(self, X):
        Z = (X - self.mu) / self.sd
        scores = np.empty((len(X), len(self.classes)))
        for k, c in enumerate(self.classes):
            U = Z @ self.R[c]
            s = np.full(len(X), self.logprior[c])
            for j in range(U.shape[1]):
                u = U[:, j]
                idx = np.searchsorted(self.edges[c][j], u)
                inside = self.logdens[c][j][idx]
                lo, hi, sc = self.lo[c][j], self.hi[c][j], self.scale[c][j]
                dist = np.maximum(lo - u, u - hi)
                outside = self.tail[c][j] - dist / (0.25 * sc)
                s += np.where(dist > 0, outside, inside)
            scores[:, k] = s
        return self.classes[np.argmax(scores, axis=1)]


def main():
    d = fetch_covtype()
    X, y = d.data.astype(np.float64), d.target.astype(int)
    idx = rng.permutation(len(y))
    k = int(0.7 * len(y))
    Xtr, ytr, Xte, yte = X[idx[:k]], y[idx[:k]], X[idx[k:]], y[idx[k:]]
    print(f"covtype: train {len(ytr):,}  test {len(yte):,}")

    t0 = time.time()
    box = BoxDoors().fit(Xtr, ytr)
    pb = np.concatenate([box.predict(Xte[i:i + 100_000])
                         for i in range(0, len(yte), 100_000)])
    acc_box = float((pb == yte).mean())
    print(f"BoxDoors (old):            {acc_box*100:5.2f}% correct   "
          f"[{time.time()-t0:.0f}s]   (recorded box ceiling ~62%, net 82%)")

    for bins in (12, 32):
        t0 = time.time()
        prx = ProximityDoors(bins=bins).fit(Xtr, ytr)
        pp = np.concatenate([prx.predict(Xte[i:i + 100_000])
                             for i in range(0, len(yte), 100_000)])
        acc = float((pp == yte).mean())
        print(f"ProximityDoors bins={bins:2d}:    {acc*100:5.2f}% correct   "
              f"[{time.time()-t0:.0f}s]")

    for bins in (32, 64):
        t0 = time.time()
        cc = ProximityDoorsCC(bins=bins).fit(Xtr, ytr)
        pc = np.concatenate([cc.predict(Xte[i:i + 100_000])
                             for i in range(0, len(yte), 100_000)])
        acc = float((pc == yte).mean())
        print(f"ProximityDoorsCC bins={bins:2d}:  {acc*100:5.2f}% correct   "
              f"[{time.time()-t0:.0f}s]   (per-class null-gated basis + priors)")


if __name__ == "__main__":
    main()
