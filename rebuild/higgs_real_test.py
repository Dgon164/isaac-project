"""
REAL-DATA TEST 2 — HIGGS (full 11,000,000 rows).

Part 1: proximity doors as classifier on the 28 features.
  Recorded references: box (his, no lens) 0.525 ~ chance; his processing
  matrix 0.650; logistic 0.642; MLP 0.691; RF 0.721; HGB 0.726;
  additive/no-interaction model AUC 0.765; deterministic detector
  acc 0.7957 / AUC 0.8810 at full scale (= Baldi 2014 ceiling).
  Doors are additive over rotated dims -> the fair target is the additive
  ceiling, NOT the interaction ceiling.

Part 2: the real m_jj wall (recorded: Stage-2 R2 0.075, "could not close").
  Massless-jet truth: m_jj^2 = 2*pt1*pt2*(cosh(d_eta) - cos(d_phi)) — but the
  dataset's columns are rescaled (phi capped at 1.74 = pi/1.806), so the law
  in recorded units has unknown scale constants INSIDE cosh/cos. The staged
  enumerator gets scale-gridded atoms cos(k*diff)/cosh(k*diff) and must find
  form AND scales itself. Old poly-L1 runs on the same rows for comparison.
Train/test: fit on the first rows, evaluate on the LAST 500k (Baldi split).
"""
import time
import numpy as np
from doors_proximity import ProximityDoors
from enumerator_staged import StagedEnumerator, PolyL1, term_name, r2

NAMES = ["lep_pt", "lep_eta", "lep_phi", "met", "met_phi",
         "j1pt", "j1eta", "j1phi", "j1b", "j2pt", "j2eta", "j2phi", "j2b",
         "j3pt", "j3eta", "j3phi", "j3b", "j4pt", "j4eta", "j4phi", "j4b",
         "m_jj", "m_jjj", "m_lv", "m_jlv", "m_bb", "m_wbb", "m_wwbb"]


def auc(scores, labels):
    order = np.argsort(scores)
    ranks = np.empty(len(scores)); ranks[order] = np.arange(1, len(scores) + 1)
    pos = labels == 1
    n1, n0 = pos.sum(), (~pos).sum()
    return float((ranks[pos].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def part1_doors(D):
    X, y = D[:, 1:].astype(np.float64), D[:, 0].astype(int)
    Xtr, ytr, Xte, yte = X[:-500_000], y[:-500_000], X[-500_000:], y[-500_000:]
    print(f"\nPART 1 — proximity doors on 28 features, "
          f"train {len(ytr):,} / test {len(yte):,}")
    t0 = time.time()
    prx = ProximityDoors(bins=32).fit(Xtr, ytr)
    preds, margins = [], []
    for i in range(0, len(yte), 100_000):
        H = prx._onehot(Xte[i:i + 100_000])
        S = H @ prx.L.T
        preds.append(prx.classes[np.argmax(S, axis=1)])
        margins.append(S[:, 1] - S[:, 0])
    p, m = np.concatenate(preds), np.concatenate(margins)
    print(f"  doors: {(p == yte).mean()*100:.2f}% correct   AUC {auc(m, yte):.3f}"
          f"   [{time.time()-t0:.0f}s]")
    print("  (references: box 52.5% / logistic 64.2% / MLP 69.1% / "
          "additive AUC 0.765 / full ceiling 79.6%, AUC 0.881)")


def jet_atoms(X, names):
    """Vars + scale-gridded transcendental pair atoms (scales unknown because
    the dataset rescaled every column — the grid lets the enumerator FIND them)."""
    cols, labels = [], []
    d = X.shape[1]
    for i in range(d):
        cols.append(X[:, i]); labels.append(names[i])
    ks_cos = np.arange(0.25, 3.01, 0.25)
    ks_cosh = np.arange(0.25, 2.01, 0.25)
    for i in range(d):
        for j in range(i + 1, d):
            diff = X[:, i] - X[:, j]
            for k in ks_cos:
                cols.append(np.cos(k * diff))
                labels.append(f"cos({k:.2f}*({names[i]}-{names[j]}))")
            for k in ks_cosh:
                cols.append(np.cosh(k * diff))
                labels.append(f"cosh({k:.2f}*({names[i]}-{names[j]}))")
    return np.column_stack(cols), labels


def part2_mjj(D):
    feats = [5, 6, 7, 9, 10, 11]                      # j1pt j1eta j1phi j2pt j2eta j2phi
    names = [NAMES[i] for i in feats]
    X = D[:, [f + 1 for f in feats]].astype(np.float64)
    y = (D[:, 22].astype(np.float64)) ** 2            # m_jj^2 (col 22 = m_jj)
    ntr = 100_000
    Xtr, ytr = X[:ntr], y[:ntr]
    Xte, yte = X[-500_000:], y[-500_000:]
    print(f"\nPART 2 — real m_jj^2 from jet1/jet2 low-level, "
          f"fit {ntr:,} rows, held-out 500,000")
    t0 = time.time()
    old = PolyL1().fit(Xtr, ytr)
    print(f"  OLD poly-L1:  held-out R2 {r2(yte, old.predict(Xte)):.3f} "
          f"with {old.n_terms()} terms   [{time.time()-t0:.0f}s]"
          f"   (recorded wall: R2 0.075)")
    t0 = time.time()
    new = StagedEnumerator(n_perm=40, atom_fn=jet_atoms).fit(Xtr, ytr, names)
    print(f"  NEW staged:   held-out R2 {r2(yte, new.predict(Xte, names)):.3f}"
          f"   [{time.time()-t0:.0f}s]")
    print(f"  NEW equation: {new.equation()}")


if __name__ == "__main__":
    t0 = time.time()
    D = np.load("../data/HIGGS.npy")
    print(f"HIGGS loaded {D.shape} [{time.time()-t0:.0f}s]")
    part1_doors(D)
    part2_mjj(D)
