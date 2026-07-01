"""
HIGGS through HIS PROCESSING MATRIX (user's actual design).
Not external dicts. Load every event into his net as a token-sequence ending in
its class; let HIS compile build the cumulative co-occurrence matrix W and
column-normalize it (W/col_sums = differentiate-vs-baseline, the shared factored
out); classify by HIS matmul (W_norm @ x) — the comparison happens IN the matrix.
The cumulative structure of all events is the baseline each input registers against.

Run:  PYTHONUTF8=1 python -u higgs_matrix.py
"""
import sys, time
sys.path.insert(0, "..")
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from isaac import Isaac
from higgs_bench import load_higgs

NBINS = 8                      # quantization levels per feature (fewer = more recurrence)
NTR, NTE = 15000, 3000
MAXCTX = 5


def glyphs(row, edges):
    """one event -> feature-tagged discrete glyphs (his native input)."""
    return [f"{j}_{int(np.digitize(v, edges[j]))}" for j, v in enumerate(row)]


def main():
    print("loading HIGGS..."); X, y = load_higgs()
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=0, stratify=y)
    Xtr, ytr = Xtr[:NTR], ytr[:NTR]; Xte, yte = Xte[:NTE], yte[:NTE]
    sc = StandardScaler().fit(Xtr); Xtr, Xte = sc.transform(Xtr), sc.transform(Xte)
    edges = [np.quantile(Xtr[:, j], np.linspace(0.05, 0.95, NBINS - 1)) for j in range(Xtr.shape[1])]
    cls = {0: "BKG", 1: "SIG"}

    isaac = Isaac()
    print("loading ALL events into his processing matrix...")
    t = time.time()
    for row, lab in zip(Xtr, ytr):
        isaac.observe(glyphs(row, edges) + [cls[lab]])      # event -> sequence ending in class
    info = isaac.compile(max_context=MAXCTX)                 # cumulative W, column-normalized
    print(f"  observed {len(Xtr)} events; matrix {info['matrix_shape']}, "
          f"{info['frames']} frames, {time.time()-t:.0f}s")

    print("=" * 56)
    print("  HIGGS via his matrix  (W_norm @ x; chance ~0.53)")
    print("=" * 56)
    t = time.time(); correct = 0; abst = 0
    for row, lab in zip(Xte, yte):
        ctx = glyphs(row, edges)
        sS = isaac._route(ctx, mode="check", target="SIG")[1]   # his matmul, per class
        sB = isaac._route(ctx, mode="check", target="BKG")[1]
        if sS == 0 and sB == 0:
            abst += 1; pred = 1            # no matching frames -> guess majority
        else:
            pred = 1 if sS >= sB else 0
        correct += (pred == lab)
    acc = correct / len(yte)
    print(f"  his-matrix differential acc : {acc:.3f}   ({abst} abstained, {time.time()-t:.0f}s)")
    print("=" * 56)
    print("  ref: box(his) 0.525 | contrast(his) 0.620 | logistic 0.642 | RF 0.721")
    print("  READ: did loading all events into his matrix + matmul-vs-baseline")
    print("  differentiate the signal? this is the decision running IN him.")


if __name__ == "__main__":
    main()
