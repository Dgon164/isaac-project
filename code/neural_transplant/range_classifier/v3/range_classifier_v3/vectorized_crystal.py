"""
Vectorized scoring core for range / crystal concepts, with per-concept dimension masks.
=======================================================================================

Two properties matter here:

1. **Exactness.** With an all-ones mask the predictions are identical, sample for
   sample, to the shipped ``RangeClassifier._classify_one`` decision rule:
       primary  = count of in-range dims        (higher wins)
       tiebreak = sum |x - med| over those dims  (lower wins)
       ties     = earliest concept index wins
   So the dense crystal is recovered exactly; the mask is the only new degree of freedom.

2. **No (B, N, F) blow-up.** Scoring streams over the (few) concepts and vectorizes
   over the batch, so it never materializes a B x N x F tensor. On a GPU the same shape
   fuses compare-and-reduce; the dimension axis collapses into the parallel lanes.

The 0/1 mask selects which dimensions are *allowed to count* for each concept. It is
applied as a multiply inside the reduction, so it costs nothing structurally. The mask
is the pluggable part: any "which axes are useful" rule produces one. Two starter rules
are included (all-ones = dense baseline; discriminative = keep only dims that actually
separate a concept from a rival). The selection *policy* is deliberately left open --
this module is the substrate it plugs into.
"""

import numpy as np

__all__ = [
    "stack_concepts", "score_batch",
    "mask_all_ones", "mask_discriminative",
    "MaskedCrystal",
]


# ------------------------------------------------------------------
# concept arrays
# ------------------------------------------------------------------

def stack_concepts(concepts):
    """Stack a list of concept dicts into dense (N, F) arrays + a label vector.

    Each concept dict has 1-D arrays 'lo', 'hi', 'med' of length F, plus 'label'.
    All concepts in a fitted model are dense over the same F dims, so this is
    rectangular.
    """
    LO  = np.asarray([c["lo"]  for c in concepts], dtype=np.float64)
    HI  = np.asarray([c["hi"]  for c in concepts], dtype=np.float64)
    MED = np.asarray([c["med"] for c in concepts], dtype=np.float64)
    labels = np.asarray([c["label"] for c in concepts])
    return LO, HI, MED, labels


# ------------------------------------------------------------------
# the scorer
# ------------------------------------------------------------------

def score_batch(X, LO, HI, MED, mask=None, return_detail=False):
    """Classify a batch X (B, F) against concepts LO/HI/MED (N, F).

    Streams over the N concepts and vectorizes over the B samples -- no (B, N, F)
    intermediate. Returns concept indices (B,). The caller maps indices to labels.

    With ``return_detail=True`` also returns a dict:
        count    (B, N)  in-range, mask-allowed dim counts
        dist     (B, N)  summed |x - med| over those dims
        by_count (B,)    True where the winner beat the runner-up on count alone
                         (False => the decision fell through to the distance tiebreak)
    """
    X = np.asarray(X, dtype=np.float64)
    B = X.shape[0]
    N, F = LO.shape
    if mask is None:
        mask = np.ones((N, F), dtype=np.float64)

    count = np.empty((B, N), dtype=np.float64)
    dist  = np.empty((B, N), dtype=np.float64)
    for c in range(N):
        inr = (X >= LO[c]) & (X <= HI[c])          # (B, F)
        m   = inr * mask[c]                          # drop non-useful dims (free)
        count[:, c] = m.sum(1)
        dist[:, c]  = (np.abs(X - MED[c]) * m).sum(1)

    # collapse the lexicographic (count desc, dist asc) rule into one scalar.
    # BIG > every observed dist guarantees one extra count outranks any dist gap;
    # argmax keeps the earliest index on exact ties, matching the shipped loop.
    BIG = float(dist.max()) + 1.0 if dist.size else 1.0
    key = count * BIG - dist
    idx = key.argmax(1)

    if not return_detail:
        return idx

    top_count = count[np.arange(B), idx]
    other = count.copy()
    other[np.arange(B), idx] = -np.inf
    runner_up = other.max(1) if N > 1 else np.full(B, -np.inf)
    by_count = top_count > runner_up
    return idx, {"count": count, "dist": dist, "by_count": by_count}


# ------------------------------------------------------------------
# mask rules (the pluggable part)
# ------------------------------------------------------------------

def mask_all_ones(LO, HI, MED, labels):
    """Every dim counts for every concept -> reproduces the dense crystal exactly."""
    return np.ones_like(LO)


def mask_discriminative(LO, HI, MED, labels, min_keep=1):
    """Keep, per concept, only dims where its box is disjoint from at least one
    differently-labeled concept's box.

    A dim that overlaps every rival carries no separating information for that
    concept (the "don't spend an axis everything agrees on" rule) and is dropped.
    Each concept is guaranteed at least ``min_keep`` dims; if box-disjointness
    yields fewer, the largest median-gap dims are added back as a fallback.

    This is one concrete, defensible selection rule -- a starting point for the
    engine, not a claim that it is *the* policy.
    """
    N, F = LO.shape
    mask = np.zeros((N, F), dtype=np.float64)
    for c in range(N):
        rivals = [r for r in range(N) if labels[r] != labels[c]]
        if not rivals:                      # no rival of a different class
            mask[c] = 1.0
            continue
        for d in range(F):
            for r in rivals:
                if HI[c, d] < LO[r, d] or LO[c, d] > HI[r, d]:
                    mask[c, d] = 1.0
                    break
        if mask[c].sum() < min_keep:        # fallback: widest median separation
            gaps = np.array([min(abs(MED[c, d] - MED[r, d]) for r in rivals)
                             for d in range(F)])
            for d in np.argsort(gaps)[::-1][:min_keep]:
                mask[c, d] = 1.0
    return mask


# ------------------------------------------------------------------
# wrapper
# ------------------------------------------------------------------

class MaskedCrystal:
    """Wrap a fitted ``CrystalClassifier`` or ``RangeClassifier`` with vectorized,
    maskable scoring.

    Builds the dense (N, F) concept arrays once, applies ``mask_fn`` to get the
    per-concept usefulness mask, and scores with :func:`score_batch`. With
    ``mask_fn=mask_all_ones`` the output equals the wrapped model's, sample for sample.

    For a crystal, ``predict(model, X)`` runs the same extract -> (DC) -> quantize
    pipeline as the source. For a raw range classifier, call ``predict(None, X)``.
    """

    def __init__(self, fitted, mask_fn=mask_all_ones):
        self.concepts = fitted.concepts
        self.LO, self.HI, self.MED, self.labels = stack_concepts(self.concepts)
        self.mask = mask_fn(self.LO, self.HI, self.MED, self.labels)
        self._extract = getattr(fitted, "extract_fn", None)
        self._dc      = getattr(fitted, "dc", None)
        self.qlo      = fitted.qlo
        self.qhi      = fitted.qhi

    def _to_quantized(self, model, X):
        from range_classifier import quantize
        if self._extract is not None:
            h = self._extract(model, X)
            if self._dc is not None:
                h = h - self._dc
            Xq, _, _ = quantize(h, self.qlo, self.qhi)
        else:
            Xq, _, _ = quantize(X, self.qlo, self.qhi)
        return Xq

    def predict(self, model, X, detail=False):
        Xq = self._to_quantized(model, X)
        out = score_batch(Xq, self.LO, self.HI, self.MED, self.mask, return_detail=detail)
        if detail:
            idx, info = out
            return self.labels[idx], info
        return self.labels[out]

    def active_dims_per_concept(self):
        """Mean number of dims each concept actually uses under the current mask."""
        return float(self.mask.sum(1).mean())
