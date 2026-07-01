"""
Box -> Function, the upgrade tested in isolation, on HIGGS (where the box died).

ONLY ONE THING changes between the two: where each dimension's EXPECTED value
comes from.
  box        : expected(x_j) = class median            (a CONSTANT — a result)
  functional : expected(x_j) = f_c,j(x_other dims)     (a FUNCTION — a mechanism)
Recognition is identical in both: residual = |observed - expected|, normalised
per (class,dim); classify by the SAME presence-primary matcher (count of dims a
class predicts best) and a total-residual tiebreak. The function is fit by
least squares (Ridge / Ridge-on-pairwise-products) — that fits the form's
PARAMETERS; the DECISION is the residual matcher, unchanged.

If functional >> box, the win is entirely "predict the value from the others'
relationships" vs "store the average value" — mechanism vs result, per dimension.

Run:  python higgs_functional.py
"""
import numpy as np, warnings; warnings.filterwarnings("ignore")
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.ensemble import RandomForestClassifier

d = fetch_openml(data_id=23512, as_frame=False)
X = np.asarray(d.data, np.float32); y = np.asarray(d.target)
y = (y == "1").astype(int) if y.dtype == object else (y.astype(float) > 0.5).astype(int)
ok = ~np.isnan(X).any(1); X, y = X[ok], y[ok]
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=0, stratify=y)
Xtr, ytr = Xtr[:12000], ytr[:12000]; Xte, yte = Xte[:4000], yte[:4000]
sc = StandardScaler().fit(Xtr); Xtr, Xte = sc.transform(Xtr), sc.transform(Xte)
n = X.shape[1]; cls = [0, 1]

logi = (LogisticRegression(max_iter=500).fit(Xtr, ytr).predict(Xte) == yte).mean()
rf = (RandomForestClassifier(200, n_jobs=-1, random_state=0).fit(Xtr, ytr).predict(Xte) == yte).mean()


def box_resid():                                   # expected = class median (constant)
    R = np.empty((2, len(Xte), n))
    for ci, c in enumerate(cls):
        Xc = Xtr[ytr == c]
        med = np.median(Xc, 0); sca = np.std(Xc, 0) + 1e-6
        R[ci] = np.abs(Xte - med) / sca
    return R


def func_resid(degree=1):                          # expected = f(other dims), fit by least squares
    R = np.empty((2, len(Xte), n))
    for ci, c in enumerate(cls):
        Xc = Xtr[ytr == c]
        for j in range(n):
            o = [k for k in range(n) if k != j]
            Xo_tr, Xo_te = Xc[:, o], Xte[:, o]
            if degree == 2:
                pf = PolynomialFeatures(2, include_bias=False)
                Xo_tr = pf.fit_transform(Xo_tr); Xo_te = pf.transform(Xo_te)
            m = Ridge(alpha=1.0).fit(Xo_tr, Xc[:, j])
            sca = np.std(Xc[:, j] - m.predict(Xo_tr)) + 1e-6      # the variance function
            R[ci, :, j] = np.abs(Xte[:, j] - m.predict(Xo_te)) / sca
    return R


def classify(R):                                   # SAME matcher for box and functional
    won = R.argmin(0)                              # (N,n): which class predicts each dim best
    votes = np.stack([(won == ci).sum(1) for ci in range(2)], 1)
    pred_count = np.array(cls)[votes.argmax(1)]    # presence-primary (count of dims won)
    pred_total = np.array(cls)[R.sum(2).argmin(0)]  # total-residual (distance)
    return (pred_count == yte).mean(), (pred_total == yte).mean()


print("=" * 64)
print("  HIGGS — expected value: CONSTANT median (box) vs FUNCTION of others")
print("=" * 64)
print(f"  {'method':<30}{'count-match':>12}{'total-resid':>13}")
print("  " + "-" * 56)
bc, bt = classify(box_resid())
print(f"  {'box (expected = median)':<30}{bc:>12.3f}{bt:>13.3f}")
f1c, f1t = classify(func_resid(1))
print(f"  {'functional (linear f)':<30}{f1c:>12.3f}{f1t:>13.3f}")
f2c, f2t = classify(func_resid(2))
print(f"  {'functional (+pairwise products)':<30}{f2c:>12.3f}{f2t:>13.3f}")
print("  " + "-" * 56)
print(f"  reference: logistic {logi:.3f} | RF {rf:.3f} | box(prev session) ~0.52 | chance 0.53")
print("  READ: only the expected-value source changed (median -> function). If")
print("  functional >> box, the gain is mechanism-per-dim vs stored-average-per-dim.")
