"""
TWO CONSTRAINTS — proximity (what's nearby) x feasibility (what can thrive here).
ABC=D: two known slots constrain the empty one. Feasibility rules out; proximity
ranks what survives; their AGREEMENT is a confidence/honesty signal.

  proximity  = kNN neighbor vote distribution (the spatial/lookup signal)
  feasibility= per-class range membership (the terrain/ecology signal)
  combined   = proximity * feasibility  (must be near AND feasible)

Key question isn't just 'is combined more accurate' — it's 'when the two AGREE,
is it reliable, and when they CONFLICT, does it correctly flag uncertainty?'
"""
import numpy as np
from sklearn.datasets import fetch_covtype
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier

RNG = np.random.default_rng(0)
X, y = fetch_covtype(return_X_y=True)
idx = RNG.choice(len(X), 40000, replace=False); X, y = X[idx], y[idx]
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=.3, random_state=1, stratify=y)
sc = StandardScaler().fit(Xtr); Xtr_s, Xte_s = sc.transform(Xtr), sc.transform(Xte)
classes = np.array(sorted(np.unique(ytr)))

# --- proximity: kNN neighbor votes ---
knn = KNeighborsClassifier(15).fit(Xtr_s, ytr)
prox = knn.predict_proba(Xte_s)                      # (n, C) fraction of neighbors per class

# --- feasibility: per-class feature-range membership (the terrain box) ---
lo = {c: np.percentile(Xtr_s[ytr == c], 2, 0) for c in classes}
hi = {c: np.percentile(Xtr_s[ytr == c], 98, 0) for c in classes}
feas = np.stack([((Xte_s >= lo[c]) & (Xte_s <= hi[c])).mean(1) for c in classes], 1)  # (n,C)

comb = prox * feas                                   # AND: near AND feasible

def acc(P, m=None):
    P = classes[P.argmax(1)]
    return (P[m] == yte[m]).mean() if m is not None else (P == yte).mean()

pred_prox = classes[prox.argmax(1)]
pred_feas = classes[feas.argmax(1)]
pred_comb = classes[comb.argmax(1)]

print("=" * 60)
print("  TWO CONSTRAINTS on covtype (random split, n=12000 test)")
print("=" * 60)
print(f"  proximity alone (kNN-15)   : {(pred_prox==yte).mean():.3f}")
print(f"  feasibility alone (box)    : {(pred_feas==yte).mean():.3f}")
print(f"  combined (proximity x feas): {(pred_comb==yte).mean():.3f}")

# --- the honesty signal: do the two constraints agree? ---
agree = pred_prox == pred_feas
print("\n  CALIBRATION — does agreement predict reliability?")
print(f"  they AGREE   : {agree.mean():.0%} of cells, accuracy {(pred_prox[agree]==yte[agree]).mean():.3f}  <- COMMIT")
print(f"  they CONFLICT: {(~agree).mean():.0%} of cells, accuracy {(pred_comb[~agree]==yte[~agree]).mean():.3f}  <- GUESS / abstain")
print("\n  If agree-accuracy >> conflict-accuracy, the two-constraint check is a")
print("  real honesty signal: it knows when it knows. That's the committed-vs-")
print("  free-guess split, falling out of 'near AND feasible'.")
