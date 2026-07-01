"""
Quickstart — Range Classifier v2
=================================
Run this file to see all three use modes:
  1. Raw range classifier (no neural net)
  2. Crystallize a trained MLP
  3. Inspect what the model learned
"""
import numpy as np
from sklearn.datasets import load_iris, load_wine, load_breast_cancer, load_digits
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score

from range_classifier import (
    RangeClassifier, CrystalClassifier,
    extract_sklearn_mlp, find_best_margin
)

# ============================================================
# 1. RAW RANGE CLASSIFIER
# ============================================================
print("=" * 60)
print("1. RAW RANGE CLASSIFIER (no neural net)")
print("=" * 60)

data = load_iris()
X_tr, X_te, y_tr, y_te = train_test_split(
    data.data, data.target, test_size=0.2, random_state=42
)

# Scale
sc = StandardScaler().fit(X_tr)
X_tr_s, X_te_s = sc.transform(X_tr), sc.transform(X_te)

# Fit
clf = RangeClassifier(margin=1.5, percentile_lo=1, percentile_hi=95)
clf.fit(X_tr_s, y_tr,
        feature_names=list(data.feature_names),
        class_names={0: "setosa", 1: "versicolor", 2: "virginica"})

acc = clf.score_accuracy(X_te_s, y_te)
print(f"\nIris accuracy: {acc:.3f}")
print(f"Concepts: {len(clf.concepts)}")

# Inspect
clf.inspect()
clf.discrimination_report()

# ============================================================
# 2. CRYSTALLIZE A TRAINED MLP
# ============================================================
print("\n\n" + "=" * 60)
print("2. CRYSTALLIZE A TRAINED MLP")
print("=" * 60)

data = load_digits()
X_tr, X_te, y_tr, y_te = train_test_split(
    data.data, data.target, test_size=0.2, random_state=42
)
sc = StandardScaler().fit(X_tr)
X_tr_s, X_te_s = sc.transform(X_tr), sc.transform(X_te)

# Train the net
mlp = MLPClassifier((256, 128, 64), max_iter=500, random_state=42)
mlp.fit(X_tr_s, y_tr)
net_acc = accuracy_score(y_te, mlp.predict(X_te_s))

# Crystallize
crystal = CrystalClassifier(extract_sklearn_mlp)
crystal.fit(mlp, X_tr_s, y_tr)
cry_acc = crystal.score_accuracy(mlp, X_te_s, y_te)

print(f"\nDigits — MLP accuracy:     {net_acc:.4f}")
print(f"Digits — Crystal accuracy: {cry_acc:.4f}")
print(f"Retention: {cry_acc/net_acc*100:.1f}%")
print(f"Concepts: {len(crystal.concepts)}")

# Inspect top features per concept
crystal.inspect(top_n_features=5)

# ============================================================
# 3. ADAPTIVE MARGIN
# ============================================================
print("\n\n" + "=" * 60)
print("3. ADAPTIVE MARGIN (auto-tuned)")
print("=" * 60)

data = load_wine()
X_tr, X_te, y_tr, y_te = train_test_split(
    data.data, data.target, test_size=0.2, random_state=42
)
sc = StandardScaler().fit(X_tr)
X_tr_s, X_te_s = sc.transform(X_tr), sc.transform(X_te)

best_margin, cv_score = find_best_margin(X_tr_s, y_tr)
print(f"\nBest margin: {best_margin} (CV score: {cv_score:.4f})")

clf = RangeClassifier(margin=best_margin)
clf.fit(X_tr_s, y_tr, feature_names=list(data.feature_names))
acc = clf.score_accuracy(X_te_s, y_te)
print(f"Wine accuracy with auto margin: {acc:.4f}")

# ============================================================
# 4. EXPORT / LOAD (portable model)
# ============================================================
print("\n\n" + "=" * 60)
print("4. EXPORT / LOAD")
print("=" * 60)

import json

model_data = clf.export()
json_str = json.dumps(model_data)
print(f"Model size: {len(json_str):,} bytes")
print(f"Concepts: {len(model_data['concepts'])}")

# Reload
clf2 = RangeClassifier.load(json.loads(json_str))
acc2 = clf2.score_accuracy(X_te_s, y_te)
print(f"Reloaded model accuracy: {acc2:.4f} (matches: {acc == acc2})")

# ============================================================
# 5. DETAILED PREDICTIONS (explainable)
# ============================================================
print("\n\n" + "=" * 60)
print("5. EXPLAINABLE PREDICTIONS")
print("=" * 60)

data = load_iris()
X_tr, X_te, y_tr, y_te = train_test_split(
    data.data, data.target, test_size=0.2, random_state=42
)
sc = StandardScaler().fit(X_tr)
X_tr_s, X_te_s = sc.transform(X_tr), sc.transform(X_te)

clf = RangeClassifier(margin=1.5)
clf.fit(X_tr_s, y_tr,
        class_names={0: "setosa", 1: "versicolor", 2: "virginica"})

details = clf.predict_detail(X_te_s)

# Show first 5 predictions with reasoning
names = {0: "setosa", 1: "versicolor", 2: "virginica"}
for i in range(5):
    d = details[i]
    true = names[y_te[i]]
    pred = names[d["prediction"]]
    correct = "✓" if d["prediction"] == y_te[i] else "✗"
    top = d["scores"][0]
    runner = d["scores"][1]
    
    print(f"\nSample {i}: true={true}, predicted={pred} {correct}")
    print(f"  Winner: {names[top['label']]} — {top['count']}/{d['total_dims']} dims in range, dist={top['dist']:.1f}")
    print(f"  Runner: {names[runner['label']]} — {runner['count']}/{d['total_dims']} dims in range, dist={runner['dist']:.1f}")
    print(f"  Margin: {d['margin']} dimensions")
