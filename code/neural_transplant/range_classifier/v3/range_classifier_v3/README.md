# Range Classifier v2

Classification via per-dimension range membership. No weights, no gradients, no activation functions.

## What it does

A concept is a bounding box in feature space: per-dimension `[lo, hi]` with a median prototype. Classification counts how many dimensions of an observation fall within a concept's range. The concept with the highest count wins. Median distance breaks ties.

Three modes:

1. **Raw classifier** — Build range concepts directly from features. No neural net needed.
2. **Crystal classifier** — Extract a trained neural net's hidden representations into range concepts. Retains 98–100% of the net's accuracy at a fraction of inference cost.
3. **Reservoir crystal** — Crystallize a random (untrained) net. Competitive accuracy with zero training.

## Quick start

```python
from range_classifier import RangeClassifier, CrystalClassifier, extract_sklearn_mlp

# Mode 1: Raw
clf = RangeClassifier(margin=1.5, percentile_lo=1, percentile_hi=95)
clf.fit(X_train, y_train, feature_names=["feat_a", "feat_b", ...])
predictions = clf.predict(X_test)
clf.inspect()  # print what it learned

# Mode 2: Crystal from trained MLP
crystal = CrystalClassifier(extract_sklearn_mlp)
crystal.fit(trained_mlp, X_train, y_train)
predictions = crystal.predict(trained_mlp, X_test)

# Auto-tune margin
from range_classifier import find_best_margin
best_m, cv_score = find_best_margin(X_train, y_train)
```

## Key findings (validated)

| Claim | Result |
|-------|--------|
| Crystal retains 98–100% of MLP accuracy | **Confirmed** — 99.1% avg, 98.4% min |
| 4-bit quantization is optimal | **Confirmed** — more bits add noise, not signal |
| Percentile ranges outperform min/max | **Confirmed** — +0.9% on outlier-heavy datasets |
| Crystal inference 10–100× cheaper | **Confirmed** — ratio grows with net size |
| Random reservoir beats standard classifiers | **Partial** — beats DTree 3/4, kNN 2/4 |

## Files

| File | Purpose |
|------|---------|
| `range_classifier.py` | Core library — all you need |
| `quickstart.py` | Usage examples for all modes |
| `benchmark.py` | Full validation against baselines |
| `METHODS.md` | Detailed methods and theory |

## Requirements

- `numpy`
- `scikit-learn` (for benchmarks and MLP extraction)
- `torch` (optional, for reservoir experiments)

## Parameters

| Parameter | Default | What it does |
|-----------|---------|-------------|
| `margin` | 1.5 | Tolerance beyond observed range bounds |
| `percentile_lo` | 1 | Lower percentile for range boundary |
| `percentile_hi` | 95 | Upper percentile for range boundary |
| `max_splits` | 10 | Confusion resolution rounds |
| `min_group` | 3 | Minimum samples to create a variant concept |
