"""
LOCATE by difference — the swing.

Predictive coding, simplest rung: Isaac's expectation of empty space is BLANK.
The actual scene has a shape. The RESIDUAL (actual minus prediction) is the
shape. That's the comparison doing the localizing — the object is now a sparse
set of surprising pixels instead of a dense field.

What is Isaac's here, and what is the seam:
  - COMPARISON (predicted blank vs actual): Isaac's. Yields the residual.
  - CENTER = anchor + half-span: ISAAC'S ARITHMETIC. The anchor (big absolute
    coord) is only ever ADDED to; the half-span is a small number halved by a
    taught table. Both are his, and addition was proven to scale to 1000s.
  - THE SEAM (flagged): reading the two corner pixels out of the residual is a
    scan I do in numpy. It's the last reduction we have not made Isaac-native.
    Everything downstream of it is his.

Test: a shape on a 10x10, then the SAME kind of shape on a 500x500. Does the
center come out right at both? If yes, the arithmetic half is scale-free and
only the corner-read remains.
"""

import numpy as np
from isaac import Isaac
from shapegen import draw_square


def make_halver(upto=40):
    """A net that ONLY knows halving. Isolation prevents cross-talk."""
    h = Isaac()
    for x in range(0, upto + 1):
        h.observe(["half", str(x), str(x // 2)])
    h.consolidate()
    return h


def half(halver, n):
    res = halver.predict_next(["half", str(n)])
    if not res:
        return None
    p = res["prediction"]
    return int(p) if str(p).lstrip("-").isdigit() else None


def scene(W, H, size, x0, y0):
    """Raw grid (bottom-left origin) with one square. We KNOW the truth."""
    g = np.zeros((H, W), dtype=int)
    for dx in range(size):
        for dy in range(size):
            xx, yy = x0 + dx, y0 + dy
            if 0 <= xx < W and 0 <= yy < H:
                g[H - 1 - yy, xx] = 1
    true_center = (x0 + (size - 1) / 2, y0 + (size - 1) / 2)
    return g, true_center


def residual_corners(grid):
    """THE SEAM. predicted=blank, so residual = the on-pixels. Read the two
    bounding corners. This scan is the part not yet Isaac-native."""
    H = grid.shape[0]
    ys, xs = np.nonzero(grid)
    if len(xs) == 0:
        return None
    ys_cart = (H - 1) - ys                      # back to bottom-left origin
    return (int(xs.min()), int(ys_cart.min())), (int(xs.max()), int(ys_cart.max()))


def locate(arith, halver, grid):
    """Center from the residual corners using ISOLATED arithmetic nets."""
    corners = residual_corners(grid)
    if corners is None:
        return None
    (ax, ay), (fx, fy) = corners
    spanx, spany = fx - ax, fy - ay
    hx, hy = half(halver, spanx), half(halver, spany)
    if hx is None or hy is None:
        return None
    cx, _ = arith.compute(ax, "+", hx, verbose=False, memorize=False)
    cy, _ = arith.compute(ay, "+", hy, verbose=False, memorize=False)
    if cx is None or cy is None:
        return None
    try:
        return (int(cx), int(cy))
    except (TypeError, ValueError):
        return None


def run_scale(arith, halver, W, H, n, rng):
    ok = near = 0
    for _ in range(n):
        size = int(rng.integers(2, 7))
        x0 = int(rng.integers(0, W - size))
        y0 = int(rng.integers(0, H - size))
        g, true_c = scene(W, H, size, x0, y0)
        pred = locate(arith, halver, g)
        if pred is None:
            continue
        dx = abs(pred[0] - true_c[0])
        dy = abs(pred[1] - true_c[1])
        if dx <= 0.5 and dy <= 0.5:
            ok += 1
        if dx <= 1.5 and dy <= 1.5:
            near += 1
    return ok / n, near / n


def main():
    arith = Isaac()          # ONLY does addition
    halver = make_halver()   # ONLY does halving

    rng = np.random.default_rng(0)
    print("=" * 60)
    print("  LOCATE BY DIFFERENCE — center via isolated arithmetic nets")
    print("=" * 60)
    for (W, H, label) in [(10, 10, "10x10"), (100, 100, "100x100"),
                          (500, 500, "500x500")]:
        exact, near = run_scale(arith, halver, W, H, 60, rng)
        print(f"  {label:>9}:  center exact {exact:>4.0%}   within 1 {near:>4.0%}")
    print("=" * 60)
    print("  exact = computed center matched the true center")
    print("  comparison isolates the object; arithmetic (isolated) sizes it")
    print("=" * 60)


if __name__ == "__main__":
    main()
