"""
verify_fastscore.py
===================
1. Prove FastScorer with an all-ones mask reproduces the shipped crystal's
   predictions EXACTLY on every dataset (parity check).
2. Drop in the illustrative greedy_separation_mask and measure what changes:
   accuracy and mean axes-used-per-concept (dense F vs sparse).

This measures; it does not claim the sparse policy is better. The selection
rule is still open — the point is the engine runs any mask against the baseline.
"""
import numpy as np
import warnings; warnings.filterwarnings("ignore")
from sklearn.datasets import load_iris, load_wine, load_breast_cancer, load_digits
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier

from range_classifier import CrystalClassifier, extract_sklearn_mlp
from fastscore import (FastScorer, quantize_for_crystal,
                       greedy_separation_mask, concepts_to_tensors)

DATASETS = {
    "Iris":     (load_iris(return_X_y=True),          (128, 64)),
    "Wine":     (load_wine(return_X_y=True),          (128, 64)),
    "BreastCa": (load_breast_cancer(return_X_y=True), (256, 128)),
    "Digits":   (load_digits(return_X_y=True),        (256, 128, 64)),
}

print("=" * 78)
print("PARITY CHECK  —  FastScorer(all-ones)  vs  shipped crystal.predict")
print("=" * 78)
print(f"{'Dataset':<10} {'shipped acc':>12} {'fast acc':>10} {'preds identical':>17}")
print("-" * 52)

scorers = {}
for name, ((X, y), layers) in DATASETS.items():
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=.3,
                                          random_state=0, stratify=y)
    sc = StandardScaler().fit(Xtr)
    Xtr_s, Xte_s = sc.transform(Xtr), sc.transform(Xte)
    mlp = MLPClassifier(layers, max_iter=500, random_state=42).fit(Xtr_s, ytr)
    crystal = CrystalClassifier(extract_sklearn_mlp).fit(mlp, Xtr_s, ytr)

    shipped = crystal.predict(mlp, Xte_s)                     # shipped path
    fs = FastScorer.from_crystal(crystal)                     # all-ones
    Xq = quantize_for_crystal(crystal, mlp, Xte_s)
    fast = fs.predict_q(Xq)                                   # vectorized path

    identical = bool(np.array_equal(shipped, fast))
    print(f"{name:<10} {(shipped==yte).mean():>12.4f} "
          f"{(fast==yte).mean():>10.4f} {str(identical):>17}")
    scorers[name] = (fs, Xq, yte, crystal)

print("\n" + "=" * 78)
print("SPARSE MASK  —  illustrative greedy_separation_mask (count-only specificity)")
print("=" * 78)
print(f"{'Dataset':<10} {'dense acc':>10} {'dense dims':>11} "
      f"{'sparse acc':>11} {'sparse dims':>12}")
print("-" * 58)

for name, (fs, Xq, yte, crystal) in scorers.items():
    dense_pred = fs.predict_q(Xq)
    dense_acc, dense_dims = (dense_pred == yte).mean(), fs.F

    mask = greedy_separation_mask(fs.LO, fs.HI, fs.MED, fs.labels)
    fs.set_mask(mask)
    sparse_pred = fs.predict_q(Xq)
    sparse_acc, sparse_dims = (sparse_pred == yte).mean(), fs.mean_active_dims()
    fs.set_mask(None)

    print(f"{name:<10} {dense_acc:>10.4f} {dense_dims:>11d} "
          f"{sparse_acc:>11.4f} {sparse_dims:>12.1f}")
