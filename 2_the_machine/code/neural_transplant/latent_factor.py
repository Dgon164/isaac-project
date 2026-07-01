"""
LATENT FACTOR — the answer lives in a hidden variable that no observable carries.

The hidden factor flips the CORRELATION between X1 and X2:
  class 0: corr(X1,X2) = +0.8
  class 1: corr(X1,X2) = -0.8
But both classes have IDENTICAL marginals (mean 0, var 1 for X1 and X2). So no
single observable, and no first-order method (box, linear, kNN), can tell them
apart — the signal is purely metastructural: it's in the RELATIONSHIP, not the
values. Computing the second-order feature (the product = the correlation) makes
the latent visible. This is 'indirect associations / things not directly
observable that point toward the answer', as a clean test.
"""
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
LOW, HIGH = -7, 8
rng = np.random.default_rng(0)

n, rho, noise = 4000, 0.8, 6
y = rng.integers(0, 2, n)
X12 = np.zeros((n, 2))
for cls, s in [(0, +rho), (1, -rho)]:
    m = y == cls
    X12[m] = rng.multivariate_normal([0, 0], [[1, s], [s, 1]], m.sum())
X = np.concatenate([X12, rng.normal(0, 1, (n, noise))], 1)

print("=" * 60)
print("  THE TRAP: marginals identical, only the correlation differs")
print("=" * 60)
print(f"  X1 mean: class0 {X[y==0,0].mean():+.2f}  class1 {X[y==1,0].mean():+.2f}  (same)")
print(f"  X2 mean: class0 {X[y==0,1].mean():+.2f}  class1 {X[y==1,1].mean():+.2f}  (same)")
print(f"  corr(X1,X2): class0 {np.corrcoef(X[y==0,0],X[y==0,1])[0,1]:+.2f}  "
      f"class1 {np.corrcoef(X[y==1,0],X[y==1,1])[0,1]:+.2f}  <- the ONLY signal")

tr, te = slice(0, 3000), slice(3000, None)


def quantize(X, lo=None, hi=None):
    if lo is None: lo, hi = X.min(0), X.max(0)
    rng_ = np.where(hi - lo == 0, 1, hi - lo)
    return np.clip(np.round((X - lo) / rng_ * (HIGH - LOW) + LOW), LOW, HIGH), lo, hi

def boxacc(Xtr, ytr, Xte, yte):
    Qtr, lo, hi = quantize(Xtr); Qte, _, _ = quantize(Xte, lo, hi)
    labels = sorted(np.unique(ytr))
    B = {c: (np.percentile(Qtr[ytr == c], 1, 0) - 1.5,
             np.percentile(Qtr[ytr == c], 95, 0) + 1.5,
             np.median(Qtr[ytr == c], 0)) for c in labels}
    out = []
    for x in Qte:
        best, bc, bd = None, -1, 1e18
        for c, (l, h, md) in B.items():
            inr = (x >= l) & (x <= h); cnt = int(inr.sum())
            d = float(np.abs(x[inr] - md[inr]).sum()) if cnt else 1e18
            if cnt > bc or (cnt == bc and d < bd): bc, bd, best = cnt, d, c
        out.append(best)
    return (np.array(out) == yte).mean()


def aug(X):                                   # add centered pairwise products
    Xc = X - X.mean(0); d = X.shape[1]
    P = [Xc[:, a] * Xc[:, b] for a in range(d) for b in range(a + 1, d)]
    return np.concatenate([X, np.stack(P, 1)], 1)


print("\n  FIRST-ORDER methods on raw observables (should be ~chance 0.50):")
print(f"    box / crystal : {boxacc(X[tr],y[tr],X[te],y[te]):.3f}")
print(f"    linear (logreg): {LogisticRegression(max_iter=500).fit(X[tr],y[tr]).score(X[te],y[te]):.3f}")
print(f"    kNN-15        : {KNeighborsClassifier(15).fit(X[tr],y[tr]).score(X[te],y[te]):.3f}")

Xa = aug(X)
print("\n  + SECOND-ORDER (pairwise products = the correlations made visible):")
print(f"    box / crystal : {boxacc(Xa[tr],y[tr],Xa[te],y[te]):.3f}")
print(f"    linear (logreg): {LogisticRegression(max_iter=500).fit(Xa[tr],y[tr]).score(Xa[te],y[te]):.3f}")

prod = X[:, 0] * X[:, 1]
print(f"\n  the smoking gun — X1*X2 (the latent's shadow):")
print(f"    mean(X1*X2): class0 {prod[y==0].mean():+.2f}   class1 {prod[y==1].mean():+.2f}")
print("=" * 60)
print("  No value carried the answer; the RELATIONSHIP did. Compute the")
print("  second-order term and the hidden factor becomes separable. That's")
print("  metastructural / latent inference: infer the unseen from co-variation.")
