"""
HIGGS through Isaac's NEW contrast mechanism (user's design).
Two reinforced interpretations per node -> HIS compare() nulls the shared,
crystallizes the residual (the difference, the bump) -> decide by the residual.
order=2 makes the cells compound (his binding) for joint/high-order structure.

Run:  PYTHONUTF8=1 python -u higgs_contrast.py
"""
import sys, time
sys.path.insert(0, "..")
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from isaac import Isaac
from higgs_bench import load_higgs


def main():
    print("loading HIGGS..."); X, y = load_higgs()
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=0, stratify=y)
    Xtr, ytr = Xtr[:40000], ytr[:40000]; Xte, yte = Xte[:5000], yte[:5000]
    sc = StandardScaler().fit(Xtr); Xtr, Xte = sc.transform(Xtr), sc.transform(Xte)
    isaac = Isaac()

    print("=" * 60)
    print("  HIGGS via his CONTRAST comparator   (chance ~0.53)")
    print("=" * 60)
    for order, mode, name in [(1, "set", "order-1  his compare() set"),
                              (1, "soft", "order-1  log-contrast residual"),
                              (2, "soft", "order-2  COMPOUND (his binding)")]:
        t = time.time()
        info = isaac.crystallize_contrast(Xtr, ytr, order=order)
        acc = (isaac.classify_contrast(Xte, mode=mode) == yte).mean()
        print(f"  {name:<34}acc {acc:.3f}   "
              f"(resid a/b={info['only_a']}/{info['only_b']}, {time.time()-t:.1f}s)")
    print("=" * 60)
    print("  ref: box(his) 0.525 | logistic 0.642 | RF 0.721 | HGB 0.726 | deep AUC 0.88")
    print("  READ: contrast > box = nulling-the-shared beats describing-each-class.")


if __name__ == "__main__":
    main()
