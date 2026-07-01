"""
THE REAL RETEST — does binding (compound/interaction doors) break the box-
hostility ceiling on covtype? Measured baseline: flat box ~0.5, box-forest ~0.69,
RF ~0.85, net ~0.82. CPU, bounded, no GPU.

Interaction doors = pairwise products of (already standardized, so zero-mean)
features — the conjunction as its own axis. We test all-pairwise (risks noise
dilution) and Fisher-SELECTED interactions (keep only the discriminative ones),
each with and without variants (box-forest).
"""
import time, numpy as np
from sklearn.datasets import fetch_covtype
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier

RNG = np.random.default_rng(0)
LOW, HIGH = -7, 8


def quantize(X, lo=None, hi=None):
    if lo is None:
        lo, hi = X.min(0), X.max(0)
    rng = np.where(hi - lo == 0, 1, hi - lo)
    return np.clip(np.round((X - lo) / rng * (HIGH - LOW) + LOW), LOW, HIGH), lo, hi


def fisher(H, y, k):
    if k is None or k >= H.shape[1]:
        return None
    ov = H.mean(0); sb = np.zeros(H.shape[1]); sw = np.zeros(H.shape[1])
    for c in np.unique(y):
        Hc = H[y == c]; mu = Hc.mean(0)
        sb += len(Hc) * (mu - ov) ** 2; sw += ((Hc - mu) ** 2).sum(0)
    sw[sw == 0] = 1e-9
    return np.argsort(-(sb / sw))[:k]


def box(o, margin=1.5):
    return (np.percentile(o, 1, 0) - margin, np.percentile(o, 95, 0) + margin, np.median(o, 0))


def score(Xq, LO, HI, MED, chunk=1500):
    n, D = Xq.shape; denom = D * (HIGH - LOW) + 1.0
    out = np.empty((n, LO.shape[0]))
    for i in range(0, n, chunk):
        a = Xq[i:i + chunk][:, None, :]
        inr = (a >= LO[None]) & (a <= HI[None])
        out[i:i + chunk] = inr.sum(2) - (np.abs(a - MED[None]) * inr).sum(2) / denom
    return out


def per_label(S, LAB, labels):
    o = np.full((S.shape[0], len(labels)), -1e18)
    for j, l in enumerate(labels):
        m = LAB == l
        if m.any(): o[:, j] = S[:, m].max(1)
    return np.array(labels)[o.argmax(1)]


def build(Xq, y, splits=0, min_group=20):
    labels = sorted(np.unique(y).tolist())
    LO, HI, MED, LAB = [], [], [], []
    for c in labels:
        lo, hi, md = box(Xq[y == c]); LO.append(lo); HI.append(hi); MED.append(md); LAB.append(c)
    LO, HI, MED, LAB = np.array(LO), np.array(HI), np.array(MED), np.array(LAB)
    for _ in range(splits):
        pred = per_label(score(Xq, LO, HI, MED), LAB, labels)
        al, ah, am, alab = [], [], [], []
        for tl in labels:
            for cl in labels:
                if tl == cl: continue
                m = (y == tl) & (pred == cl)
                if m.sum() >= min_group:
                    lo, hi, md = box(Xq[m]); al.append(lo); ah.append(hi); am.append(md); alab.append(tl)
        if not al: break
        LO = np.vstack([LO, al]); HI = np.vstack([HI, ah]); MED = np.vstack([MED, am])
        LAB = np.concatenate([LAB, alab])
    return LO, HI, MED, LAB, labels


def interactions(X):
    d = X.shape[1]
    comps = [X[:, a] * X[:, b] for a in range(d) for b in range(a + 1, d)]
    return np.concatenate([X, np.stack(comps, 1)], 1)


def run(name, Xtr, ytr, Xte, yte, interact=False, select=None, splits=0):
    t = time.time()
    A, B = (interactions(Xtr), interactions(Xte)) if interact else (Xtr, Xte)
    Qtr, lo, hi = quantize(A); Qte, _, _ = quantize(B, lo, hi)
    if select:
        d = fisher(Qtr, ytr, select); Qtr, Qte = Qtr[:, d], Qte[:, d]
    LO, HI, MED, LAB, labels = build(Qtr, ytr, splits=splits)
    acc = (per_label(score(Qte, LO, HI, MED), LAB, labels) == yte).mean()
    print(f"  {name:<32}{acc:6.3f}   dims {Qtr.shape[1]:>5}  concepts {len(LAB):>3}  {time.time()-t:5.1f}s")
    return acc


def main():
    print("loading covtype...")
    X, y = fetch_covtype(return_X_y=True)
    idx = RNG.choice(len(X), 24000, replace=False); X, y = X[idx], y[idx]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, random_state=1, stratify=y)
    sc = StandardScaler().fit(Xtr); Xtr, Xte = sc.transform(Xtr), sc.transform(Xte)
    print(f"  train {len(Xtr)} test {len(Xte)} feat {Xtr.shape[1]}\n")

    rf = RandomForestClassifier(100, n_jobs=-1, random_state=0).fit(Xtr, ytr)
    mlp = MLPClassifier((256, 128), max_iter=60, random_state=0).fit(Xtr, ytr)
    print(f"  [ref] RF {rf.score(Xte, yte):.3f}   MLP {mlp.score(Xte, yte):.3f}\n")
    print(f"  {'config':<32}{'acc':>6}")
    run("flat box (54 dims)",           Xtr, ytr, Xte, yte)
    run("flat box + variants",          Xtr, ytr, Xte, yte, splits=4)
    run("interactions ALL (54+1431)",   Xtr, ytr, Xte, yte, interact=True)
    run("interactions, Fisher-128",     Xtr, ytr, Xte, yte, interact=True, select=128)
    run("interactions-128 + variants",  Xtr, ytr, Xte, yte, interact=True, select=128, splits=4)
    print("\n  baseline to beat: flat ~0.5, box-forest ~0.69. Does binding climb past it?")


if __name__ == "__main__":
    main()
