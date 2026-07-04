"""
DIGITS AS POINT SETS — does spatial representation unlock the registration
benchmark WITHOUT registering?

The registration road (registration_perception_16.py): factor pose out by
canonicalization, then classify. 23.7% raw -> 84.4% registered.

The spatial road tried here: don't factor pose out — represent the digit by
RELATIONS that never had pose in them. Each glyph's ink pixels become a
point set; the descriptor is its pairwise-distance spectrum (histogram of
distances normalized by the glyph's own scale) + ink-mass profile by radius.
Translation invariance: free (distances). Scale invariance: free
(normalization). Same protocol as the registration test: 16x16 canvas,
random position + size 8-12, novel bigger 13-15, novel tiny 6-7.

Honest expectations stated up front: the spectrum is a LOSSY shape summary
(it also confers rotation invariance nobody asked for — a 6 and a 9 share a
spectrum), so this measures how far pure relational representation gets on
this benchmark, not a claim it must win.
"""
import sys
import numpy as np

import os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from registration_perception import resample
from registration_perception_16 import random_canvas, CANVAS
from sklearn.datasets import load_digits          # data loading only

rng = np.random.default_rng(3)
N_BINS = 14


def ink_points(flat, side=CANVAS, thresh=0.25, max_pts=48):
    img = flat.reshape(side, side)
    m = img.max()
    if m <= 0:
        return np.zeros((0, 2)), np.zeros(0)
    ys, xs = np.nonzero(img > thresh * m)
    w = img[ys, xs]
    if len(ys) > max_pts:
        keep = np.argsort(-w)[:max_pts]
        ys, xs, w = ys[keep], xs[keep], w[keep]
    return np.column_stack([ys, xs]).astype(float), w / w.sum()


def descriptor(flat, side=CANVAS):
    """Pose-free by construction: ink-weighted pairwise-distance spectrum
    (normalized by the glyph's own 90th-pct distance) + radial mass profile
    around the ink centroid (also self-normalized)."""
    P, w = ink_points(flat, side)
    if len(P) < 3:
        return np.zeros(N_BINS + 6)
    D = np.sqrt(((P[:, None, :] - P[None, :, :]) ** 2).sum(-1))
    ww = np.outer(w, w)
    iu = np.triu_indices(len(P), 1)
    d, dw = D[iu], ww[iu]
    scale = np.quantile(d, 0.9) + 1e-9
    hist, _ = np.histogram(d / scale, bins=N_BINS, range=(0, 1.4),
                           weights=dw)
    hist = hist / (hist.sum() + 1e-12)
    ctr = (P * w[:, None]).sum(0)
    r = np.sqrt(((P - ctr) ** 2).sum(1))
    rhist, _ = np.histogram(r / (np.quantile(r, 0.9) + 1e-9), bins=6,
                            range=(0, 1.4), weights=w)
    rhist = rhist / (rhist.sum() + 1e-12)
    return np.concatenate([hist, rhist])


def classify(train_desc, ytr, test_desc, k=5):
    out = np.empty(len(test_desc), int)
    for i, q in enumerate(test_desc):
        d = np.abs(train_desc - q).sum(1)
        nn = np.argpartition(d, k)[:k]
        out[i] = np.bincount(ytr[nn]).argmax()
    return out


def main():
    d = load_digits()
    X, y = d.data.astype(float), d.target
    idx = rng.permutation(len(y)); kk = int(0.7 * len(y))
    tr, te = idx[:kk], idx[kk:]

    Ctr = random_canvas(X[tr], (8, 12))
    Cte = random_canvas(X[te], (8, 12))
    Cte_big = random_canvas(X[te], (13, 15))
    Cte_tiny = random_canvas(X[te], (6, 7))

    Dtr = np.array([descriptor(v) for v in Ctr])
    print("spectra computed for train; classifying (k=5, L1)...\n")
    print(f"{'variant':26s} {'spectrum':>9s}   (raw doors / registered, from"
          f" registration_perception_16)")
    print("-" * 78)
    refs = {"random pos + size 8-12": (23.7, 84.4),
            "novel bigger 13-15": (26.5, 85.4),
            "novel tiny 6-7": (13.7, 58.3)}
    obs = {}
    for name, V in [("random pos + size 8-12", Cte),
                    ("novel bigger 13-15", Cte_big),
                    ("novel tiny 6-7", Cte_tiny)]:
        Dte = np.array([descriptor(v) for v in V])
        acc = (classify(Dtr, y[tr], Dte) == y[te]).mean()
        obs[name] = acc
        r, g = refs[name]
        print(f"{name:26s} {acc*100:8.1f}%   ({r}% / {g}%)")

    print("\nHONEST READING: the spectrum needs NO registration step — pose")
    print("never entered the representation. Where it lands relative to the")
    print("registration road is the measurement; the confusion structure")
    print("(6 vs 9 share a spectrum) is the known lossy-ness, by design.")


if __name__ == "__main__":
    main()
