"""
COVTYPE — the road to parity, with honest accounting.

Two roads, per the theory's own tiers:
  UNDERSTOOD road — COMPOUND DOORS (audit 2.11): conjunctions
    "feature i in bin a AND feature j in bin b" as first-class doors,
    mined per confusable class pair (differentia thinking), admitted only
    when the conjunction's separation beats its BEST PART by a margin that
    survives a label-permutation null (selection-corrected). The flat
    ceiling fired the trigger (bins saturated at 56%); this is the
    designed response, not a patch.
  CAPTURED road — exemplar recognition (presence, not average): covtype is
    terrain, densely sampled; near neighbors share labels. This measures
    how much of the dataset is CAUGHT even if not yet said.

Recorded context: boxes 49.3% / marginal proximity doors 56.2% /
box-forest ~62% / net 0.82.
"""
import time
import numpy as np
from sklearn.datasets import fetch_covtype          # data loading only
import sys
sys.path.insert(0, r"C:\Users\jtwee\Documents\isaac_project\rebuild")
from doors_proximity import ProximityDoors

rng = np.random.default_rng(3)
N_BINS = 8


def bin_features(X, edges=None):
    """Quantile-bin every feature (binaries collapse naturally)."""
    if edges is None:
        qs = np.linspace(0, 100, N_BINS + 1)[1:-1]
        edges = [np.percentile(X[:, j], qs) for j in range(X.shape[1])]
    B = np.column_stack([np.searchsorted(edges[j], X[:, j])
                         for j in range(X.shape[1])])
    return B.astype(np.int8), edges


def mine_pair(Ba, Bb, top_feats=8, n_perm=30):
    """Compound candidates for one confusable class pair.
    Admission (audit 2.11): joint separation must beat the best PART's
    separation by a margin surviving the label-permutation null."""
    d = Ba.shape[1]
    # marginal separation per (feature, bin)
    marg = np.zeros((d, N_BINS))
    for j in range(d):
        pa = np.bincount(Ba[:, j], minlength=N_BINS) / len(Ba)
        pb = np.bincount(Bb[:, j], minlength=N_BINS) / len(Bb)
        marg[j] = np.abs(pa - pb)
    feat_rank = np.argsort(-marg.max(axis=1))[:top_feats]

    def gains(A, B_):
        out = []
        for fi in range(len(feat_rank)):
            for fj in range(fi + 1, len(feat_rank)):
                f1, f2 = feat_rank[fi], feat_rank[fj]
                for b1 in range(N_BINS):
                    if marg[f1, b1] < 0.02:
                        continue
                    m1 = A[:, f1] == b1
                    n1 = B_[:, f1] == b1
                    for b2 in range(N_BINS):
                        if marg[f2, b2] < 0.02:
                            continue
                        ja = float((m1 & (A[:, f2] == b2)).mean())
                        jb = float((n1 & (B_[:, f2] == b2)).mean())
                        gain = abs(ja - jb) - max(marg[f1, b1], marg[f2, b2])
                        if gain > 0:
                            out.append((gain, f1, b1, f2, b2))
        return out

    real = gains(Ba, Bb)
    if not real:
        return []
    # selection-corrected null: permute the pair's labels, take the MAX gain
    pool = np.vstack([Ba, Bb])
    na = len(Ba)
    null_max = []
    for _ in range(n_perm):
        p = rng.permutation(len(pool))
        null = gains(pool[p[:na]], pool[p[na:]])
        null_max.append(max((g for g, *_ in null), default=0.0))
    thr = np.percentile(null_max, 95)
    return [(g, f1, b1, f2, b2) for g, f1, b1, f2, b2 in real if g > thr]


def main():
    d = fetch_covtype()
    X, y = d.data.astype(np.float64), d.target.astype(int)
    idx = rng.permutation(len(y))
    k = int(0.7 * len(y))
    tr, te = idx[:k], idx[k:]
    Xtr, ytr, Xte, yte = X[tr], y[tr], X[te], y[te]
    print(f"covtype: train {len(ytr):,} test {len(yte):,}")

    # ---- baseline (the recorded 56.2%)
    t0 = time.time()
    base = ProximityDoors(bins=32).fit(Xtr, ytr)
    pb = np.concatenate([base.predict(Xte[i:i + 100_000])
                         for i in range(0, len(yte), 100_000)])
    acc0 = (pb == yte).mean()
    print(f"marginal doors:            {acc0*100:5.2f}%  [{time.time()-t0:.0f}s]")

    # ---- find the confusable pairs from validation errors
    val = Xtr[-50_000:]; yval = ytr[-50_000:]
    pv = base.predict(val)
    pairs = {}
    for a, b in zip(yval, pv):
        if a != b:
            key = (min(a, b), max(a, b))
            pairs[key] = pairs.get(key, 0) + 1
    top_pairs = sorted(pairs, key=pairs.get, reverse=True)[:4]
    print(f"most-confused pairs: {top_pairs}")

    # ---- mine compound doors per confused pair (the 2.11 trigger fired)
    Btr, edges = bin_features(Xtr)
    t0 = time.time()
    compounds = []
    for a, b in top_pairs:
        sa = Btr[ytr == a][:20_000]
        sb = Btr[ytr == b][:20_000]
        found = mine_pair(sa, sb)
        found.sort(reverse=True)
        compounds += [(f1, b1, f2, b2) for _, f1, b1, f2, b2 in found[:15]]
        print(f"  pair {a}-{b}: {len(found)} null-surviving compounds "
              f"(kept {min(15, len(found))})")
    seen = set()
    compounds = [c for c in compounds
                 if not (c in seen or seen.add(c))][:40]
    print(f"compound doors admitted: {len(compounds)}  [{time.time()-t0:.0f}s]")

    # ---- augmented doors: original features + compound indicator columns
    def augment(Xs):
        B, _ = bin_features(Xs, edges)
        cols = [((B[:, f1] == b1) & (B[:, f2] == b2)).astype(float)
                for f1, b1, f2, b2 in compounds]
        return np.column_stack([Xs] + cols)

    t0 = time.time()
    aug = ProximityDoors(bins=32).fit(augment(Xtr), ytr)
    Xte_aug = augment(Xte)
    pa = np.concatenate([aug.predict(Xte_aug[i:i + 100_000])
                         for i in range(0, len(yte), 100_000)])
    acc1 = (pa == yte).mean()
    print(f"marginal + compound doors: {acc1*100:5.2f}%  [{time.time()-t0:.0f}s]")

    # ---- the CAPTURED road: exemplar recognition (presence, not average)
    t0 = time.time()
    n_ex, n_te = 200_000, 20_000
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9
    A = ((Xtr[:n_ex] - mu) / sd).astype(np.float32)
    Bq = ((Xte[:n_te] - mu) / sd).astype(np.float32)
    yA = ytr[:n_ex]
    hits = 0
    for i in range(0, n_te, 2000):
        chunk = Bq[i:i + 2000]
        d2 = ((chunk[:, None, :] - A[None, :, :]) ** 2).sum(-1) \
            if False else None
        # memory-safe: compute via dot trick
        d2 = (chunk ** 2).sum(1)[:, None] - 2 * chunk @ A.T + (A ** 2).sum(1)[None, :]
        nn = np.argpartition(d2, 5, axis=1)[:, :5]
        for r in range(len(chunk)):
            votes = np.bincount(yA[nn[r]])
            hits += (votes.argmax() == yte[i + r])
    acc2 = hits / n_te
    print(f"exemplar (captured) road:  {acc2*100:5.2f}%  [{time.time()-t0:.0f}s]"
          f"  (5-NN over 200k exemplars, 20k test sample)")

    print("\nACCOUNTING vs recorded net 0.82:")
    print(f"  articulated (doors):     {acc0*100:.1f}%")
    print(f"  + compound doors:        {acc1*100:.1f}%")
    print(f"  captured (exemplars):    {acc2*100:.1f}%")


if __name__ == "__main__":
    main()
