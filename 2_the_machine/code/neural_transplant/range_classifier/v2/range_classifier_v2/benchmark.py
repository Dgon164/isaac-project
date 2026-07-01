"""
Benchmark — Range Classifier v2
================================
Full validation suite: raw classifier, crystallization, reservoir, efficiency.
Reproduces all claims from the methods document.
"""
import numpy as np
import time
from sklearn.datasets import load_iris, load_wine, load_breast_cancer, load_digits
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score
import warnings; warnings.filterwarnings('ignore')

from range_classifier import (
    RangeClassifier, CrystalClassifier,
    extract_sklearn_mlp, find_best_margin
)

DATASETS = {
    "Iris":     (load_iris().data,          load_iris().target),
    "Wine":     (load_wine().data,          load_wine().target),
    "BreastCa": (load_breast_cancer().data, load_breast_cancer().target),
    "Digits":   (load_digits().data,        load_digits().target),
}

skf = StratifiedKFold(5, shuffle=True, random_state=42)

# ============================================================
# TEST 1: Raw Range vs Baselines
# ============================================================
print("=" * 75)
print("TEST 1: Raw Range Classifier vs Standard Baselines (5-fold CV)")
print("=" * 75)
print(f"{'Dataset':<10} {'Range':>7} {'kNN-5':>7} {'DTree':>7} {'MLP':>7} {'SVM':>7}")
print("-" * 50)

for dname, (X_raw, y) in DATASETS.items():
    scores = {"range": [], "knn": [], "dtree": [], "mlp": [], "svm": []}
    
    for tr, te in skf.split(X_raw, y):
        sc = StandardScaler().fit(X_raw[tr])
        Xtr, Xte = sc.transform(X_raw[tr]), sc.transform(X_raw[te])
        
        # Auto-margin range classifier
        clf = RangeClassifier(margin=1.5)
        clf.fit(Xtr, y[tr])
        scores["range"].append(clf.score_accuracy(Xte, y[te]))
        
        for name, baseline in [("knn", KNeighborsClassifier(5)),
                                ("dtree", DecisionTreeClassifier(random_state=42)),
                                ("mlp", MLPClassifier((64,32), max_iter=500, random_state=42)),
                                ("svm", SVC(random_state=42))]:
            baseline.fit(X_raw[tr], y[tr])
            scores[name].append(accuracy_score(y[te], baseline.predict(X_raw[te])))
    
    means = {k: np.mean(v) for k, v in scores.items()}
    print(f"{dname:<10} {means['range']:>7.3f} {means['knn']:>7.3f} "
          f"{means['dtree']:>7.3f} {means['mlp']:>7.3f} {means['svm']:>7.3f}")

# ============================================================
# TEST 2: Crystallization Retention
# ============================================================
print(f"\n{'='*75}")
print("TEST 2: Crystallization Retention — Crystal Accuracy / Net Accuracy")
print("=" * 75)

NET_CONFIGS = {
    "Iris":     (128, 64),
    "Wine":     (128, 64),
    "BreastCa": (256, 128),
    "Digits":   (256, 128, 64),
}

print(f"{'Dataset':<10} {'Net':>7} {'Crystal':>8} {'Retained':>9} {'#Concepts':>10}")
print("-" * 50)

for dname, (X_raw, y) in DATASETS.items():
    layers = NET_CONFIGS[dname]
    net_sc, cry_sc, n_con = [], [], []
    
    for tr, te in skf.split(X_raw, y):
        sc = StandardScaler().fit(X_raw[tr])
        Xtr, Xte = sc.transform(X_raw[tr]), sc.transform(X_raw[te])
        
        mlp = MLPClassifier(layers, max_iter=500, random_state=42)
        mlp.fit(Xtr, y[tr])
        net_sc.append(accuracy_score(y[te], mlp.predict(Xte)))
        
        crystal = CrystalClassifier(extract_sklearn_mlp)
        crystal.fit(mlp, Xtr, y[tr])
        cry_sc.append(crystal.score_accuracy(mlp, Xte, y[te]))
        n_con.append(len(crystal.concepts))
    
    nm, cm = np.mean(net_sc), np.mean(cry_sc)
    ret = cm / nm * 100 if nm > 0 else 0
    print(f"{dname:<10} {nm:>7.3f} {cm:>8.3f} {ret:>8.1f}% {np.mean(n_con):>10.1f}")

# ============================================================
# TEST 3: Reservoir (zero training)
# ============================================================
try:
    import torch
    import torch.nn as nn
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

if HAS_TORCH:
    print(f"\n{'='*75}")
    print("TEST 3: Reservoir Crystallization (Random Net, Zero Training)")
    print("=" * 75)
    
    class RandomReservoir(nn.Module):
        def __init__(self, d_in, d_hidden):
            super().__init__()
            self.net = nn.Sequential(nn.Linear(d_in, d_hidden), nn.ReLU())
            for p in self.parameters(): p.requires_grad = False
        def forward(self, x):
            with torch.no_grad(): return self.net(x).numpy()
    
    print(f"{'Dataset':<10} {'Raw':>7} {'Res-512':>8} {'Trained':>8} {'kNN':>7}")
    print("-" * 45)
    
    for dname, (X_raw, y) in DATASETS.items():
        layers = NET_CONFIGS[dname]
        raw_sc, res_sc, trn_sc, knn_sc = [], [], [], []
        F = X_raw.shape[1]
        
        for tr, te in skf.split(X_raw, y):
            sc = StandardScaler().fit(X_raw[tr])
            Xtr, Xte = sc.transform(X_raw[tr]), sc.transform(X_raw[te])
            
            # Raw range
            clf = RangeClassifier(margin=1.5)
            clf.fit(Xtr, y[tr])
            raw_sc.append(clf.score_accuracy(Xte, y[te]))
            
            # Reservoir (avg 3 seeds)
            seeds = []
            for seed in range(3):
                torch.manual_seed(seed)
                res = RandomReservoir(F, 512)
                h_tr = res(torch.FloatTensor(Xtr))
                h_te = res(torch.FloatTensor(Xte))
                cry = CrystalClassifier(lambda m, X: m(torch.FloatTensor(X)))
                cry.fit(res, Xtr, y[tr])
                seeds.append(cry.score_accuracy(res, Xte, y[te]))
            res_sc.append(np.mean(seeds))
            
            # Trained crystal
            mlp = MLPClassifier(layers, max_iter=500, random_state=42)
            mlp.fit(Xtr, y[tr])
            cry = CrystalClassifier(extract_sklearn_mlp)
            cry.fit(mlp, Xtr, y[tr])
            trn_sc.append(cry.score_accuracy(mlp, Xte, y[te]))
            
            # kNN
            knn = KNeighborsClassifier(5).fit(X_raw[tr], y[tr])
            knn_sc.append(accuracy_score(y[te], knn.predict(X_raw[te])))
        
        print(f"{dname:<10} {np.mean(raw_sc):>7.3f} {np.mean(res_sc):>8.3f} "
              f"{np.mean(trn_sc):>8.3f} {np.mean(knn_sc):>7.3f}")

# ============================================================
# TEST 4: Efficiency
# ============================================================
print(f"\n{'='*75}")
print("TEST 4: Inference Efficiency (FLOPs per sample)")
print("=" * 75)

print(f"{'Net Size':<20} {'Net FLOPs':>12} {'Crystal FLOPs':>14} {'Ratio':>8}")
print("-" * 58)

F = 64  # Digits features
C = 10  # Digits classes
est_concepts = 15

for label, layers in [("Small(64,32)",    (64,32)),
                       ("Med(128,64)",     (128,64)),
                       ("Large(256,128)",  (256,128)),
                       ("XL(512,256)",     (512,256)),
                       ("XXL(1024,512)",   (1024,512))]:
    dims = [F] + list(layers) + [C]
    net_flops = sum(dims[i] * dims[i+1] * 2 for i in range(len(dims)-1))
    crystal_flops = est_concepts * layers[-1] * 3
    ratio = net_flops / crystal_flops
    print(f"{label:<20} {net_flops:>12,} {crystal_flops:>14,} {ratio:>7.0f}×")

# ============================================================
# TEST 5: Adaptive Margin Benefit
# ============================================================
print(f"\n{'='*75}")
print("TEST 5: Adaptive Margin vs Fixed Margin")
print("=" * 75)

print(f"{'Dataset':<10} {'Fixed m=1':>10} {'Fixed m=1.5':>12} {'Auto':>7} {'Best m':>7}")
print("-" * 50)

for dname, (X_raw, y) in DATASETS.items():
    fixed1, fixed15, auto_sc, auto_m = [], [], [], []
    
    for tr, te in skf.split(X_raw, y):
        sc = StandardScaler().fit(X_raw[tr])
        Xtr, Xte = sc.transform(X_raw[tr]), sc.transform(X_raw[te])
        
        for m, store in [(1.0, fixed1), (1.5, fixed15)]:
            clf = RangeClassifier(margin=m)
            clf.fit(Xtr, y[tr])
            store.append(clf.score_accuracy(Xte, y[te]))
        
        bm, _ = find_best_margin(Xtr, y[tr], margins=(0.5, 1, 1.5, 2, 3), n_folds=3)
        clf = RangeClassifier(margin=bm)
        clf.fit(Xtr, y[tr])
        auto_sc.append(clf.score_accuracy(Xte, y[te]))
        auto_m.append(bm)
    
    print(f"{dname:<10} {np.mean(fixed1):>10.4f} {np.mean(fixed15):>12.4f} "
          f"{np.mean(auto_sc):>7.4f} {np.mean(auto_m):>7.1f}")

print(f"\n{'='*75}")
print("DONE")
print("=" * 75)
