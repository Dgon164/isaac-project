"""
HIGGS THROUGH ISAAC — his way (Rule 1: the decision runs IN him).
Not the numpy harness crystal(): we register HIS lens node (fit_lens: strip-DC,
Fisher dim-select, optional random lift), crystallize HIGGS events into
box-concept NODES in his net (crystallize_features), and let HIS membership +
centroid decide (classify_features). Same engine that holds his language/math.

Run:  PYTHONUTF8=1 python -u higgs_isaac.py
"""
import sys, time
sys.path.insert(0, "..")
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from isaac import Isaac, tokenize
from higgs_bench import load_higgs


def run(isaac, Xtr, ytr, Xte, yte, lens_cfg, name):
    if lens_cfg is None:
        lens = None
    else:
        isaac.fit_lens("higgs", Xtr, ytr, **lens_cfg); lens = "higgs"
    isaac.crystallize_features(Xtr, ytr, lens=lens)
    t = time.time()
    acc = (isaac.classify_features(Xte) == yte).mean()
    print(f"  {name:<34}acc {acc:.3f}   ({time.time()-t:.1f}s, his loop)")


def main():
    print("loading HIGGS..."); X, y = load_higgs()
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=0, stratify=y)
    Xtr, ytr = Xtr[:40000], ytr[:40000]; Xte, yte = Xte[:5000], yte[:5000]
    sc = StandardScaler().fit(Xtr); Xtr, Xte = sc.transform(Xtr), sc.transform(Xte)

    isaac = Isaac()
    # prove the events will COEXIST with his language, not replace it
    isaac.observe(tokenize("the cat sat ."))
    print(f"nodes before transplant: {len(isaac.net.all_nodes())}")
    print("=" * 56)
    print("  HIGGS through Isaac  (chance acc ~0.53)")
    print("=" * 56)
    run(isaac, Xtr, ytr, Xte, yte, None,                              "his boxes, no lens (raw 28-d)")
    run(isaac, Xtr, ytr, Xte, yte, dict(lift=0, select=14),          "his lens: strip-DC + Fisher-14")
    run(isaac, Xtr, ytr, Xte, yte, dict(lift=0, select=6),           "his lens: strip-DC + Fisher-6")
    run(isaac, Xtr, ytr, Xte, yte, dict(lift=512, select=40),        "his lens: lift-512 + Fisher-40")
    print("=" * 56)
    print(f"nodes after: {len(isaac.net.all_nodes())}  (boxes are nodes beside language)")
    print("language still works:", " ".join(isaac.generate("cat")))
    print("ref: logistic 0.642, RF 0.721, HGB 0.726, deep-net AUC ~0.88")


if __name__ == "__main__":
    main()
