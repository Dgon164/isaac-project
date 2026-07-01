"""
concept_pipeline.py — co-activation + sample-driven selection on the box engine
================================================================================
Three mechanisms, each empirical, each decided by "does it change what gets
confused" rather than by geometry or assertion:

  1. collapse_redundant  — fold correlated axes into one. The flat count treats
     N axes as independent; if they co-vary they are one factor counted many
     times. Collapsing makes the count tally independent differences.

  2. joint_axes          — for axis pairs that co-activate class-conditionally,
     append a derived interaction feature (centered product). A sum of marginals
     cannot encode "both-or-neither"; the joint axis can. This is the only way
     axis-aligned boxes get at interaction structure.

  3. sample_separation_mask — per concept, greedily add the axis that excludes
     the most still-confused other-class SAMPLES, stop when none helps. Set
     cover over real misclassifications, not prototype geometry (the geometry
     version is what collapsed on Digits).

All outputs feed the verified FastScorer; concepts stay plain {lo,hi,med,label}.
"""

import numpy as np
from range_classifier import quantize, build_concept
from fastscore import FastScorer


# ----------------------------------------------------- 1. redundancy collapse

def collapse_redundant(H, corr_thr=0.8):
    """Fold columns with |corr| >= corr_thr into single mean-columns.

    Returns (H_collapsed, groups) where groups is a list of original-index lists.
    Uses single-linkage connected components over the correlation graph.
    """
    F = H.shape[1]
    Hs = H - H.mean(0)
    sd = Hs.std(0)
    sd[sd == 0] = 1.0
    C = (Hs / sd).T @ (Hs / sd) / len(H)          # correlation matrix
    adj = np.abs(C) >= corr_thr
    np.fill_diagonal(adj, True)

    seen = np.zeros(F, bool)
    groups = []
    for i in range(F):
        if seen[i]:
            continue
        stack, comp = [i], []
        while stack:                               # connected component
            v = stack.pop()
            if seen[v]:
                continue
            seen[v] = True
            comp.append(v)
            stack.extend(np.where(adj[v] & ~seen)[0])
        groups.append(sorted(comp))

    H_collapsed = np.column_stack([H[:, g].mean(1) for g in groups])
    return H_collapsed, groups


# ----------------------------------------------------------- 2. joint axes

def joint_axes(H, y, k=20, min_spread=0.3):
    """Append up to k interaction features for class-conditionally co-active pairs.

    A pair is a candidate when its co-fire rate (both above their own medians)
    varies across classes by >= min_spread — i.e. the co-activation itself is
    class-defining, not global redundancy. The appended feature is the centered
    product (the canonical 2nd-order interaction term), which encodes the joint.
    """
    F = H.shape[1]
    fire = (H > np.median(H, 0)).astype(np.int8)
    classes = np.unique(y)
    Hc = H - H.mean(0)

    cand = []
    for a in range(F):
        for b in range(a + 1, F):
            co = fire[:, a] & fire[:, b]
            rates = np.array([co[y == c].mean() for c in classes])
            spread = rates.max() - rates.min()
            if spread >= min_spread:
                cand.append((spread, a, b))
    cand.sort(reverse=True)
    chosen = cand[:k]

    if not chosen:
        return H, []
    cols = [Hc[:, a] * Hc[:, b] for _, a, b in chosen]
    H_aug = np.column_stack([H] + cols)
    pairs = [(a, b) for _, a, b in chosen]
    return H_aug, pairs


# --------------------------------------------------------- concepts + mask

def build_general_concepts(Xq, y, margin=1.5, plo=1, phi=95):
    """One range concept per class (general only — isolates the new mechanisms)."""
    concepts = []
    for c in np.unique(y):
        lo, hi, med = build_concept(Xq[y == c], margin, plo, phi)
        concepts.append({"label": int(c), "lo": lo, "hi": hi, "med": med,
                         "type": "general"})
    return concepts


def sample_separation_mask(Xq, y, concepts, min_keep=1):
    """Greedy, sample-driven, minimal axis selection per concept.

    For concept i, repeatedly add the axis that pushes the most still-admitted
    other-class training samples OUT of i's box, until every other-class sample
    is excluded on some kept axis or no axis helps. Set cover over real
    confusions. Returns an (N, F) {0,1} mask for FastScorer.
    """
    N = len(concepts)
    F = len(concepts[0]["lo"])
    mask = np.zeros((N, F))
    for i, c in enumerate(concepts):
        lo, hi = c["lo"], c["hi"]
        comp = Xq[y != c["label"]]                 # other-class samples
        if len(comp) == 0:
            mask[i, :min_keep] = 1.0
            continue
        admit = (comp >= lo) & (comp <= hi)        # (Ncomp, F): True = in-range on d
        confused = np.ones(len(comp), bool)        # still looks like concept i
        used = np.zeros(F, bool)
        while confused.any():
            # gain of axis d = # confused samples it excludes (out of range)
            excl = confused[:, None] & ~admit      # (Ncomp, F)
            gain = excl.sum(0)
            gain[used] = -1
            d = int(gain.argmax())
            if gain[d] <= 0:                        # nothing more can be separated
                break
            used[d] = True
            mask[i, d] = 1.0
            confused &= admit[:, d]                 # keep only those still in-range on d
        if mask[i].sum() < min_keep:               # degenerate -> tightest axes
            for d in np.argsort(hi - lo)[:min_keep]:
                mask[i, d] = 1.0
    return mask


# ------------------------------------------------- held-out-driven selection

def greedy_holdout_mask(Xq, y, margin=1.5, tol=0.0):
    """Greedy forward axis selection driven by HELD-OUT accuracy, not training
    separation. Carve a validation split, add the axis that most improves
    validation accuracy, stop when the next one doesn't earn its place. Returns
    a shared (N, F) mask — the honest "fewest axes that preserve generalization"
    rule, contrasted with sample_separation_mask which overfits to training.
    """
    from sklearn.model_selection import train_test_split
    Xf, Xv, yf, yv = train_test_split(Xq, y, test_size=.3, random_state=1, stratify=y)
    concepts = build_general_concepts(Xf, yf, margin=margin)
    fs = FastScorer(concepts)
    N, F = len(concepts), len(concepts[0]["lo"])

    selected, best = [], -1.0
    remaining = set(range(F))
    while remaining:
        cand_best, cand_axis = best, None
        for d in list(remaining):
            m = np.zeros((N, F))
            for dd in selected + [d]:
                m[:, dd] = 1.0
            fs.set_mask(m)
            acc = (fs.predict_q(Xv) == yv).mean()
            if acc > cand_best:
                cand_best, cand_axis = acc, d
        if cand_axis is None or cand_best <= best + tol:
            break
        selected.append(cand_axis)
        remaining.discard(cand_axis)
        best = cand_best

    mask = np.zeros((N, F))
    if selected:
        for d in selected:
            mask[:, d] = 1.0
    else:
        mask[:] = 1.0
    return mask, selected


# ------------------------------------------------ per-concept resolution mask

def per_concept_resolution_mask(Xq, y, margin=1.5):
    """Give each id its own committed set, sized to what resolves it.

    For each class, greedily add the axis that most improves (recall - leakage)
    on a validation split: recall = fraction of this class's samples still inside
    the committed box, leakage = fraction of other-class samples inside it. Stop
    when no axis improves the trade. Different ids end up with different numbers
    of committed distinctions — significant digits, set per id by the data.
    """
    from sklearn.model_selection import train_test_split
    Xf, Xv, yf, yv = train_test_split(Xq, y, test_size=.3, random_state=1, stratify=y)
    concepts = build_general_concepts(Xf, yf, margin=margin)
    N = len(concepts)
    F = len(concepts[0]["lo"])
    mask = np.zeros((N, F))

    for i, c in enumerate(concepts):
        lo, hi = c["lo"], c["hi"]
        inr = (Xv >= lo) & (Xv <= hi)              # (nval, F)
        is_i = (yv == c["label"])
        fire = np.ones(len(Xv), bool)              # empty committed set fires for all
        def obj(f):
            recall = f[is_i].mean() if is_i.any() else 0.0
            leak = f[~is_i].mean() if (~is_i).any() else 0.0
            return recall - leak
        best = obj(fire)
        used = set()
        while True:
            best_axis, best_fire, best_o = None, None, best
            for d in range(F):
                if d in used:
                    continue
                f2 = fire & inr[:, d]
                o = obj(f2)
                if o > best_o:
                    best_o, best_axis, best_fire = o, d, f2
            if best_axis is None:
                break
            used.add(best_axis); fire = best_fire; best = best_o
        if not used:                               # commit at least the tightest axis
            used = {int(np.argmin(hi - lo))}
        for d in used:
            mask[i, d] = 1.0
    return mask


# ------------------------------------------------------------- quantize wrap

def quantize_fit(H):
    Xq, qlo, qhi = quantize(H)
    return Xq, qlo, qhi


def quantize_apply(H, qlo, qhi):
    Xq, _, _ = quantize(H, qlo, qhi)
    return Xq
