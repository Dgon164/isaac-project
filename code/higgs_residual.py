"""
The reframe: don't hunt the Higgs — model EVERYTHING ELSE, the Higgs is the residual.

For each class, model its FULL internal structure: predict every feature from all
the others, at three levels of completeness. An event belongs to the class whose
structure it best fits (smallest residual). The principle being tested: the MORE
complete the structure model, the better the signal separates.

  level 0  box      : expected = class median            (no relationships)
  level 1  linear   : expected = linear f(other features) (linear structure)
  level 2  nonlinear: expected = RF f(other features)     (full nonlinear structure)

Also checks the extracted structure is REAL: how well each model predicts the
known derived (invariant-mass) features it should be able to reconstruct.

Run:  python higgs_residual.py
"""
import numpy as np, time, warnings; warnings.filterwarnings("ignore")
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier

d = fetch_openml(data_id=23512, as_frame=False)
X = np.asarray(d.data, np.float32); names = list(d.feature_names)
y = np.asarray(d.target); y = (y == "1").astype(int) if y.dtype == object else (y.astype(float) > .5).astype(int)
ok = ~np.isnan(X).any(1); X, y = X[ok], y[ok]
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=0, stratify=y)
Xtr, ytr = Xtr[:8000], ytr[:8000]; Xte, yte = Xte[:3000], yte[:3000]
s = StandardScaler().fit(Xtr); Xtr, Xte = s.transform(Xtr), s.transform(Xte)
n = X.shape[1]; cls = [0, 1]

logi = (LogisticRegression(max_iter=500).fit(Xtr, ytr).predict(Xte) == yte).mean()
rf_d = (RandomForestClassifier(200, n_jobs=-1, random_state=0).fit(Xtr, ytr).predict(Xte) == yte).mean()


def residual_classify(model_fn):
    """model_fn(Xc, j) -> (predict_fn, train_resid_std). Classify test by per-class residual."""
    R = np.empty((2, len(Xte), n)); r2 = []
    for ci, c in enumerate(cls):
        Xc = Xtr[ytr == c]
        for j in range(n):
            o = [k for k in range(n) if k != j]
            pred, sca, fit_r2 = model_fn(Xc[:, o], Xc[:, j], Xte[:, o])
            R[ci, :, j] = np.abs(Xte[:, j] - pred) / sca
            if ci == 0 and j >= n - 7: r2.append(fit_r2)        # high-level feats
    won = R.argmin(0)
    votes = np.stack([(won == ci).sum(1) for ci in range(2)], 1)
    acc_count = (np.array(cls)[votes.argmax(1)] == yte).mean()
    acc_total = (np.array(cls)[R.sum(2).argmin(0)] == yte).mean()
    return acc_count, acc_total, np.mean(r2)


def m_box(Xo_tr, yj, Xo_te):
    med = np.median(yj); return np.full(len(Xo_te), med), np.std(yj) + 1e-6, 0.0

def m_lin(Xo_tr, yj, Xo_te):
    m = Ridge(1.0).fit(Xo_tr, yj); res = yj - m.predict(Xo_tr)
    r2 = 1 - res.var() / (yj.var() + 1e-9)
    return m.predict(Xo_te), np.std(res) + 1e-6, r2

def m_rf(Xo_tr, yj, Xo_te):
    m = RandomForestRegressor(40, max_depth=10, n_jobs=-1, random_state=0).fit(Xo_tr, yj)
    res = yj - m.predict(Xo_tr); r2 = 1 - res.var() / (yj.var() + 1e-9)
    return m.predict(Xo_te), np.std(res) + 1e-6, r2


print("=" * 70)
print("  MODEL EVERYTHING ELSE — the Higgs is the residual (completeness ladder)")
print("=" * 70)
print(f"  {'structure model':<26}{'count-acc':>11}{'total-acc':>11}{'hi-feat R2':>12}")
print("  " + "-" * 60)
for name, fn in [("level 0: box (median)", m_box), ("level 1: linear", m_lin),
                 ("level 2: nonlinear (RF)", m_rf)]:
    t = time.time(); ac, at, r2 = residual_classify(fn)
    print(f"  {name:<26}{ac:>11.3f}{at:>11.3f}{r2:>12.3f}   ({time.time()-t:.0f}s)")
print("  " + "-" * 60)
print(f"  reference: logistic {logi:.3f} | discriminative RF {rf_d:.3f} | chance 0.53")
print("  READ: 'hi-feat R2' = how well the model reconstructs the known invariant-mass")
print("  features (is the extracted structure REAL?). As structure completeness rises,")
print("  does discrimination rise? That is the reframe, tested.")
