"""
PARTIAL FUZZY OVERLAP — give Isaac a VARIANT finder (user's idea).

His matrix matches frames EXACTLY = an INVARIANT detector (what holds every time).
HIGGS is almost all VARIANTS (patterns that occur MORE in one class, not always),
so the exact detector floors near logistic. Fix: activate each learned frame by
HOW MUCH it overlaps the event (fraction of its glyphs present), not exact match.
Then HIS matmul (W_norm @ x_fuzzy) reads class evidence over partial matches.
Fuzzy overlap captures the "sometimes" AND densifies the sparse exact frames.

Run:  PYTHONUTF8=1 python -u higgs_fuzzy.py   (builds his matrix, then fuzzy-reads it)
"""
import sys, time
sys.path.insert(0, "..")
import numpy as np
import scipy.sparse as sp
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from isaac import Isaac
from higgs_bench import load_higgs

NBINS, NTR, NTE, MAXCTX = 8, 15000, 3000, 5


def glyphs(row, edges):
    return [f"{j}_{int(np.digitize(v, edges[j]))}" for j, v in enumerate(row)]


def main():
    print("loading HIGGS..."); X, y = load_higgs()
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=0, stratify=y)
    Xtr, ytr = Xtr[:NTR], ytr[:NTR]; Xte, yte = Xte[:NTE], yte[:NTE]
    sc = StandardScaler().fit(Xtr); Xtr, Xte = sc.transform(Xtr), sc.transform(Xte)
    edges = [np.quantile(Xtr[:, j], np.linspace(0.05, 0.95, NBINS - 1)) for j in range(Xtr.shape[1])]
    cls = {0: "BKG", 1: "SIG"}

    isaac = Isaac()
    print("loading ALL events into his matrix...")
    Gtr = [glyphs(r, edges) for r in Xtr]
    for g, lab in zip(Gtr, ytr):
        isaac.observe(g + [cls[lab]])
    isaac.compile(max_context=MAXCTX)
    c = isaac._compiled
    frames, W_norm = c["frames"], c["W_norm"]; didx = c["didx"]
    print(f"  matrix {W_norm.shape}, {len(frames)} frames")

    # ---- build frame x glyph incidence (each frame = its set of glyphs) ----
    vocab = {}
    for f in frames:
        for t in f:
            if t not in vocab: vocab[t] = len(vocab)
    rows, colsv, fsize = [], [], np.zeros(len(frames), np.float32)
    for fi, f in enumerate(frames):
        s = set(f); fsize[fi] = len(s)
        for t in s:
            rows.append(fi); colsv.append(vocab[t])
    F = sp.csr_matrix((np.ones(len(rows), np.float32), (rows, colsv)),
                      shape=(len(frames), len(vocab)))            # frames x vocab
    iSIG, iBKG = didx["SIG"], didx["BKG"]

    def event_vec(g):
        v = np.zeros(len(vocab), np.float32)
        for t in g:
            if t in vocab: v[vocab[t]] = 1.0
        return v

    print("=" * 60)
    print("  HIGGS via FUZZY partial overlap of his frames  (chance ~0.53)")
    print("=" * 60)
    Gte = [glyphs(r, edges) for r in Xte]
    for p, mino in [(1.0, 0.0), (2.0, 0.0), (3.0, 0.5)]:
        t = time.time(); pred = np.empty(len(Gte), int)
        for i0 in range(0, len(Gte), 500):                       # chunk test events
            B = Gte[i0:i0+500]
            Gmat = np.stack([event_vec(g) for g in B], 1)        # vocab x b
            ov = (F @ Gmat) / fsize[:, None]                     # frame overlap fraction
            ov[ov < mino] = 0.0
            xf = ov ** p                                         # sharpen fuzzy activation
            Y = W_norm @ xf                                      # HIS matmul -> 2 x b
            pred[i0:i0+len(B)] = np.where(Y[iSIG] >= Y[iBKG], 1, 0)
        acc = (pred == yte).mean()
        print(f"  fuzzy overlap  p={p:<3} min={mino:<3}   acc {acc:.3f}   ({time.time()-t:.0f}s)")
    print("=" * 60)
    print("  ref: box 0.525 | contrast 0.620 | logistic 0.642 | his-matrix(exact) 0.650 | RF 0.721")
    print("  READ: does fuzzy partial overlap (variants) beat exact match (invariants)?")


if __name__ == "__main__":
    main()
