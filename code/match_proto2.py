"""
MATCH PROTO step 2: RELATIONAL recognition, scale-invariant, the matrix way.

'frame = a box that ENCOMPASSES a HOLLOW interior' -- a purely RELATIONAL concept,
no fixed template. We find the shape's extent (1st pass: the component), then read
its RELATIONS as scale-free ratios -- border-density vs interior-density -- and
match those against relational concept-signatures (2nd pass: W @ x).

Because the features are ratios (relative, not absolute), recognition is
scale-invariant by construction: a 3x3 frame and a 10x10 frame have the same
relational signature [border~1, interior~0]. Test: FRAME vs FILLED vs CHECKER
across SCALE and NOISE, vs a raw-pixel exact baseline that can't cross scales.

Run:  python match_proto2.py
"""
import numpy as np
from scipy.ndimage import label
rng = np.random.default_rng(0)


def largest_cc(g):
    """1st-pass robustness: isolate the shape, ignore scattered noise specks."""
    lab, n = label(g, structure=np.ones((3, 3)))     # 8-connectivity
    if n == 0:
        return g
    sizes = np.bincount(lab.ravel()); sizes[0] = 0
    return (lab == sizes.argmax()).astype(float)

# relational signatures: [border_density, interior_density] -- scale-free
SIG = {"frame": np.array([1.0, 0.0]),     # border present, interior hollow
       "filled": np.array([1.0, 1.0]),    # border present, interior full
       "checker": np.array([0.5, 0.5])}   # half-on everywhere
names = list(SIG)
W = np.array([SIG[n] for n in names])      # the concept matrix


def make(kind, size, grid=16, noise=0.0):
    g = np.zeros((grid, grid))
    r0 = 0 if grid <= size else int(rng.integers(0, grid - size))
    c0 = 0 if grid <= size else int(rng.integers(0, grid - size))
    sub = np.zeros((size, size))
    if kind == "frame":
        sub[:] = 1; sub[1:-1, 1:-1] = 0
    elif kind == "filled":
        sub[:] = 1
    elif kind == "checker":
        for i in range(size):
            for j in range(size):
                sub[i, j] = (i + j) % 2
    g[r0:r0+size, c0:c0+size] = sub
    if noise:
        flip = rng.random(g.shape) < noise
        g[flip] = 1 - g[flip]
    return g


def relfeat(g):
    """1st pass: extent of the component. 2nd pass: relational ratios (scale-free)."""
    g = largest_cc(g)                          # noise-aware extraction
    ys, xs = np.nonzero(g)
    if len(ys) == 0:
        return None
    crop = g[ys.min():ys.max()+1, xs.min():xs.max()+1]
    h, w = crop.shape
    if h < 3 or w < 3:                         # too small to have an interior
        return np.array([crop.mean(), 0.0])
    ring = np.ones_like(crop); ring[1:-1, 1:-1] = 0
    border_d = crop[ring == 1].mean()
    interior_d = crop[1:-1, 1:-1].mean()
    return np.array([border_d, interior_d])


def recognize(g, mode, templates=None):
    if mode == "exact":                       # raw-pixel exact vs a fixed-size template
        for n, t in templates.items():
            if g.shape == t.shape and np.array_equal(g, t):
                return n
        return None
    x = relfeat(g)
    if x is None: return None
    scores = -np.linalg.norm(W - x[None], axis=1)   # match against the concept matrix
    return names[int(scores.argmax())]


def main():
    # exact baseline gets ONE canonical template per class (size 6, no noise, fixed pos)
    templates = {}
    for n in names:
        t = np.zeros((6, 6))
        sub = make(n, 6, grid=6, noise=0.0)
        templates[n] = sub

    print("relational signatures [border_density, interior_density]:")
    for n in names: print(f"    {n:<8} {SIG[n]}")
    print("=" * 60)
    print(f"  {'noise':>6} | {'exact':>8}{'relational(W@x)':>18}")
    print("  " + "-" * 40)
    for noise in (0.0, 0.05, 0.1, 0.2):
        ae = ar = 0; N = 3000
        for _ in range(N):
            true = names[int(rng.integers(0, len(names)))]
            size = int(rng.integers(3, 11))           # SCALE varies 3..10
            g = make(true, size, noise=noise)
            ae += (recognize(g, "exact", templates) == true)
            ar += (recognize(g, "relational") == true)
        print(f"  {noise:>6.2f} | {ae/N:>8.3f}{ar/N:>18.3f}")
    print("  " + "-" * 40)

    print("\n  scale-invariance check (relational, noise=0.05), accuracy by size:")
    for size in (3, 5, 7, 10):
        ar = 0; N = 1500
        for _ in range(N):
            true = names[int(rng.integers(0, len(names)))]
            g = make(true, size, noise=0.05)
            ar += (recognize(g, "relational") == true)
        print(f"    size {size:>2}x{size:<2}: {ar/N:.3f}")
    print("  READ: exact can't cross scale (one size only); the relational match")
    print("  recognizes 'hollow-encompasses' as a frame at ANY size, because the")
    print("  relation is a ratio. This is the 2nd-order step, done in the matrix.")


if __name__ == "__main__":
    main()
