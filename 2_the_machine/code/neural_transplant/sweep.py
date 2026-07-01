"""
SWEEP — mash on the knobs, watch what moves.

Levers:
  source     : 'mlp' (trained-net transplant) or 'reservoir' (zero training)
  width      : reservoir hidden dims
  nonlin     : relu | tanh
  dim_k      : keep top-k Fisher-discriminative dims (None = all)  <- the front-end
  splits     : confusion-resolution rounds (box-forest variants per class)
  K          : reservoir-bank merge size (decorrelated voters)
  margin     : box tolerance

Everything is vectorized (including confusion resolution) so dozens of configs
run in minutes. Edit CONFIGS at the bottom and re-run to keep messing with it.
"""

import time
import numpy as np
from sklearn.datasets import fetch_covtype
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from range_classifier import quantize, build_concept, extract_sklearn_mlp

RNG = np.random.default_rng(0)


# ---------- core: vectorized crystal with dim-select + variants -------------
def fisher_dims(H, y, k):
    """Top-k dims by between-class / within-class variance."""
    if k is None or k >= H.shape[1]:
        return None
    classes = np.unique(y)
    overall = H.mean(0)
    sb = np.zeros(H.shape[1]); sw = np.zeros(H.shape[1])
    for c in classes:
        Hc = H[y == c]; mu = Hc.mean(0)
        sb += len(Hc) * (mu - overall) ** 2
        sw += ((Hc - mu) ** 2).sum(0)
    sw[sw == 0] = 1e-9
    return np.argsort(-(sb / sw))[:k]


def scores_matrix(concepts, Aq, labels):
    out = np.zeros((Aq.shape[0], len(labels)))
    idx = {l: i for i, l in enumerate(labels)}
    for (label, lo, hi, med) in concepts:
        cnt = ((Aq >= lo) & (Aq <= hi)).sum(1).astype(float)
        i = idx[label]
        out[:, i] = np.maximum(out[:, i], cnt)
    return out


def make_crystal(H, y, splits=0, dim_k=None, margin=1.5):
    dc = H.mean(0)
    A = H - dc
    dims = fisher_dims(A, y, dim_k)
    if dims is not None:
        A = A[:, dims]
    Aq, qlo, qhi = quantize(A)
    labels = sorted(np.unique(y).tolist())
    concepts = [(c, *build_concept(Aq[y == c], margin=margin)) for c in labels]
    for _ in range(splits):
        pred = np.array(labels)[scores_matrix(concepts, Aq, labels).argmax(1)]
        added = False
        for tl in labels:
            for cl in labels:
                if tl == cl:
                    continue
                m = (y == tl) & (pred == cl)
                if m.sum() >= 3:
                    concepts.append((tl, *build_concept(Aq[m], margin=margin)))
                    added = True
        if not added:
            break
    return dict(dc=dc, dims=dims, qlo=qlo, qhi=qhi, concepts=concepts, labels=labels)


def crystal_scores(cr, H):
    A = H - cr["dc"]
    if cr["dims"] is not None:
        A = A[:, cr["dims"]]
    Aq, _, _ = quantize(A, cr["qlo"], cr["qhi"])
    return scores_matrix(cr["concepts"], Aq, cr["labels"])


# ---------- reservoir -------------------------------------------------------
def reservoir(d_in, width, seed, nonlin):
    g = np.random.default_rng(seed)
    R = g.standard_normal((d_in, width)) / np.sqrt(d_in)
    b = g.standard_normal(width) * 0.1
    f = (np.tanh if nonlin == "tanh" else (lambda z: np.maximum(z, 0.0)))
    return lambda X: f(X @ R + b)


# ---------- one config ------------------------------------------------------
def run(cfg, data):
    Xtr, Xte, ytr, yte = data
    labels = sorted(np.unique(ytr).tolist())
    t = time.time()
    if cfg["source"] == "mlp":
        mlp = cfg["mlp"]
        Htr, Hte = extract_sklearn_mlp(mlp, Xtr), extract_sklearn_mlp(mlp, Xte)
        cr = make_crystal(Htr, ytr, cfg["splits"], cfg["dim_k"], cfg.get("margin", 1.5))
        S = crystal_scores(cr, Hte)
        nconc = len(cr["concepts"])
    else:  # reservoir bank
        S = np.zeros((len(Xte), len(labels)))
        nconc = 0
        for k in range(cfg["K"]):
            proj = reservoir(Xtr.shape[1], cfg["width"], 1000 + k, cfg["nonlin"])
            cr = make_crystal(proj(Xtr), ytr, cfg["splits"], cfg["dim_k"], cfg.get("margin", 1.5))
            S += crystal_scores(cr, proj(Xte))
            nconc += len(cr["concepts"])
    acc = (np.array(labels)[S.argmax(1)] == yte).mean()
    return acc, nconc, time.time() - t


def main():
    print("Loading covtype...")
    X, y = fetch_covtype(return_X_y=True)
    idx = RNG.choice(len(X), 28000, replace=False)
    X, y = X[idx], y[idx]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.30, random_state=1, stratify=y)
    sc = StandardScaler().fit(Xtr); Xtr, Xte = sc.transform(Xtr), sc.transform(Xte)
    data = (Xtr, Xte, ytr, yte)
    print(f"  train {len(Xtr)} test {len(Xte)} feat {Xtr.shape[1]} classes {len(np.unique(ytr))}\n")

    rf = RandomForestClassifier(100, n_jobs=-1, random_state=0).fit(Xtr, ytr)
    mlp = MLPClassifier((256, 128), max_iter=60, random_state=0).fit(Xtr, ytr)
    print(f"  [ref] RandomForest {rf.score(Xte, yte):.3f}   MLP {mlp.score(Xte, yte):.3f}\n")

    CONFIGS = [
        # --- trained-net transplant: does dim-select + variants close the gap? ---
        ("mlp  base",            dict(source="mlp", mlp=mlp, splits=0,  dim_k=None)),
        ("mlp  +variants",       dict(source="mlp", mlp=mlp, splits=10, dim_k=None)),
        ("mlp  +dim64",          dict(source="mlp", mlp=mlp, splits=0,  dim_k=64)),
        ("mlp  +dim64+var",      dict(source="mlp", mlp=mlp, splits=10, dim_k=64)),
        ("mlp  +dim128+var",     dict(source="mlp", mlp=mlp, splits=10, dim_k=128)),
        # --- single reservoir: what makes one good? ---
        ("res1 relu1024",        dict(source="res", K=1, width=1024, nonlin="relu", splits=0,  dim_k=None)),
        ("res1 relu1024 +var",   dict(source="res", K=1, width=1024, nonlin="relu", splits=10, dim_k=None)),
        ("res1 relu1024 d64 var",dict(source="res", K=1, width=1024, nonlin="relu", splits=10, dim_k=64)),
        ("res1 relu4096 d64 var",dict(source="res", K=1, width=4096, nonlin="relu", splits=10, dim_k=64)),
        ("res1 tanh2048 d64 var",dict(source="res", K=1, width=2048, nonlin="tanh", splits=10, dim_k=64)),
        # --- merge the bank: does bolting climb with the front-end on? ---
        ("merge30 relu1024 var", dict(source="res", K=30, width=1024, nonlin="relu", splits=10, dim_k=None)),
        ("merge30 d64 var",      dict(source="res", K=30, width=1024, nonlin="relu", splits=10, dim_k=64)),
        ("merge120 d64 var",     dict(source="res", K=120, width=1024, nonlin="relu", splits=10, dim_k=64)),
    ]

    print("  " + "-" * 70)
    print(f"  {'config':<24}{'acc':>7}{'concepts':>10}{'time':>8}")
    print("  " + "-" * 70)
    for name, cfg in CONFIGS:
        cfg["source"] = "mlp" if cfg["source"] == "mlp" else "reservoir"
        acc, nconc, dt = run(cfg, data)
        print(f"  {name:<24}{acc:>7.3f}{nconc:>10}{dt:>7.1f}s")
    print("  " + "-" * 70)
    print("  covtype box-family record: box-forest ~0.69 ceiling, RF ~0.95, net ~0.83")


if __name__ == "__main__":
    main()
