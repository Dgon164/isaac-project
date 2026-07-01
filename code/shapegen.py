"""
shapegen — make as many labeled scenes as you want.

The point: we never EXTRACT the answer from pixels (that's the reduction wall).
We GENERATE pixels from the answer. We choose the shape, size and place it, so
center / size / type are known by construction. Unlimited, perfectly labeled.

Cartesian frame: origin BOTTOM-LEFT, x right, y up (a real xy quadrant).
Rendering prints y downward-from-top so the picture matches the coordinates.
"""

import numpy as np
from math import ceil


def _blank(W, H):
    return np.zeros((H, W), dtype=int)  # [row=y][col=x], we map y from bottom


def _set(grid, x, y):
    H = grid.shape[0]
    if 0 <= x < grid.shape[1] and 0 <= y < H:
        grid[H - 1 - y, x] = 1   # bottom-left origin


def draw_square(grid, x0, y0, s):
    for dx in range(s):
        for dy in range(s):
            _set(grid, x0 + dx, y0 + dy)


def draw_rect(grid, x0, y0, w, h):
    for dx in range(w):
        for dy in range(h):
            _set(grid, x0 + dx, y0 + dy)


def draw_circle(grid, cx, cy, r):
    for x in range(cx - r, cx + r + 1):
        for y in range(cy - r, cy + r + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                _set(grid, x, y)


def make_example(rng):
    """One random labeled scene. Returns (grid, label)."""
    W = int(rng.integers(8, 16))
    H = int(rng.integers(8, 16))
    grid = _blank(W, H)
    shape = rng.choice(["square", "rectangle", "circle"])

    if shape == "square":
        s = int(rng.integers(2, max(3, min(W, H) // 2)))
        x0 = int(rng.integers(0, W - s + 1))
        y0 = int(rng.integers(0, H - s + 1))
        draw_square(grid, x0, y0, s)
        cx, cy = x0 + (s - 1) / 2, y0 + (s - 1) / 2
        label = {"shape": "square", "size": s,
                 "anchor": (x0, y0), "center": (cx, cy)}

    elif shape == "rectangle":
        w = int(rng.integers(2, max(3, W // 2)))
        h = int(rng.integers(2, max(3, H // 2)))
        if w == h:
            w += 1
        x0 = int(rng.integers(0, W - w + 1))
        y0 = int(rng.integers(0, H - h + 1))
        draw_rect(grid, x0, y0, w, h)
        cx, cy = x0 + (w - 1) / 2, y0 + (h - 1) / 2
        label = {"shape": "rectangle", "size": (w, h),
                 "anchor": (x0, y0), "center": (cx, cy)}

    else:  # circle
        r = int(rng.integers(1, max(2, min(W, H) // 4)))
        cx = int(rng.integers(r, W - r))
        cy = int(rng.integers(r, H - r))
        draw_circle(grid, cx, cy, r)
        label = {"shape": "circle", "size": 2 * r + 1,
                 "anchor": (cx - r, cy - r), "center": (cx, cy)}

    return grid, label


def render(grid):
    return "\n".join("    " + "".join("#" if v else "." for v in row)
                     for row in grid)


def dataset(n, seed=0):
    rng = np.random.default_rng(seed)
    return [make_example(rng) for _ in range(n)]


if __name__ == "__main__":
    rng = np.random.default_rng(42)
    print("=" * 50)
    print("  SAMPLE SCENES (origin bottom-left)")
    print("=" * 50)
    for _ in range(4):
        g, lab = make_example(rng)
        print(f"\n  {g.shape[1]}x{g.shape[0]} canvas  ->  {lab}")
        print(render(g))

    # prove it's unlimited and balanced
    ds = dataset(3000, seed=1)
    from collections import Counter
    c = Counter(lab["shape"] for _, lab in ds)
    sizes = Counter(g.shape for g, _ in ds)
    print("\n" + "=" * 50)
    print(f"  generated {len(ds)} scenes, shapes: {dict(c)}")
    print(f"  distinct canvas sizes seen: {len(sizes)}")
    print("=" * 50)
