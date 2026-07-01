"""
HIGGS — the canonical HARD tabular challenge. 28 refined physics features,
binary (signal vs background). Notoriously high-order: linear/shallow models
flounder (~0.64 AUC), boosted trees ~0.81, deep nets ~0.88. No leakage (sim).

Where does the box family stand on hard tabular, and does BINDING (pairwise
interaction features = the high-order structure made explicit) close the gap?

Stack baselined:
  logistic           - shallow linear floor
  box (crystal)      - axis-aligned reader, raw
  box + LDA lens     - aligned (binary -> 1-d)
  box + interactions - pairwise products fed in (the binding thesis)
  RandomForest       - axis-aligned trees (box's natural cousin)
  HistGradientBoost  - strong shallow SOTA
  MLP                - the net

Run:  PYTHONUTF8=1 python -u higgs_bench.py
"""
import time, numpy as np
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
from sklearn.metrics import roc_auc_score
from lens_bench import crystal


def load_higgs():
    for kw in (dict(data_id=23512), dict(name="higgs", version=2), dict(name="Higgs", version=1)):
        try:
            d = fetch_openml(**kw, as_frame=False)
            X = np.asarray(d.data, dtype=np.float32)
            y = np.asarray(d.target)
            y = (y.astype(float) > 0.5).astype(int) if y.dtype != object else (y == "1").astype(int)
            ok = ~np.isnan(X).any(1)
            return X[ok], y[ok]
        except Exception as e:
            print(f"  (openml {kw} failed: {str(e)[:60]})")
    raise SystemExit("could not load HIGGS from openml")


def interactions(X, k=12):
    """append pairwise products of the top-k variance features (binding, explicit)."""
    v = X.var(0); idx = np.argsort(v)[::-1][:k]
    prods = [X[:, i] * X[:, j] for a, i in enumerate(idx) for j in idx[a:]]
    return np.column_stack([X] + prods)


def auc_of(model, Xtr, ytr, Xte, yte):
    model.fit(Xtr, ytr)
    s = model.predict_proba(Xte)[:, 1]
    return roc_auc_score(yte, s), (model.predict(Xte) == yte).mean()


def main():
    print("loading HIGGS (openml ~98k)..."); X, y = load_higgs()
    print(f"  X={X.shape}  class balance={y.mean():.3f}")
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=0, stratify=y)
    sc = StandardScaler().fit(Xtr); Xtr, Xte = sc.transform(Xtr), sc.transform(Xte)

    print("=" * 64)
    print("  HIGGS — hard tabular. ACC and AUC (chance ACC ~0.53, AUC 0.50)")
    print("=" * 64)
    rows = []

    a, ac = auc_of(LogisticRegression(max_iter=500), Xtr, ytr, Xte, yte)
    rows.append(("logistic (linear floor)", ac, a))

    boxr, _, _, _ = crystal(Xtr, ytr, Xte, yte, splits=3)
    rows.append(("box (crystal, raw)", boxr, None))

    lda = LDA().fit(Xtr, ytr)
    boxl, _, _, _ = crystal(lda.transform(Xtr), ytr, lda.transform(Xte), yte, splits=3)
    rows.append(("box + LDA lens", boxl, None))

    Itr, Ite = interactions(Xtr), interactions(Xte)
    ldai = LDA().fit(Itr, ytr)
    boxi, _, _, _ = crystal(ldai.transform(Itr), ytr, ldai.transform(Ite), yte, splits=3)
    rows.append(("box + interactions + lens", boxi, None))

    a, ac = auc_of(RandomForestClassifier(300, n_jobs=-1, random_state=0), Xtr, ytr, Xte, yte)
    rows.append(("RandomForest-300", ac, a))

    a, ac = auc_of(HistGradientBoostingClassifier(max_iter=400, random_state=0), Xtr, ytr, Xte, yte)
    rows.append(("HistGradientBoosting", ac, a))

    a, ac = auc_of(MLPClassifier((128, 64), max_iter=120, random_state=0), Xtr, ytr, Xte, yte)
    rows.append(("MLP (128,64)", ac, a))

    print(f"  {'model':<28}{'ACC':>8}{'AUC':>8}")
    print("  " + "-" * 44)
    for name, acc, auc in rows:
        print(f"  {name:<28}{acc:>8.3f}{(f'{auc:.3f}' if auc else '   -- '):>8}")
    print("  " + "-" * 44)
    print("  ref (full HIGGS): logistic AUC ~0.64, BDT ~0.81, deep net ~0.88.")
    print("  READ: does box+interactions reach the trees? = is the high-order")
    print("  structure recoverable cheaply on the box's tabular home turf.")


if __name__ == "__main__":
    main()
