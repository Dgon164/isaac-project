"""
SWEEP (GPU) — same reservoir+crystal+merge sweep, on the RTX 3090.

The hot path (box scoring: (Aq>=lo)&(Aq<=hi), elementwise/boolean) is what pegged
one CPU core. On the GPU it's massively parallel, and we batch all concepts at
once. Everything lives on cuda; reservoirs loop in Python but each step is a GPU
op, so the loop overhead is nil. Lets us crank width / K far past the CPU version.

Knobs identical to sweep.py: source, width, nonlin, dim_k, splits, K, margin.
"""

import time
import numpy as np
import torch
from sklearn.datasets import fetch_covtype
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier

DEV = "cuda" if torch.cuda.is_available() else "cpu"
LOW, HIGH = -7, 8


# ---------- GPU crystal primitives ------------------------------------------
def quantize_t(A, lo=None, hi=None):
    if lo is None:
        lo, hi = A.min(0).values, A.max(0).values
    rng = (hi - lo).clamp_min(1e-9)
    Aq = torch.round((A - lo) / rng * (HIGH - LOW) + LOW).clamp(LOW, HIGH)
    return Aq, lo, hi


def fisher_dims(A, y, k):
    if k is None or k >= A.shape[1]:
        return None
    overall = A.mean(0)
    sb = torch.zeros(A.shape[1], device=A.device)
    sw = torch.zeros(A.shape[1], device=A.device)
    for c in torch.unique(y):
        Ac = A[y == c]; mu = Ac.mean(0)
        sb += Ac.shape[0] * (mu - overall) ** 2
        sw += ((Ac - mu) ** 2).sum(0)
    return torch.topk(sb / sw.clamp_min(1e-9), k).indices


def box(Aq_c, margin):
    lo = torch.quantile(Aq_c, 0.01, dim=0) - margin
    hi = torch.quantile(Aq_c, 0.95, dim=0) + margin
    med = Aq_c.median(0).values
    return lo, hi, med


def box_counts(Aq, LO, HI, MED, chunk=2048):
    """Combined score = count - dist/denom: count dominates, median-distance is
    the sub-unit tiebreak (this is what makes tight variant boxes win)."""
    n, D = Aq.shape
    denom = D * (HIGH - LOW) + 1.0
    out = torch.empty((n, LO.shape[0]), device=Aq.device)
    for i in range(0, n, chunk):
        a = Aq[i:i + chunk].unsqueeze(1)
        inr = (a >= LO) & (a <= HI)
        cnt = inr.sum(-1).float()
        dist = (torch.abs(a - MED) * inr).sum(-1)
        out[i:i + chunk] = cnt - dist / denom
    return out


def label_scores(counts, LAB, labels):
    out = torch.zeros((counts.shape[0], len(labels)), device=counts.device)
    for i, l in enumerate(labels):
        m = LAB == l
        if m.any():
            out[:, i] = counts[:, m].max(1).values
    return out


def make_crystal(H, y, splits, dim_k, margin, labels):
    dc = H.mean(0); A = H - dc
    dims = fisher_dims(A, y, dim_k)
    if dims is not None:
        A = A[:, dims]
    Aq, qlo, qhi = quantize_t(A)
    LO, HI, MED, LAB = [], [], [], []
    for c in labels:
        lo, hi, med = box(Aq[y == c], margin)
        LO.append(lo); HI.append(hi); MED.append(med); LAB.append(c)
    LO = torch.stack(LO); HI = torch.stack(HI); MED = torch.stack(MED)
    LAB = torch.tensor(LAB, device=H.device)
    for _ in range(splits):
        pred_i = label_scores(box_counts(Aq, LO, HI, MED), LAB, labels).argmax(1)
        pred = torch.tensor(labels, device=H.device)[pred_i]
        nl, nh, nm, nlab = [], [], [], []
        for tl in labels:
            for cl in labels:
                if tl == cl:
                    continue
                m = (y == tl) & (pred == cl)
                if m.sum() >= 3:
                    lo, hi, med = box(Aq[m], margin)
                    nl.append(lo); nh.append(hi); nm.append(med); nlab.append(tl)
        if not nl:
            break
        LO = torch.cat([LO, torch.stack(nl)]); HI = torch.cat([HI, torch.stack(nh)])
        MED = torch.cat([MED, torch.stack(nm)])
        LAB = torch.cat([LAB, torch.tensor(nlab, device=H.device)])
    return dict(dc=dc, dims=dims, qlo=qlo, qhi=qhi, LO=LO, HI=HI, MED=MED, LAB=LAB)


def crystal_scores(cr, H, labels):
    A = H - cr["dc"]
    if cr["dims"] is not None:
        A = A[:, cr["dims"]]
    Aq, _, _ = quantize_t(A, cr["qlo"], cr["qhi"])
    return label_scores(box_counts(Aq, cr["LO"], cr["HI"], cr["MED"]), cr["LAB"], labels)


def reservoir(d_in, width, seed, nonlin):
    g = torch.Generator(device=DEV).manual_seed(seed)
    R = torch.randn(d_in, width, generator=g, device=DEV) / (d_in ** 0.5)
    b = torch.randn(width, generator=g, device=DEV) * 0.1
    f = torch.tanh if nonlin == "tanh" else torch.relu
    return lambda X: f(X @ R + b)


def run(cfg, Xtr, Xte, ytr, yte, labels, mlp_H=None):
    t = time.time()
    if cfg["source"] == "mlp":
        Htr, Hte = mlp_H
        cr = make_crystal(Htr, ytr, cfg["splits"], cfg["dim_k"], cfg.get("margin", 1.5), labels)
        S = crystal_scores(cr, Hte, labels); nc = cr["LO"].shape[0]
    else:
        S = torch.zeros((Xte.shape[0], len(labels)), device=DEV); nc = 0
        for k in range(cfg["K"]):
            proj = reservoir(Xtr.shape[1], cfg["width"], 1000 + k, cfg["nonlin"])
            cr = make_crystal(proj(Xtr), ytr, cfg["splits"], cfg["dim_k"], cfg.get("margin", 1.5), labels)
            S += crystal_scores(cr, proj(Xte), labels); nc += cr["LO"].shape[0]
    pred = torch.tensor(labels, device=DEV)[S.argmax(1)]
    torch.cuda.synchronize()
    return (pred == yte).float().mean().item(), nc, time.time() - t


def mlp_hidden(M, X):
    h = X
    for i in range(len(M.coefs_) - 1):
        W = torch.tensor(M.coefs_[i], dtype=torch.float32, device=DEV)
        b = torch.tensor(M.intercepts_[i], dtype=torch.float32, device=DEV)
        h = torch.relu(h @ W + b)
    return h


CONFIGS = [
    ("mlp base",             dict(source="mlp", splits=0,  dim_k=None)),
    ("mlp +var",             dict(source="mlp", splits=10, dim_k=None)),
    ("mlp +dim+var",         dict(source="mlp", splits=10, dim_k=64)),
    ("res1 relu1024",        dict(source="res", K=1,   width=1024, nonlin="relu", splits=0,  dim_k=None)),
    ("res1 relu1024 var",    dict(source="res", K=1,   width=1024, nonlin="relu", splits=10, dim_k=None)),
    ("res1 d64 var",         dict(source="res", K=1,   width=1024, nonlin="relu", splits=10, dim_k=64)),
    ("merge30 var",          dict(source="res", K=30,  width=1024, nonlin="relu", splits=10, dim_k=None)),
    ("merge100 var",         dict(source="res", K=100, width=1024, nonlin="relu", splits=10, dim_k=None)),
    ("merge100 d64 var",     dict(source="res", K=100, width=1024, nonlin="relu", splits=10, dim_k=64)),
]


def run_dataset(name, X, y, n_sub=None):
    if n_sub and len(X) > n_sub:
        idx = np.random.default_rng(0).choice(len(X), n_sub, replace=False)
        X, y = X[idx], y[idx]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.30, random_state=1, stratify=y)
    sc = StandardScaler().fit(Xtr); Xtr_n, Xte_n = sc.transform(Xtr), sc.transform(Xte)
    labels = sorted(np.unique(ytr).tolist())
    rf = RandomForestClassifier(100, n_jobs=-1, random_state=0).fit(Xtr_n, ytr)
    mlp = MLPClassifier((256, 128), max_iter=80, random_state=0).fit(Xtr_n, ytr)

    Xtr_t = torch.tensor(Xtr_n, dtype=torch.float32, device=DEV)
    Xte_t = torch.tensor(Xte_n, dtype=torch.float32, device=DEV)
    ytr_t = torch.tensor(ytr, device=DEV); yte_t = torch.tensor(yte, device=DEV)
    mlp_H = (mlp_hidden(mlp, Xtr_t), mlp_hidden(mlp, Xte_t))

    print(f"\n{'='*60}\n  {name}: train {len(Xtr)} test {len(Xte)} feat {X.shape[1]} "
          f"classes {len(labels)}\n{'='*60}")
    print(f"  [ref] RF {rf.score(Xte_n, yte):.3f}   MLP {mlp.score(Xte_n, yte):.3f}")
    print(f"  {'config':<22}{'acc':>7}{'concepts':>10}{'time':>8}")
    for cname, cfg in CONFIGS:
        c = dict(cfg); c["source"] = "mlp" if c["source"] == "mlp" else "res"
        acc, nc, dt = run(c, Xtr_t, Xte_t, ytr_t, yte_t, labels, mlp_H)
        print(f"  {cname:<22}{acc:>7.3f}{nc:>10}{dt:>7.1f}s")


def main():
    from sklearn.datasets import load_digits
    print(f"Device: {DEV} ({torch.cuda.get_device_name(0) if DEV=='cuda' else 'cpu'})")
    dig = load_digits()
    run_dataset("digits (box-friendly)", dig.data, dig.target)
    Xc, yc = fetch_covtype(return_X_y=True)
    run_dataset("covtype (box-hostile)", Xc, yc, n_sub=28000)


if __name__ == "__main__":
    main()
