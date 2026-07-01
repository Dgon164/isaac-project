"""
INTERACTION RETEST — the box-face of the binding gap.

Flat axis-aligned boxes (independent per-dim scoring) provably can't do XOR:
class0 sits at corners (0,0)&(1,1), class1 at (0,1)&(1,0) — the boxes overlap on
every single dimension, so independent voting is chance. This is box-hostility in
its purest form: the answer is in the INTERACTION, not any dimension.

The binding fix = compound doors = interaction features (centered pairwise
products). Add them and the conjunction becomes its own axis — boxes separate it.
Same primitive as the node router (condition on a combination), box surface.
"""
import numpy as np
rng = np.random.default_rng(0)

N = 2000
f0 = rng.integers(0, 2, N); f1 = rng.integers(0, 2, N)
y = f0 ^ f1                                    # XOR — the interaction label
X = np.stack([f0 + rng.normal(0, .08, N), f1 + rng.normal(0, .08, N)], 1)
X = np.concatenate([X, rng.normal(0, 1, (N, 4))], 1)   # + 4 noise dims
tr, te = slice(0, 1500), slice(1500, None)


def box_acc(Xtr, ytr, Xte, yte):
    """One axis-aligned box per class (percentile range); score = count in-range."""
    boxes = {c: (np.percentile(Xtr[ytr == c], 5, 0), np.percentile(Xtr[ytr == c], 95, 0))
             for c in np.unique(ytr)}
    def pred(X):
        out = []
        for x in X:
            best, bc = None, -1
            for c, (lo, hi) in boxes.items():
                cnt = int(((x >= lo) & (x <= hi)).sum())
                if cnt > bc: bc, best = cnt, c
            out.append(best)
        return np.array(out)
    return (pred(Xte) == yte).mean()


def add_interactions(X):
    """Compound doors: centered pairwise products (the conjunction as a new axis)."""
    Xc = X - X.mean(0)
    comps = [Xc[:, a] * Xc[:, b] for a in range(X.shape[1]) for b in range(a + 1, X.shape[1])]
    return np.concatenate([X, np.stack(comps, 1)], 1)


flat = box_acc(X[tr], y[tr], X[te], y[te])
Xi = add_interactions(X)
bound = box_acc(Xi[tr], y[tr], Xi[te], y[te])

print("=" * 60)
print("  INTERACTION RETEST (XOR — pure box-hostility)")
print("=" * 60)
print(f"  flat boxes (independent dims) : {flat:.3f}   <- chance; can't bind")
print(f"  + compound doors (interactions): {bound:.3f}   <- binding resolves it")
print("=" * 60)
print("  Same primitive as the node router: condition the answer on a")
print("  COMBINATION, not independent parts. Node-face = routing by sense;")
print("  box-face = compound doors. One missing primitive, both surfaces.")
