"""
Extract the input->output functional associations: WHICH variables and WHICH
interactions drive the decision, with their weights.

Method (the section-5.8 idea, aimed at the OUTPUT instead of per-dimension):
build an interaction basis -- each variable x_i, each square x_i^2, each pairwise
product x_i*x_j -- and sparse-regress (L1) the label onto it. The surviving terms
*name* the functional associations; their coefficients are the contributions.

Test 1: a synthetic with PLANTED interactions -> does it recover them?
Test 2: HIGGS -> what does it find, and how much of the signal is in nameable
        pairwise interactions vs deeper structure?

Run:  python interaction_extract.py
"""
import numpy as np, warnings; warnings.filterwarnings("ignore")
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier


def expand(X, names):
    cols = [X, X**2]; cn = list(names) + [f"{n}^2" for n in names]
    n = X.shape[1]; pr = []
    for i in range(n):
        for j in range(i+1, n):
            pr.append(X[:, i]*X[:, j]); cn.append(f"{names[i]}*{names[j]}")
    return np.column_stack(cols + [np.column_stack(pr)]), cn


def extract(Xtr, ytr, Xte, yte, names, C, topk, title):
    Etr, cn = expand(Xtr, names); Ete, _ = expand(Xte, names)
    sc = StandardScaler().fit(Etr); Etr, Ete = sc.transform(Etr), sc.transform(Ete)
    clf = LogisticRegression(penalty="l1", solver="saga", C=C, max_iter=3000).fit(Etr, ytr)
    w = clf.coef_[0]; acc = (clf.predict(Ete) == yte).mean(); nz = int((w != 0).sum())
    order = np.argsort(-np.abs(w))
    print(f"\n  {title}")
    print(f"    accuracy {acc:.3f}   ({nz} of {len(cn)} terms selected)")
    print(f"    top contributing functional terms (variable / interaction):")
    for idx in order[:topk]:
        if w[idx] != 0:
            print(f"       {w[idx]:+.2f}  {cn[idx]}")
    return acc


# ---- Test 1: synthetic with planted interactions ----
rng = np.random.default_rng(0)
N, P = 6000, 10
Xs = rng.normal(0, 1, (N, P))
logit = Xs[:, 0]*Xs[:, 1] + 0.8*Xs[:, 2]**2 - 1.2*Xs[:, 3]      # planted structure
ys = (logit + rng.normal(0, 0.3, N) > 0).astype(int)
snames = [f"x{i}" for i in range(P)]
Xtr, Xte, ytr, yte = train_test_split(Xs, ys, test_size=0.3, random_state=0)
print("=" * 64)
print("  TEST 1 — synthetic, planted: y ~ x0*x1 + 0.8*x2^2 - 1.2*x3")
print("=" * 64)
extract(Xtr, ytr, Xte, yte, snames, C=0.2, topk=6,
        title="recovered (should surface x0*x1, x2^2, x3):")

# ---- Test 2: HIGGS ----
d = fetch_openml(data_id=23512, as_frame=False)
X = np.asarray(d.data, np.float32); names = list(d.feature_names)
yv = np.asarray(d.target); yv = (yv == "1").astype(int) if yv.dtype == object else (yv.astype(float) > .5).astype(int)
ok = ~np.isnan(X).any(1); X, yv = X[ok], yv[ok]
Xtr, Xte, ytr, yte = train_test_split(X, yv, test_size=0.2, random_state=0, stratify=yv)
Xtr, ytr = Xtr[:12000], ytr[:12000]; Xte, yte = Xte[:4000], yte[:4000]
s = StandardScaler().fit(Xtr); Xtr, Xte = s.transform(Xtr), s.transform(Xte)
logi = (LogisticRegression(max_iter=500).fit(Xtr, ytr).predict(Xte) == yte).mean()
rf = (RandomForestClassifier(200, n_jobs=-1, random_state=0).fit(Xtr, ytr).predict(Xte) == yte).mean()
print("\n" + "=" * 64)
print("  TEST 2 — HIGGS: what interactions drive signal vs background?")
print("=" * 64)
print(f"  reference: logistic(main only) {logi:.3f} | RF {rf:.3f} | chance 0.53")
extract(Xtr, ytr, Xte, yte, names, C=0.05, topk=12,
        title="extracted functional associations (named):")
print("\n  READ: test 1 validates the extractor recovers PLANTED interactions.")
print("  test 2 shows what HIGGS's signal is made of, and whether pairwise")
print("  interaction extraction beats main-effects logistic (or needs deeper terms).")
