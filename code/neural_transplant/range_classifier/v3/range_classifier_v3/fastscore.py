"""
fastscore.py — vectorized, mask-aware scoring core for Range/Crystal classifiers
================================================================================
Drop-in replacement for the per-sample Python loop in `_classify_one`.

Design goals (from the dense-vs-minimal discussion):
  - Stream over concepts, vectorize over the batch. Never materialize the
    (B, N, F) membership tensor — that blowup is what makes the naive
    broadcast slower than the loop on CPU.
  - Pad every concept to a fixed width F and stack into dense (N, F) tensors,
    so the whole comparison is one elementwise op + a reduction. GPU-ready as
    written; on CPU it runs in tens of microseconds per sample for F < 1000.
  - Carry a per-concept 0/1 MASK that says which axes are allowed to count.
    The mask is the *only* place "which dims are useful" lives. It multiplies
    into the reduction at zero structural cost.
      * mask = all ones  -> identical predictions to the shipped dense scorer
      * mask = sparse     -> a concept only counts over its selected axes, so a
                             more-specified concept can win by COUNT rather than
                             falling through to the median-distance tiebreak.

The scoring rule reproduced exactly (per the shipped `score`/`_classify_one`):
  primary key   = count of in-range dims      (higher wins)
  tiebreaker    = -sum(|obs - med|) over those (closer to prototype wins)
  ties in both  -> lowest concept index wins  (matches the loop's strict `>`)
"""

import numpy as np
from range_classifier import quantize


# ------------------------------------------------------------------ tensors

def concepts_to_tensors(concepts):
    """Stack a list of concept dicts into dense (N, F) arrays + a label vector."""
    N = len(concepts)
    F = len(np.asarray(concepts[0]["lo"]))
    LO = np.empty((N, F)); HI = np.empty((N, F)); MED = np.empty((N, F))
    labels = np.empty(N, dtype=int)
    for i, c in enumerate(concepts):
        LO[i] = c["lo"]; HI[i] = c["hi"]; MED[i] = c["med"]; labels[i] = c["label"]
    return LO, HI, MED, labels


# ------------------------------------------------------------------ scoring

def score_batch(Xq, LO, HI, MED, labels, mask=None, return_detail=False):
    """Score a batch of quantized observations against all concepts.

    Args:
        Xq:     (B, F) quantized observations
        LO/HI/MED: (N, F) concept boxes and prototypes
        labels: (N,) concept labels
        mask:   (N, F) of {0,1}, or None for all-ones (dense / shipped behavior)
        return_detail: also return per-sample counts, distances, margins

    Returns:
        pred (B,)  — predicted labels
        [detail dict] if return_detail
    """
    Xq = np.asarray(Xq, dtype=np.float64)
    B = Xq.shape[0]
    N, F = LO.shape
    # BIG must exceed the largest achievable distance so count strictly dominates.
    # quantized values live in [-7, 8] -> |obs - med| <= 15, summed over <= F dims.
    BIG = 16.0 * F + 1.0

    cnt  = np.empty((B, N), dtype=np.float64)
    dist = np.empty((B, N), dtype=np.float64)
    for c in range(N):                              # stream: no (B, N, F) tensor
        inr = (Xq >= LO[c]) & (Xq <= HI[c])         # (B, F) bool
        w = inr * mask[c] if mask is not None else inr.astype(np.float64)
        cnt[:, c]  = w.sum(1)
        dist[:, c] = (np.abs(Xq - MED[c]) * w).sum(1)

    key = cnt * BIG - dist                           # lexicographic (count, -dist)
    idx = key.argmax(1)                              # argmax -> lowest index on ties
    pred = labels[idx]
    if not return_detail:
        return pred

    rows = np.arange(B)
    key2 = key.copy()
    key2[rows, idx] = -np.inf
    idx2 = key2.argmax(1)
    detail = {
        "count": cnt,
        "dist": dist,
        "pred_idx": idx,
        "count_margin": cnt[rows, idx] - cnt[rows, idx2],  # top1 - top2 count gap
        "active_per_concept": (mask.sum(1) if mask is not None
                               else np.full(N, F, dtype=float)),
    }
    return pred, detail


# ----------------------------------------------- deepest-satisfied-key rule

def score_batch_deepest(Xq, LO, HI, MED, labels, mask, return_detail=False):
    """Bundle-match with significant-digits resolution.

    Each concept is a committed set of constraints (its mask). A concept *fires*
    when every committed constraint is satisfied. Among firing concepts the most
    *resolved* one wins — the one with the most committed-and-satisfied
    distinctions (depth). If nothing fires cleanly, fall back to the concept
    closest to firing (most committed constraints satisfied). Ties -> nearest
    prototype, then lowest index. This is "report to the finest grain the
    evidence supports," not "tally what lit up."
    """
    Xq = np.asarray(Xq, dtype=np.float64)
    B = Xq.shape[0]
    N, F = LO.shape
    if mask is None:
        mask = np.ones((N, F))
    depth = mask.sum(1)                              # committed digits per concept
    W1 = 16.0 * F + 1.0                              # > max distance
    W2 = (F + 1.0) * W1                              # firing dominates non-firing

    fires = np.empty((B, N)); satisf = np.empty((B, N)); dist = np.empty((B, N))
    for c in range(N):
        inr = (Xq >= LO[c]) & (Xq <= HI[c])         # (B, F)
        comm = mask[c].astype(bool)
        m = comm.sum()
        s = inr[:, comm].sum(1) if m > 0 else np.zeros(B)
        satisf[:, c] = s
        fires[:, c] = (s == m) if m > 0 else 1.0    # empty set fires vacuously, depth 0
        w = inr * mask[c]
        dist[:, c] = (np.abs(Xq - MED[c]) * w).sum(1)

    fire_b = fires.astype(bool)
    resolved = np.where(fire_b, depth[None, :], satisf)   # depth if fired, else partial
    key = fire_b * W2 + resolved * W1 - dist
    idx = key.argmax(1)
    pred = labels[idx]
    if not return_detail:
        return pred
    return pred, {"fired": fire_b, "depth": depth, "resolved": resolved,
                  "pred_idx": idx, "any_fired": fire_b.any(1)}


# --------------------------------------------- average-difference rule

def score_batch_avgdiff(Xq, LO, HI, MED, labels, mask, return_detail=False):
    """Arity-normalized matcher: average difference per committed digit.

    For each concept, the difference on a committed axis is how far the value
    lies OUTSIDE the accepted range (0 if inside). Averaging over the committed
    set (not summing) makes keys of different length comparable — a 3-digit id
    and an 18-digit id are ranked on per-digit fit, not total. Smallest average
    difference wins; among equally-good fits (e.g. several keys fully contain the
    point, avg 0) the most resolved one wins (significant digits); final ties go
    to nearest prototype. Graceful where strict AND is brittle: one digit barely
    out only nudges the average instead of vetoing the whole id.
    """
    Xq = np.asarray(Xq, dtype=np.float64)
    B = Xq.shape[0]
    N, F = LO.shape
    if mask is None:
        mask = np.ones((N, F))
    depth = mask.sum(1)
    BIGA = 1e9        # avg difference is primary
    BIGB = 1e3        # then depth (specificity)

    avgdiff = np.empty((B, N)); avgmed = np.empty((B, N))
    for c in range(N):
        comm = mask[c].astype(bool)
        m = max(int(comm.sum()), 1)
        gap = np.maximum.reduce([LO[c] - Xq, Xq - HI[c], np.zeros_like(Xq)])  # 0 if in range
        avgdiff[:, c] = gap[:, comm].sum(1) / m
        avgmed[:, c] = (np.abs(Xq - MED[c])[:, comm]).sum(1) / m

    key = -avgdiff * BIGA + depth[None, :] * BIGB - avgmed
    idx = key.argmax(1)
    pred = labels[idx]
    if not return_detail:
        return pred
    rows = np.arange(B)
    return pred, {"avgdiff": avgdiff, "pred_idx": idx,
                  "fully_contained": (avgdiff[rows, idx] == 0)}


# ----------------------------------------------- quantizers

def quantize_for_range(clf, X_raw):
    """Quantized observations for a fitted RangeClassifier."""
    Xq, _, _ = quantize(np.asarray(X_raw, dtype=float), clf.qlo, clf.qhi)
    return Xq


def quantize_for_crystal(crystal, model, X_raw):
    """Quantized hidden representation for a fitted CrystalClassifier."""
    h = crystal.extract_fn(model, np.asarray(X_raw, dtype=float)) - crystal.dc
    Xq, _, _ = quantize(h, crystal.qlo, crystal.qhi)
    return Xq


# ----------------------------------------------------------------- wrapper

class FastScorer:
    """Thin wrapper holding a classifier's concepts as tensors + a mask.

    >>> fs = FastScorer.from_crystal(crystal)          # all-ones mask
    >>> pred = fs.predict_q(quantize_for_crystal(crystal, mlp, X_test))
    >>> fs.set_mask(my_mask)                            # test a selection rule
    >>> pred2 = fs.predict_q(...)
    """

    def __init__(self, concepts, mask=None):
        self.LO, self.HI, self.MED, self.labels = concepts_to_tensors(concepts)
        self.N, self.F = self.LO.shape
        self.mask = mask

    @classmethod
    def from_range(cls, clf):
        return cls(clf.concepts)

    @classmethod
    def from_crystal(cls, crystal):
        return cls(crystal.concepts)

    def set_mask(self, mask):
        if mask is not None and mask.shape != (self.N, self.F):
            raise ValueError(f"mask must be {(self.N, self.F)}, got {mask.shape}")
        self.mask = mask
        return self

    def predict_q(self, Xq, return_detail=False):
        return score_batch(Xq, self.LO, self.HI, self.MED, self.labels,
                           self.mask, return_detail)

    def predict_q_deepest(self, Xq, return_detail=False):
        return score_batch_deepest(Xq, self.LO, self.HI, self.MED, self.labels,
                                   self.mask, return_detail)

    def predict_q_avgdiff(self, Xq, return_detail=False):
        return score_batch_avgdiff(Xq, self.LO, self.HI, self.MED, self.labels,
                                   self.mask, return_detail)

    def mean_active_dims(self):
        return float(self.F if self.mask is None else self.mask.sum(1).mean())


# ----------------------------------------------- example selection policies
# These are ILLUSTRATIVE mask builders to exercise the engine. The actual
# "what makes an axis useful / when to stop" rule is still an open design
# choice — drop a different builder in here to test it.

def all_ones_mask(LO, HI, MED, labels):
    """Baseline: every concept uses every axis -> reproduces the dense scorer."""
    return np.ones_like(LO)


def greedy_separation_mask(LO, HI, MED, labels, min_keep=1):
    """Greedy, context-relative, minimal-ish axis selection.

    For each concept, add the fewest axes whose box excludes other-label
    prototypes, until every other-label concept is separated on at least one
    kept axis. An axis 'separates' concept j from i when j's prototype falls
    outside i's box on that axis. This embodies "add useful axes until the
    confusion is refined" — but it is one policy among many, not settled.
    """
    N, F = LO.shape
    mask = np.zeros((N, F))
    for i in range(N):
        others = [j for j in range(N) if labels[j] != labels[i]]
        # sep[j] : bool (F,) — axes on which j's prototype is outside i's box
        sep = {j: (MED[j] < LO[i]) | (MED[j] > HI[i]) for j in others}
        remaining = set(others)
        while remaining:
            best_d, best_gain = -1, 0
            for d in range(F):
                if mask[i, d]:
                    continue
                gain = sum(1 for j in remaining if sep[j][d])
                if gain > best_gain:
                    best_gain, best_d = gain, d
            if best_d < 0:           # nothing left can separate the remainder
                break
            mask[i, best_d] = 1.0
            remaining = {j for j in remaining if not sep[j][best_d]}
        if mask[i].sum() < min_keep:  # degenerate: keep the tightest axes
            for d in np.argsort(HI[i] - LO[i])[:min_keep]:
                mask[i, d] = 1.0
    return mask
