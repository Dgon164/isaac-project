"""
experiment_pooled.py
====================
Your idea, built: pool several nets into ONE axis space, dedup across them, and
let selection pick whichever axes earn their place — regardless of which net
they came from.

Addressing  : each net owns a contiguous section of global dims (offset table).
              mlp local dim 3 -> global 3 ; reservoirA local 0 -> global 64 ; etc.
Meaning     : collapse runs over the whole pooled space. Axes that co-vary fold
              into one merged dim (the collapse map) whether or not they came
              from the same net. Axes that stay apart kept their own meaning.
Translation : at inference, concat the same sections in the same order, apply the
              same collapse grouping. Both tables are exact, no hashing needed.

The real question: does pooling + dedup beat the single best net, and do the
random-reservoir axes ever survive selection — or does it all collapse back into
the trained net's features? Tested with a STRONG net (should dominate) and a
WEAK net (reservoirs should get their chance).
"""
import numpy as np
import warnings; warnings.filterwarnings("ignore")
from sklearn.datasets import fetch_covtype
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier

from range_classifier import extract_sklearn_mlp
from fastscore import FastScorer
from concept_pipeline import (collapse_redundant, build_general_concepts,
                              greedy_holdout_mask, quantize_fit, quantize_apply)

rng = np.random.default_rng(0)


def reservoir(seed, d_in, d_out):
    g = np.random.default_rng(seed)
    return (g.normal(0, 1/np.sqrt(d_in), (d_in, d_out)), g.normal(0, 0.1, d_out))

def rfx(X, Wb):
    return np.maximum(0, X @ Wb[0] + Wb[1])

def live_cols(tr, te):                      # drop dead (zero-variance) units
    keep = tr.std(0) > 1e-9
    return tr[:, keep], te[:, keep]


# ----------------------------------------------------------------- data
d = fetch_covtype(); X, Y = d.data, d.target
idx = np.concatenate([rng.choice(np.where(Y == c)[0], min(2000, (Y == c).sum()),
                                 replace=False) for c in np.unique(Y)])
X, Y = X[idx], Y[idx]
Xtr, Xte, ytr, yte = train_test_split(X, Y, test_size=.3, random_state=0, stratify=Y)
sc = StandardScaler().fit(Xtr); Xtr, Xte = sc.transform(Xtr), sc.transform(Xte)

res1, res2 = reservoir(1, Xtr.shape[1], 48), reservoir(2, Xtr.shape[1], 48)


def make_sources(mlp):
    a, b = live_cols(extract_sklearn_mlp(mlp, Xtr), extract_sklearn_mlp(mlp, Xte))
    c, dd = live_cols(rfx(Xtr, res1), rfx(Xte, res1))
    e, f = live_cols(rfx(Xtr, res2), rfx(Xte, res2))
    return {"mlp": (a, b), "resA": (c, dd), "resB": (e, f)}


def pool(blocks):                            # blocks: list of (name, arr)
    off, table, cols = 0, {}, []
    for name, arr in blocks:
        table[name] = (off, off + arr.shape[1]); off += arr.shape[1]; cols.append(arr)
    return np.column_stack(cols), table


def run(names, sources, collapse=True, select=True):
    Htr, table = pool([(n, sources[n][0]) for n in names])
    Hte, _     = pool([(n, sources[n][1]) for n in names])
    raw_F = Htr.shape[1]
    groups = None
    if collapse:
        Htr, groups = collapse_redundant(Htr, corr_thr=0.8)
        Hte = np.column_stack([Hte[:, g].mean(1) for g in groups])
    Xqtr, qlo, qhi = quantize_fit(Htr); Xqte = quantize_apply(Hte, qlo, qhi)
    fs = FastScorer(build_general_concepts(Xqtr, ytr))
    selected = None
    if select:
        mask, selected = greedy_holdout_mask(Xqtr, ytr); fs.set_mask(mask)
    acc = (fs.predict_q(Xqte) == yte).mean()

    # provenance: which sections do the SELECTED merged axes trace back to?
    prov = {}
    if selected is not None and groups is not None:
        def src_of(gi):
            for nm, (a, b) in table.items():
                if a <= gi < b: return nm
            return "?"
        for gid in selected:
            key = "+".join(sorted(set(src_of(i) for i in groups[gid])))
            prov[key] = prov.get(key, 0) + 1
    return acc, fs.mean_active_dims(), raw_F, (Htr.shape[1] if collapse else raw_F), prov


for tag, iters in [("STRONG net (400 iter)", 400), ("WEAK net (12 iter)", 12)]:
    mlp = MLPClassifier((256, 128, 64), max_iter=iters, random_state=42).fit(Xtr, ytr)
    net_acc = (mlp.predict(Xte) == yte).mean()
    src = make_sources(mlp)
    print("=" * 70)
    print(f"{tag}   source-net test acc = {net_acc:.3f}")
    print("=" * 70)

    a_s, dim_s, rawF_s, colF_s, _ = run(["mlp"], src)
    a_p, dim_p, rawF_p, colF_p, prov = run(["mlp", "resA", "resB"], src)
    print(f"  single net (mlp only)   acc {a_s:.3f} | axes used {dim_s:.0f} "
          f"| pooled {rawF_s}->{colF_s} after dedup")
    print(f"  pooled (mlp+resA+resB)  acc {a_p:.3f} | axes used {dim_p:.0f} "
          f"| pooled {rawF_p}->{colF_p} after dedup")
    print(f"  provenance of selected axes: {prov}\n")
