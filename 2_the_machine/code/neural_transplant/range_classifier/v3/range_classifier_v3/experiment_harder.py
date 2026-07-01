"""
experiment_harder.py
====================
Two tests the toy four can't show:

A) XOR, raw mode (no net). Single axes are useless by construction; only the
   interaction matters. Isolates whether joint_axes recovers what marginals
   can't — and whether co-activation detection finds the right pair on its own.

B) Covtype, crystal mode. A real 7-class problem with genuinely confusable
   classes. Ablates dense -> +collapse -> +joints -> +select, reporting both
   accuracy and mean axes-used-per-concept, so we see whether the mechanisms
   hold up and how minimal they stay off the toy data.
"""
import numpy as np
import warnings; warnings.filterwarnings("ignore")
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.datasets import fetch_covtype

from range_classifier import extract_sklearn_mlp
from fastscore import FastScorer
from concept_pipeline import (collapse_redundant, joint_axes,
                              build_general_concepts, sample_separation_mask,
                              greedy_holdout_mask, quantize_fit, quantize_apply)


def evaluate(H_tr, y_tr, H_te, y_te, collapse, n_joints, select,
             corr_thr=0.8, margin=1.5):
    """Build a representation + concepts from training, score test set."""
    groups = pairs = None
    if collapse:
        H_tr, groups = collapse_redundant(H_tr, corr_thr)
        H_te = np.column_stack([H_te[:, g].mean(1) for g in groups])
    if n_joints:
        H_tr2, pairs = joint_axes(H_tr, y_tr, k=n_joints)
        if pairs:
            mean = (H_tr - H_tr.mean(0))  # recompute centered using TRAIN mean
            tr_mean = H_tr.mean(0)
            cols_te = [ (H_te[:, a]-tr_mean[a]) * (H_te[:, b]-tr_mean[b]) for a, b in pairs]
            cols_tr = [ (H_tr[:, a]-tr_mean[a]) * (H_tr[:, b]-tr_mean[b]) for a, b in pairs]
            H_tr = np.column_stack([H_tr] + cols_tr)
            H_te = np.column_stack([H_te] + cols_te)

    Xq_tr, qlo, qhi = quantize_fit(H_tr)
    Xq_te = quantize_apply(H_te, qlo, qhi)
    concepts = build_general_concepts(Xq_tr, y_tr, margin=margin)
    fs = FastScorer(concepts)
    if select:
        mask, _ = greedy_holdout_mask(Xq_tr, y_tr, margin=margin)
        fs.set_mask(mask)
    acc = (fs.predict_q(Xq_te) == y_te).mean()
    return acc, fs.mean_active_dims(), (len(pairs) if pairs else 0)


# ============================================================ A) XOR (raw)
print("=" * 70)
print("A) XOR in RAW mode — single axes useless by construction")
print("=" * 70)
rng = np.random.default_rng(0)
n = 4000
s1, s2 = rng.normal(size=n), rng.normal(size=n)
yx = ((s1 > 0) ^ (s2 > 0)).astype(int)
noise = rng.normal(size=(n, 8))
Xx = np.column_stack([s1, s2, noise])
Xtr, Xte, ytr, yte = train_test_split(Xx, yx, test_size=.3, random_state=0, stratify=yx)

for label, (cj, sel) in [("dense (boxes only)", (0, False)),
                         ("+ joints", (20, False)),
                         ("+ joints + select", (20, True))]:
    acc, dims, npair = evaluate(Xtr, ytr, Xte, yte, collapse=False,
                                n_joints=cj, select=sel, margin=1.5)
    print(f"  {label:<22} acc {acc:.3f} | axes/concept {dims:5.1f} | joints added {npair}")

# ============================================================ B) covtype
print("\n" + "=" * 70)
print("B) Covtype, crystal mode — real 7-class, confusable")
print("=" * 70)
d = fetch_covtype()
X, Y = d.data, d.target
# stratified subsample: up to 2000 per class
idx = np.concatenate([rng.choice(np.where(Y == c)[0],
                                 min(2000, (Y == c).sum()), replace=False)
                      for c in np.unique(Y)])
X, Y = X[idx], Y[idx]
Xtr, Xte, ytr, yte = train_test_split(X, Y, test_size=.3, random_state=0, stratify=Y)
sc = StandardScaler().fit(Xtr)
Xtr_s, Xte_s = sc.transform(Xtr), sc.transform(Xte)

mlp = MLPClassifier((256, 128, 64), max_iter=400, random_state=42).fit(Xtr_s, ytr)
net_acc = (mlp.predict(Xte_s) == yte).mean()
H_tr = extract_sklearn_mlp(mlp, Xtr_s)
H_te = extract_sklearn_mlp(mlp, Xte_s)
print(f"  source net accuracy: {net_acc:.3f}   (hidden dim {H_tr.shape[1]})\n")

print(f"  {'config':<26}{'acc':>7}{'axes/concept':>14}{'joints':>8}")
print("  " + "-" * 54)
configs = [("dense baseline",            dict(collapse=False, n_joints=0,  select=False)),
           ("+ collapse",                dict(collapse=True,  n_joints=0,  select=False)),
           ("+ collapse + joints",       dict(collapse=True,  n_joints=20, select=False)),
           ("+ collapse + select",       dict(collapse=True,  n_joints=0,  select=True)),
           ("+ collapse + joints + sel", dict(collapse=True,  n_joints=20, select=True))]
for label, kw in configs:
    acc, dims, npair = evaluate(H_tr, ytr, H_te, yte, **kw)
    print(f"  {label:<26}{acc:>7.3f}{dims:>14.1f}{npair:>8}")
