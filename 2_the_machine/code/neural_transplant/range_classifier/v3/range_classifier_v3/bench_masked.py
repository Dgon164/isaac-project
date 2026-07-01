"""
Benchmark — Vectorized / Masked Crystal vs the dense crystal
============================================================
For each dataset, 5-fold CV:
  - train the source MLP, fit the dense CrystalClassifier
  - wrap it with MaskedCrystal(all-ones)      -> must reproduce the crystal exactly
  - wrap it with MaskedCrystal(discriminative) -> minimal "useful axes" mask

Reports two things:
  TABLE A  accuracy + the all-ones correctness check
  TABLE B  what the mask did: dims used per concept, and how often the decision was
           made on count alone vs falling through to the distance tiebreak.
"""
import numpy as np, warnings; warnings.filterwarnings("ignore")
from sklearn.datasets import load_iris, load_wine, load_breast_cancer, load_digits
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score

from range_classifier import CrystalClassifier, extract_sklearn_mlp
from vectorized_crystal import MaskedCrystal, mask_all_ones, mask_discriminative

DATASETS = {
    "Iris":     (load_iris().data,          load_iris().target),
    "Wine":     (load_wine().data,          load_wine().target),
    "BreastCa": (load_breast_cancer().data, load_breast_cancer().target),
    "Digits":   (load_digits().data,        load_digits().target),
}
NET_CONFIGS = {"Iris": (128, 64), "Wine": (128, 64),
               "BreastCa": (256, 128), "Digits": (256, 128, 64)}
skf = StratifiedKFold(5, shuffle=True, random_state=42)

rows = {}
for dname, (X, y) in DATASETS.items():
    layers = NET_CONFIGS[dname]
    acc = {"net": [], "dense": [], "masked": []}
    match, F, mdims = [], [], []
    bycount = {"dense": [], "masked": []}

    for tr, te in skf.split(X, y):
        sc = StandardScaler().fit(X[tr])
        Xtr, Xte = sc.transform(X[tr]), sc.transform(X[te])

        mlp = MLPClassifier(layers, max_iter=500, random_state=42).fit(Xtr, y[tr])
        acc["net"].append(accuracy_score(y[te], mlp.predict(Xte)))

        crystal = CrystalClassifier(extract_sklearn_mlp).fit(mlp, Xtr, y[tr])
        ref = crystal.predict(mlp, Xte)
        acc["dense"].append((ref == y[te]).mean())

        ones = MaskedCrystal(crystal, mask_all_ones)
        p_ones, info_ones = ones.predict(mlp, Xte, detail=True)
        match.append((p_ones == ref).mean())                 # correctness check
        bycount["dense"].append(info_ones["by_count"].mean())

        msk = MaskedCrystal(crystal, mask_discriminative)
        p_msk, info_msk = msk.predict(mlp, Xte, detail=True)
        acc["masked"].append((p_msk == y[te]).mean())
        bycount["masked"].append(info_msk["by_count"].mean())
        F.append(ones.LO.shape[1])
        mdims.append(msk.active_dims_per_concept())

    rows[dname] = dict(
        net=np.mean(acc["net"]), dense=np.mean(acc["dense"]),
        masked=np.mean(acc["masked"]), match=np.mean(match),
        F=int(np.mean(F)), mdims=np.mean(mdims),
        bc_dense=np.mean(bycount["dense"]), bc_msk=np.mean(bycount["masked"]),
    )

print("=" * 70)
print("TABLE A — accuracy & exactness")
print("=" * 70)
print(f"{'Dataset':<10}{'Net':>8}{'Dense':>8}{'Masked':>8}{'AllOnes=Dense':>16}")
print("-" * 50)
for d, r in rows.items():
    print(f"{d:<10}{r['net']:>8.3f}{r['dense']:>8.3f}{r['masked']:>8.3f}"
          f"{r['match']:>15.3f}")

print(f"\n{'='*70}")
print("TABLE B — what the discriminative mask did")
print("=" * 70)
print(f"{'Dataset':<10}{'Dims':>7}{'MaskDims':>10}{'Dense:byCount':>15}{'Mask:byCount':>14}")
print("-" * 56)
for d, r in rows.items():
    print(f"{d:<10}{r['F']:>7}{r['mdims']:>10.1f}{r['bc_dense']:>14.0%}{r['bc_msk']:>14.0%}")

print(f"\n{'='*70}")
print("Dims        = hidden dims available per concept (dense uses all of them)")
print("MaskDims    = mean dims a concept actually counts under the discriminative mask")
print("byCount     = share of test decisions won on count alone (rest go to tiebreak)")
print("=" * 70)
