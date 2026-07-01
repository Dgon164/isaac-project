"""
experiment_matcher.py
=====================
Isolate the DECISION RULE. Same representation, same per-concept committed sets;
two matchers:
  - counting     : score = # committed-and-satisfied, argmax  (the old rule)
  - deepest-key  : fire iff all committed satisfied; most-resolved fires wins;
                   partial fallback                            (the new rule)

If deepest-key matches counting, the identity frame is free and cleaner. If it
wins where ids subsume (some classes commit more digits than others), the bind
+ significant-digits resolution mattered. If it loses, the brittleness bites and
the grain needs to absorb noise before strict identity pays.
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
                              build_general_concepts, per_concept_resolution_mask,
                              quantize_fit, quantize_apply)

rng = np.random.default_rng(0)


def run(H_tr, y_tr, H_te, y_te, collapse=False, n_joints=0, tag=""):
    if collapse:
        H_tr, groups = collapse_redundant(H_tr, 0.8)
        H_te = np.column_stack([H_te[:, g].mean(1) for g in groups])
    if n_joints:
        _, pairs = joint_axes(H_tr, y_tr, k=n_joints)
        if pairs:
            mu = H_tr.mean(0)
            ctr = lambda M: [ (M[:, a]-mu[a])*(M[:, b]-mu[b]) for a, b in pairs]
            H_tr = np.column_stack([H_tr] + ctr(H_tr))
            H_te = np.column_stack([H_te] + ctr(H_te))

    Xq_tr, qlo, qhi = quantize_fit(H_tr)
    Xq_te = quantize_apply(H_te, qlo, qhi)
    concepts = build_general_concepts(Xq_tr, y_tr)
    fs = FastScorer(concepts)

    # baseline: dense counting (all axes committed, tally)
    dense = (fs.predict_q(Xq_te) == y_te).mean()

    # per-concept committed sets (varying significant digits)
    mask = per_concept_resolution_mask(Xq_tr, y_tr)
    fs.set_mask(mask)
    digits = mask.sum(1)

    count_acc = (fs.predict_q(Xq_te) == y_te).mean()
    deep_pred, det = fs.predict_q_deepest(Xq_te, return_detail=True)
    deep_acc = (deep_pred == y_te).mean()
    fired = det["any_fired"].mean()
    avg_pred, adet = fs.predict_q_avgdiff(Xq_te, return_detail=True)
    avg_acc = (avg_pred == y_te).mean()

    print(f"  {tag}")
    print(f"    dense counting (all axes)      acc {dense:.3f}")
    print(f"    per-concept mask + counting    acc {count_acc:.3f}")
    print(f"    per-concept mask + deepest-key acc {deep_acc:.3f}   "
          f"(a concept fired for {fired*100:.0f}% of samples)")
    print(f"    per-concept mask + avg-diff    acc {avg_acc:.3f}")
    print(f"    committed digits per id: min {digits.min():.0f} "
          f"max {digits.max():.0f} mean {digits.mean():.1f}\n")


print("=" * 68)
print("A) XOR, raw mode (+joint)")
print("=" * 68)
n = 4000
s1, s2 = rng.normal(size=n), rng.normal(size=n)
yx = ((s1 > 0) ^ (s2 > 0)).astype(int)
Xx = np.column_stack([s1, s2, rng.normal(size=(n, 8))])
Xtr, Xte, ytr, yte = train_test_split(Xx, yx, test_size=.3, random_state=0, stratify=yx)
run(Xtr, ytr, Xte, yte, collapse=False, n_joints=20, tag="XOR raw + joints")

print("=" * 68)
print("B) Covtype, crystal mode")
print("=" * 68)
d = fetch_covtype()
X, Y = d.data, d.target
idx = np.concatenate([rng.choice(np.where(Y == c)[0], min(1500, (Y == c).sum()),
                                 replace=False) for c in np.unique(Y)])
X, Y = X[idx], Y[idx]
Xtr, Xte, ytr, yte = train_test_split(X, Y, test_size=.3, random_state=0, stratify=Y)
sc = StandardScaler().fit(Xtr)
mlp = MLPClassifier((256, 128, 64), max_iter=300, random_state=42).fit(sc.transform(Xtr), ytr)
net = (mlp.predict(sc.transform(Xte)) == yte).mean()
H_tr = extract_sklearn_mlp(mlp, sc.transform(Xtr))
H_te = extract_sklearn_mlp(mlp, sc.transform(Xte))
print(f"  source net acc {net:.3f}\n")
run(H_tr, ytr, H_te, yte, collapse=True, n_joints=20, tag="covtype crystal + collapse + joints")
