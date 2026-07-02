"""
REGISTRATION PERCEPTION — pose/identity factoring, phase 1: canonicalization.

What the eye sees = pose ∘ identity. Comparison-as-registration says: solve
the pose, compare the identity, keep BOTH (the pose is information). Phase 1
computes the canonical frame from the thing itself:
  translation -> gone via the support's bounding box
  scale       -> gone via resampling the box to a fixed grid
  brightness  -> gone via the doors' quantile coding (already in the engine)
No learning, no nets. Deterministic, explainable, reversible (pose returned).

Test: the exact probes the raw engine just failed (shift -> 22%/11%,
scale -> 12%), rebuilt FAIRLY (no wraparound, no information destroyed),
raw vs canonicalized, same classifier, same settings.
"""
import sys
import numpy as np

sys.path.insert(0, r"C:\Users\jtwee\Documents\isaac_project\code")
from isaac import Isaac
from sklearn.datasets import load_digits          # data loading only

rng = np.random.default_rng(3)


def resample(crop, out=8):
    H, W = crop.shape
    yy = np.linspace(0, H - 1, out)
    xx = np.linspace(0, W - 1, out)
    Y, X = np.meshgrid(yy, xx, indexing="ij")
    y0 = np.floor(Y).astype(int); x0 = np.floor(X).astype(int)
    y1 = np.minimum(y0 + 1, H - 1); x1 = np.minimum(x0 + 1, W - 1)
    wy, wx = Y - y0, X - x0
    return (crop[y0, x0] * (1 - wy) * (1 - wx) + crop[y1, x0] * wy * (1 - wx)
            + crop[y0, x1] * (1 - wy) * wx + crop[y1, x1] * wy * wx)


def canonical(img, thresh=0.15):
    """Factor pose out; return (identity in canonical frame, pose)."""
    m = img.max()
    if m <= 0:
        return img, None
    ys, xs = np.nonzero(img > thresh * m)
    if len(ys) == 0:
        return img, None
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    pose = dict(cy=(y0 + y1) / 2, cx=(x0 + x1) / 2,
                h=int(y1 - y0), w=int(x1 - x0))
    return resample(img[y0:y1, x0:x1]), pose


def canon_all(flat):
    out = np.empty_like(flat)
    for i, row in enumerate(flat):
        c, _ = canonical(row.reshape(8, 8))
        out[i] = c.ravel()
    return out


# ---- fair transformed variants (no information destroyed, no wraparound)
def shift_pad(img, dy, dx):
    c = np.zeros_like(img)
    ys, xs = slice(max(0, dy), 8 + min(0, dy)), slice(max(0, dx), 8 + min(0, dx))
    yo, xo = slice(max(0, -dy), 8 + min(0, -dy)), slice(max(0, -dx), 8 + min(0, -dx))
    c[ys, xs] = img[yo, xo]
    return c


def shrink_place(img, size, oy, ox):
    small = resample(img, size)
    c = np.zeros((8, 8))
    c[oy:oy + size, ox:ox + size] = small
    return c


def main():
    d = load_digits()
    X, y = d.data.astype(float), d.target
    idx = rng.permutation(len(y)); k = int(0.7 * len(y))
    tr, te = idx[:k], idx[k:]
    img_te = X[te].reshape(-1, 8, 8)

    variants = {
        "clean": X[te],
        "shift 1px": np.array([shift_pad(im, 1, 1).ravel() for im in img_te]),
        "shift 2px": np.array([shift_pad(im, 2, 2).ravel() for im in img_te]),
        "shrink 6x6 + move": np.array(
            [shrink_place(im, 6, rng.integers(0, 3), rng.integers(0, 3)).ravel()
             for im in img_te]),
        "shrink 5x5 + move": np.array(
            [shrink_place(im, 5, rng.integers(0, 4), rng.integers(0, 4)).ravel()
             for im in img_te]),
    }

    print(f"{'variant':22s} {'raw doors':>10s} {'registered':>11s}")
    print("-" * 46)
    # raw pipeline
    raw = Isaac(); raw.fit_lens("eyes", X[tr])
    raw.crystallize_features(X[tr], y[tr], lens="eyes")
    # registered pipeline: canonicalize BOTH training and test
    Xc = canon_all(X)
    reg = Isaac(); reg.fit_lens("eyes", Xc[tr])
    reg.crystallize_features(Xc[tr], y[tr], lens="eyes")
    for name, V in variants.items():
        a_raw = (raw.classify_features(V) == y[te]).mean()
        a_reg = (reg.classify_features(canon_all(V)) == y[te]).mean()
        print(f"{name:22s} {a_raw*100:9.1f}% {a_reg*100:10.1f}%")

    # the pose is INFORMATION: recover the planted displacement
    im = img_te[0]
    _, p0 = canonical(im)
    _, p1 = canonical(shift_pad(im, 2, 1))
    print(f"\npose readout: displacement seen = "
          f"dy {p1['cy']-p0['cy']:+.1f}, dx {p1['cx']-p0['cx']:+.1f} "
          f"(planted +2, +1)")
    _, p2 = canonical(shrink_place(im, 5, 1, 2))
    print(f"pose readout: size seen = {p2['h']}x{p2['w']} vs {p0['h']}x{p0['w']}"
          f" (planted ~5/8 shrink)")


if __name__ == "__main__":
    main()
