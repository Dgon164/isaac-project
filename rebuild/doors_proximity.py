"""
REBUILD A — Doors: proximity (observe + matmul) vs boxes (fit geometry).

OLD (broken) mechanism, faithful to neural_transplant/range_classifier METHODS.md:
  per class, per dim: percentile box [p5 - margin, p95 + margin], margin = 0.1*(p95-p5).
  Score = count of dims in range; ties -> distance to median. Overlap = interval intersection.
  Known ceiling: axis-aligned boxes cap ~0.62 on diagonal data where nets hit 0.82
  (SESSION_HANDOFF_2026-06-22) and hard membership loses gradation.

NEW mechanism (the cure already recorded in the box->matrix finding, 0.922 > 0.900):
  1. Standardize, rotate to the basis where structure goes axis-aligned (PCA — basis-first decode).
  2. Doors = OBSERVED per-class per-dim distributions (quantile-binned histograms). No fitting.
  3. Score = summed log-likelihood, computed as one matmul. Soft membership everywhere.
  Doors carry range AND density: overlap is graded (sum of min densities), never a hard 0/1.

Tests (audit standard 2.2):
  T1 box-friendly data      -> parity (both work; rebuild loses nothing)
  T2 box-hostile diagonal   -> box caps, proximity doors do not (THE head-to-head)
  T3 graded overlap         -> strong / remote / none must be three distinguishable levels
  T4 representation invariance -> affine re-encoding (units, offsets, column order)
                                  must not change any verdict
Integrity rule: numpy only; every decision made by the mechanism under test.
"""
import numpy as np

rng = np.random.default_rng(7)


# ---------------------------------------------------------------- OLD: boxes
class BoxDoors:
    def fit(self, X, y):
        self.classes = np.unique(y)
        self.lo, self.hi, self.med = {}, {}, {}
        for c in self.classes:
            Xc = X[y == c]
            p5, p95 = np.percentile(Xc, 5, axis=0), np.percentile(Xc, 95, axis=0)
            m = 0.1 * (p95 - p5)
            self.lo[c], self.hi[c] = p5 - m, p95 + m
            self.med[c] = np.median(Xc, axis=0)
        return self

    def predict(self, X):
        counts = np.stack([((X >= self.lo[c]) & (X <= self.hi[c])).sum(1)
                           for c in self.classes], axis=1)
        dist = np.stack([np.abs(X - self.med[c]).sum(1) for c in self.classes], axis=1)
        # highest in-range count wins; ties -> nearer median
        best = counts.max(1, keepdims=True)
        masked = np.where(counts == best, dist, np.inf)
        return self.classes[np.argmin(masked, axis=1)]

    def overlap(self, a, b):
        """Graded connection between two class door-profiles: joint box overlap
        (product of per-dim interval IoU — the box IS the joint region)."""
        lo1, hi1, lo2, hi2 = self.lo[a], self.hi[a], self.lo[b], self.hi[b]
        inter = np.maximum(0.0, np.minimum(hi1, hi2) - np.maximum(lo1, lo2))
        union = np.maximum(hi1, hi2) - np.minimum(lo1, lo2)
        return float(np.prod(inter / np.where(union > 0, union, 1.0)))


# --------------------------------------------- NEW: basis-first proximity doors
class ProximityDoors:
    def __init__(self, bins=12):
        self.bins = bins

    def _transform(self, X):
        return ((X - self.mu) / self.sd) @ self.R

    def fit(self, X, y):
        self.classes = np.unique(y)
        self.mu, self.sd = X.mean(0), X.std(0) + 1e-12
        Z = (X - self.mu) / self.sd
        C = np.corrcoef(Z, rowvar=False)
        # null-gate the basis: only rotate along correlations that beat the
        # sampling null (~3/sqrt(n)); otherwise the eigenvectors of a
        # near-identity matrix are noise-driven arbitrary rotations.
        gate = np.abs(C) >= 3.0 / np.sqrt(len(Z))
        np.fill_diagonal(gate, True)
        w, V = np.linalg.eigh(np.where(gate, C, 0.0))
        order = np.argsort(-w, kind="stable")
        self.R = V[:, order] * np.sign(V[np.abs(V[:, order]).argmax(0), order])
        Z = Z @ self.R
        d = Z.shape[1]
        qs = np.linspace(0, 100, self.bins + 1)[1:-1]
        self.edges = np.stack([np.percentile(Z[:, j], qs) for j in range(d)])
        self.P = np.zeros((len(self.classes), d, self.bins))   # observed densities (doors)
        for i, c in enumerate(self.classes):
            Zc = Z[y == c]
            for j in range(d):
                idx = np.searchsorted(self.edges[j], Zc[:, j])
                cnt = np.bincount(idx, minlength=self.bins).astype(float)
                self.P[i, j] = (cnt + 1.0) / (cnt.sum() + self.bins)   # Laplace smoothing
        self.L = np.log(self.P).reshape(len(self.classes), -1)         # matmul-ready
        return self

    def _onehot(self, X):
        Z = self._transform(X)
        n, d = Z.shape
        H = np.zeros((n, d * self.bins))
        for j in range(d):
            idx = np.searchsorted(self.edges[j], Z[:, j])
            H[np.arange(n), j * self.bins + idx] = 1.0
        return H

    def predict(self, X):
        scores = self._onehot(X) @ self.L.T        # THE decision: one matmul
        return self.classes[np.argmax(scores, axis=1)]

    def overlap(self, a, b):
        """Graded connection: joint density overlap — product across dims of the
        per-dim overlap coefficient (sum of min densities). Never a hard 0."""
        ia, ib = list(self.classes).index(a), list(self.classes).index(b)
        per_dim = np.minimum(self.P[ia], self.P[ib]).sum(-1)
        return float(np.exp(np.log(per_dim + 1e-300).sum()))


# ------------------------------------------------------------------ datasets
def blobs(n=600):
    """T1: box-friendly — axis-aligned Gaussian blobs, 4 classes, 6-D."""
    centers = np.array([[0, 0, 0, 0, 0, 0], [4, 0, 0, 4, 0, 0],
                        [0, 4, 0, 0, 4, 0], [4, 4, 0, 0, 0, 4]], float)
    X = np.vstack([rng.normal(c, 0.8, (n // 4, 6)) for c in centers])
    y = np.repeat(np.arange(4), n // 4)
    return X, y


def diagonal(n=1200):
    """T2: box-hostile — two classes separated along the diagonal, elongated across it.
    Axis-aligned marginals overlap heavily; the structure lives in a rotated basis."""
    u = np.array([1.0, 1.0]) / np.sqrt(2)     # between-class direction
    v = np.array([1.0, -1.0]) / np.sqrt(2)    # within-class (long) direction
    half = n // 2
    A = (-1.5 * u) + rng.normal(0, 0.3, (half, 1)) * u + rng.normal(0, 3.0, (half, 1)) * v
    B = (+1.5 * u) + rng.normal(0, 0.3, (half, 1)) * u + rng.normal(0, 3.0, (half, 1)) * v
    X = np.vstack([A, B])
    X = np.hstack([X, rng.normal(0, 1.0, (n, 4))])        # 4 pure-noise dims
    y = np.repeat([0, 1], half)
    return X, y


def graded(n=900):
    """T3: three entity classes at known distances from class 0:
    d=1.0 (strongly connected), d=3.5 (remotely connected), d=12 (not connected)."""
    c = np.zeros((4, 6))
    c[1, 0], c[2, 0], c[3, 0] = 1.0, 3.5, 12.0
    X = np.vstack([rng.normal(ci, 1.0, (n // 4, 6)) for ci in c])
    y = np.repeat(np.arange(4), n // 4)
    return X, y


def split(X, y, frac=0.5):
    idx = rng.permutation(len(y))
    k = int(len(y) * frac)
    tr, te = idx[:k], idx[k:]
    return X[tr], y[tr], X[te], y[te]


def acc(model, Xtr, ytr, Xte, yte):
    return float((model.fit(Xtr, ytr).predict(Xte) == yte).mean())


# --------------------------------------------------------------------- tests
def main():
    print("=" * 72)
    print("REBUILD A — proximity doors (observe+matmul, basis-first) vs boxes")
    print("=" * 72)

    # T1 parity on box-friendly data
    Xtr, ytr, Xte, yte = split(*blobs())
    a_box, a_prx = acc(BoxDoors(), Xtr, ytr, Xte, yte), acc(ProximityDoors(), Xtr, ytr, Xte, yte)
    print(f"\nT1 box-friendly blobs      box {a_box*100:5.1f}% correct   "
          f"proximity {a_prx*100:5.1f}% correct")
    t1 = a_prx >= a_box - 0.02

    # T2 the ceiling: diagonal data
    Xtr, ytr, Xte, yte = split(*diagonal())
    b_box, b_prx = acc(BoxDoors(), Xtr, ytr, Xte, yte), acc(ProximityDoors(), Xtr, ytr, Xte, yte)
    print(f"T2 diagonal (box-hostile)  box {b_box*100:5.1f}% correct   "
          f"proximity {b_prx*100:5.1f}% correct")
    t2 = (b_prx >= 0.90) and (b_prx - b_box >= 0.10)

    # T3 graded overlap: strong / remote / none must be three separated levels
    X, y = graded()
    for name, M in [("box", BoxDoors()), ("proximity", ProximityDoors())]:
        M.fit(X, y)
        s, r, n0 = M.overlap(0, 1), M.overlap(0, 2), M.overlap(0, 3)
        three_way = (s > r * 1.5) and (r > n0 * 1.5)
        print(f"T3 graded overlap [{name:9s}] strong {s:.3f}  remote {r:.3f}  "
              f"none {n0:.3f}   three-way distinguishable: {three_way}")
        if name == "box":
            t3_box = three_way
        else:
            t3 = three_way

    # T4 representation invariance: affine re-encode + column permutation
    X, y = diagonal()
    Xtr, ytr, Xte, yte = split(X, y)
    scale = np.array([1000.0, 0.001, 5.0, 1.0, 250.0, 0.04])
    shift = np.array([-5.0, 3.0, 0.0, 100.0, -0.7, 2.2])
    perm = np.array([3, 0, 5, 1, 4, 2])
    enc = lambda A: (A * scale + shift)[:, perm]
    inv = {}
    for name, cls in [("box", BoxDoors), ("proximity", ProximityDoors)]:
        p1 = cls().fit(Xtr, ytr).predict(Xte)
        p2 = cls().fit(enc(Xtr), ytr).predict(enc(Xte))
        inv[name] = float((p1 == p2).mean())
        print(f"T4 invariance     [{name:9s}] verdicts identical after re-encoding: "
              f"{inv[name]*100:.1f}%")
    t4 = inv["proximity"] == 1.0

    print("-" * 72)
    verdict = t1 and t2 and t3 and t4
    print(f"T1 parity: {t1}   T2 beats ceiling: {t2}   T3 graded: {t3} "
          f"(box graded: {t3_box})   T4 invariant: {t4}")
    print(f"REBUILD A VERDICT: {'WORKS' if verdict else 'BROKEN'}")
    return verdict


if __name__ == "__main__":
    main()
