"""
reinforce.py — smart, mistake-driven recovery for a merged box model
=====================================================================
After a cheap merge the pooled model is generalized and mediocre. The nets are
frozen feature sources; only the boxes and mask may move. So recovery = adapt
the boxes from the model's own errors, locally, no backprop.

The smart rule (LVQ for boxes), applied only on misclassified streaming points:
  - widen the TRUE class box toward the point, but only where it was a NEAR miss
    (don't stretch to embrace far outliers — that bloats boxes and re-creates the
    wide-box problem; those want a variant instead).
  - contract the WRONG class box to push its boundary just past the intruder,
    only where the point sat near that boundary (a marginal false-admit).
  - move the TRUE prototype toward the point and the WRONG prototype away (the
    distance tiebreak).
Learning rate decays; widths are floored so boxes can't invert or vanish.

Compared against:
  frozen — boxes never move (flat line at the merge accuracy)
  naive  — rebuild every box from all data seen so far each step (accurate but
           cost grows with data; this is the "small retrain" recovery)
"""
import numpy as np
import warnings; warnings.filterwarnings("ignore")
from sklearn.datasets import fetch_covtype
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier

from range_classifier import extract_sklearn_mlp
from fastscore import FastScorer
from concept_pipeline import (collapse_redundant, build_general_concepts,
                              quantize_fit, quantize_apply)


def smart_update(fs, Xq, y, lr=0.2, band=2.0):
    """Stable mistake-driven update: widen the TRUE box toward near misses and
    pull its prototype toward the point. No wrong-box contraction, no prototype
    repulsion — those are what made it diverge on imbalanced data. Every move
    targets an actual data point, so updates are self-bounding."""
    pred = fs.predict_q(Xq)
    miss = np.where(pred != y)[0]
    tindex = {lab: i for i, lab in enumerate(fs.labels)}
    for s in miss:
        x = Xq[s].astype(float)
        t = tindex[y[s]]
        below = (x < fs.LO[t]) & (fs.LO[t] - x <= band)
        above = (x > fs.HI[t]) & (x - fs.HI[t] <= band)
        fs.LO[t][below] -= lr * (fs.LO[t][below] - x[below])
        fs.HI[t][above] += lr * (x[above] - fs.HI[t][above])
        fs.MED[t] += lr * (x - fs.MED[t])


def fresh_scorer(Xq, y):
    return FastScorer(build_general_concepts(Xq, y))


def run_recovery(mode, Xq_merge, y_merge, stream, ytest, Xq_test,
                 batch=400, lr0=0.3, reservoir_cap=600):
    """Return (sample_counts, accuracies) as the stream is consumed.

    modes: frozen | naive (rebuild from all seen) | smart (LVQ widen-true)
           | stream (per-class capped reservoir -> rebuild; naive accuracy at
                     constant cost)
    """
    fs = fresh_scorer(Xq_merge, y_merge)
    Xq_seen, y_seen = [Xq_merge], [y_merge]
    # per-class reservoirs for stream mode
    res = {c: list(Xq_merge[y_merge == c]) for c in np.unique(y_merge)}
    counts, accs = [len(Xq_merge)], [(fs.predict_q(Xq_test) == ytest).mean()]
    Xq_stream, y_stream = stream
    n = len(Xq_stream)
    for b0 in range(0, n, batch):
        xb, yb = Xq_stream[b0:b0 + batch], y_stream[b0:b0 + batch]
        if mode == "smart":
            smart_update(fs, xb, yb, lr=lr0 * (1 - b0 / n) + 0.05)
        elif mode == "naive":
            Xq_seen.append(xb); y_seen.append(yb)
            fs = fresh_scorer(np.vstack(Xq_seen), np.concatenate(y_seen))
        elif mode == "stream":
            for c in np.unique(yb):
                res.setdefault(c, [])
                res[c].extend(xb[yb == c])
                if len(res[c]) > reservoir_cap:
                    res[c] = res[c][-reservoir_cap:]      # keep most recent
            Xq_r = np.vstack([np.array(v) for v in res.values()])
            y_r = np.concatenate([[c] * len(v) for c, v in res.items()])
            fs = fresh_scorer(Xq_r, y_r)
        counts.append(counts[-1] + len(xb))
        accs.append((fs.predict_q(Xq_test) == ytest).mean())
    return np.array(counts), np.array(accs)


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    # ---- data + frozen nets ----
    d = fetch_covtype(); X, Y = d.data, d.target
    idx = np.concatenate([rng.choice(np.where(Y == c)[0], min(2000, (Y == c).sum()),
                                     replace=False) for c in np.unique(Y)])
    X, Y = X[idx], Y[idx]
    Xtr, Xte, ytr, yte = train_test_split(X, Y, test_size=.3, random_state=0, stratify=Y)
    sc = StandardScaler().fit(Xtr); Xtr, Xte = sc.transform(Xtr), sc.transform(Xte)
    mlp = MLPClassifier((256, 128, 64), max_iter=400, random_state=42).fit(Xtr, ytr)

    def res(seed, do):
        g = np.random.default_rng(seed)
        W, b = g.normal(0, 1/np.sqrt(Xtr.shape[1]), (Xtr.shape[1], do)), g.normal(0, .1, do)
        return lambda Z: np.maximum(0, Z @ W + b)
    r1, r2 = res(1, 48), res(2, 48)

    Htr = np.column_stack([extract_sklearn_mlp(mlp, Xtr), r1(Xtr), r2(Xtr)])
    Hte = np.column_stack([extract_sklearn_mlp(mlp, Xte), r1(Xte), r2(Xte)])
    Htr, groups = collapse_redundant(Htr, corr_thr=0.8)        # the merge/dedup
    Hte = np.column_stack([Hte[:, g].mean(1) for g in groups])
    Xq_tr, qlo, qhi = quantize_fit(Htr); Xq_te = quantize_apply(Hte, qlo, qhi)

    # ---- tiny merge slice, rest is the post-merge stream ----
    order = rng.permutation(len(Xq_tr))
    merge_n = 350
    mi, si = order[:merge_n], order[merge_n:]
    Xq_merge, y_merge = Xq_tr[mi], ytr[mi]
    stream = (Xq_tr[si], ytr[si])
    net_acc = (mlp.predict(Xte) == yte).mean()

    print(f"frozen-net standalone acc (ceiling reference): {net_acc:.3f}")
    print(f"pooled+deduped dims: {Xq_tr.shape[1]} | merge slice: {merge_n} samples\n")
    print(f"{'samples':>9}", end="")
    rows = {}
    for mode in ("frozen", "naive", "smart", "stream"):
        c, a = run_recovery(mode, Xq_merge, y_merge, stream, yte, Xq_te)
        rows[mode] = (c, a)
    cs = rows["frozen"][0]
    # print a few checkpoints
    picks = [0, len(cs)//4, len(cs)//2, 3*len(cs)//4, len(cs)-1]
    print("   " + "".join(f"{rows['frozen'][0][p]:>8}" for p in picks))
    for mode in ("frozen", "naive", "smart", "stream"):
        a = rows[mode][1]
        print(f"{mode:>9}   " + "".join(f"{a[p]:>8.3f}" for p in picks))
