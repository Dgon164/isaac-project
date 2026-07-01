"""
RESERVOIR + CRYSTAL + MERGE  — the monetizable thesis, tested at scale.

Claim: a BANK of random reservoirs, each crystallized into range-boxes, MERGED
by summing per-class box-counts, beats a single reservoir AND approaches/【passes】
a trained net -- at ZERO training cost. Reservoirs are the ideal thing to bolt
together because they're decorrelated by construction (their errors cancel), and
they never superpose, so axis-aligned boxes read them cleanly.

Why merging works here and not in weight space: each reservoir's crystal votes in
the SHARED label space (per-class counts). You can't average independent nets'
weights; you CAN sum their crystal votes.

Baselines for context: RandomForest, a trained MLP, that MLP crystallized, and a
raw range-classifier on the features. Dataset: covtype (subsampled for speed).
"""

import time
import numpy as np
from sklearn.datasets import fetch_covtype
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier

from range_classifier import quantize, build_concept, RangeClassifier, \
    CrystalClassifier, extract_sklearn_mlp

RNG = np.random.default_rng(0)


# ---- reservoir = random projection + relu (no training) --------------------
class Reservoir:
    def __init__(self, d_in, d_res, seed):
        g = np.random.default_rng(seed)
        self.R = g.standard_normal((d_in, d_res)) / np.sqrt(d_in)
        self.b = g.standard_normal(d_res) * 0.1

    def project(self, X):
        return np.maximum(X @ self.R + self.b, 0.0)


def build_crystal(H, y, margin=1.5):
    """H: reservoir activations (n, d_res). Strip DC, quantize, per-class boxes."""
    dc = H.mean(0)
    Hq, qlo, qhi = quantize(H - dc)
    concepts = []
    for c in np.unique(y):
        lo, hi, med = build_concept(Hq[y == c], margin=margin)
        concepts.append((c, lo, hi, med))
    return dc, qlo, qhi, concepts


def crystal_scores(concepts, Hq, labels):
    """Vectorized: per-class in-range COUNT for every test sample -> (n, n_labels)."""
    n = Hq.shape[0]
    out = np.zeros((n, len(labels)))
    for (label, lo, hi, med) in concepts:
        cnt = ((Hq >= lo) & (Hq <= hi)).sum(1).astype(float)
        li = labels.index(label)
        out[:, li] = np.maximum(out[:, li], cnt)
    return out


def reservoir_vote(res, crystal, Xte, labels):
    dc, qlo, qhi, concepts = crystal
    Hq, _, _ = quantize(res.project(Xte) - dc, qlo, qhi)
    return crystal_scores(concepts, Hq, labels)


def main():
    print("Loading covtype (downloads ~70MB first time)...")
    X, y = fetch_covtype(return_X_y=True)
    # subsample for a fast-but-real run
    idx = RNG.choice(len(X), 40000, replace=False)
    X, y = X[idx], y[idx]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.30, random_state=1, stratify=y)
    sc = StandardScaler().fit(Xtr)
    Xtr, Xte = sc.transform(Xtr), sc.transform(Xte)
    labels = sorted(np.unique(ytr).tolist())
    print(f"  train {len(Xtr)}, test {len(Xte)}, features {Xtr.shape[1]}, classes {len(labels)}\n")

    print("=" * 72)
    print("  BASELINES")
    print("=" * 72)
    t = time.time(); rf = RandomForestClassifier(n_estimators=100, n_jobs=-1, random_state=0).fit(Xtr, ytr)
    acc_rf = rf.score(Xte, yte); t_rf = time.time() - t
    print(f"  RandomForest(100)      acc {acc_rf:.3f}   train {t_rf:.1f}s")

    t = time.time(); mlp = MLPClassifier((256, 128), max_iter=60, random_state=0).fit(Xtr, ytr)
    acc_mlp = mlp.score(Xte, yte); t_mlp = time.time() - t
    print(f"  MLP(256,128)           acc {acc_mlp:.3f}   train {t_mlp:.1f}s")

    t = time.time(); cry = CrystalClassifier(extract_sklearn_mlp, max_splits=0).fit(mlp, Xtr, ytr)
    acc_cry = cry.score_accuracy(mlp, Xte, yte); t_cry = time.time() - t
    print(f"  MLP crystal (general)  acc {acc_cry:.3f}   (transplant of the MLP)")

    t = time.time(); raw = RangeClassifier(max_splits=0).fit(Xtr, ytr)
    acc_raw = raw.score_accuracy(Xte, yte)
    print(f"  Raw range (no net)     acc {acc_raw:.3f}\n")

    print("=" * 72)
    print("  RESERVOIR BANK + CRYSTAL + MERGE   (zero training; d_res=1024, relu)")
    print("=" * 72)
    D_RES, KMAX = 1024, 120
    # build the biggest bank once, evaluate ensembles of growing size
    reservoirs, crystals = [], []
    score_sum = np.zeros((len(Xte), len(labels)))
    checkpoints = [1, 3, 10, 30, 60, 120]
    t0 = time.time()
    print(f"  {'K reservoirs':<14}{'ensemble acc':>14}{'single-res avg':>16}{'cum time':>10}")
    single_accs = []
    for k in range(1, KMAX + 1):
        res = Reservoir(Xtr.shape[1], D_RES, seed=1000 + k)
        crys = build_crystal(res.project(Xtr), ytr)
        sc_k = reservoir_vote(res, crys, Xte, labels)
        reservoirs.append(res); crystals.append(crys)
        score_sum += sc_k
        single_accs.append((np.array(labels)[sc_k.argmax(1)] == yte).mean())
        if k in checkpoints:
            ens_acc = (np.array(labels)[score_sum.argmax(1)] == yte).mean()
            print(f"  {k:<14}{ens_acc:>14.3f}{np.mean(single_accs):>16.3f}{time.time()-t0:>9.1f}s")

    print("\n" + "=" * 72)
    print("  READING")
    print("=" * 72)
    print(f"  RF {acc_rf:.3f} | MLP {acc_mlp:.3f} | MLP-crystal {acc_cry:.3f} | "
          f"raw {acc_raw:.3f}")
    print("  The reservoir-ensemble column should CLIMB with K (decorrelated voters")
    print("  cancel errors). Single-reservoir avg is the floor each one contributes.")
    print("  Monetizable iff the ensemble nears/passes the TRAINED baselines at zero")
    print("  training cost. If it plateaus below, the merge needs the dim-select")
    print("  front-end (carrier/discriminative-dim peel) before crystallizing.")


if __name__ == "__main__":
    main()
