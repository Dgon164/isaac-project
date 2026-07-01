"""
EXTRACT — pull the object out of the scene into a clean, normalized frame.

Detection is a bit flip: a pixel ON where background is expected OFF is the
surprise. The set of flips is the object. Extraction = keep the flips, crop to
their bounding box, re-render in a fresh frame with background marked distinctly.

Why it matters: extraction NORMALIZES. The same object, wherever it sat on
whatever canvas, extracts to the SAME crop. That is translation invariance --
the thing that made recognition collapse to 0% when objects moved. Extract
first, recognize second, and position stops mattering.

Scope:
  - single object on blank background -> works (residual + crop, both already ours)
  - one object out of MANY -> needs flood fill (connectivity), not yet built
  - scale-invariant TYPE recognition -> needs a size-normalize on top (later)
"""

import numpy as np
from shapegen import make_example, render


def extract(grid, bg_token="."):
    """Pull the on-region into a tight, normalized frame.
    Returns a 2D array of chars: '#' for object, bg_token for background.
    The crop is at the object's own origin -- position on the source canvas
    is gone."""
    ys, xs = np.nonzero(grid)
    if len(xs) == 0:
        return None
    y0, y1 = ys.min(), ys.max()
    x0, x1 = xs.min(), xs.max()
    crop = grid[y0:y1 + 1, x0:x1 + 1]
    out = np.where(crop == 1, "#", bg_token)
    return out


def show_chars(arr):
    return "\n".join("    " + "".join(row) for row in arr)


def demo():
    rng = np.random.default_rng(7)
    print("=" * 60)
    print("  EXTRACTION — scene in, clean object out")
    print("=" * 60)
    for _ in range(3):
        g, lab = make_example(rng)
        ex = extract(g)
        print(f"\n  source {g.shape[1]}x{g.shape[0]}, {lab['shape']} "
              f"at center {lab['center']}:")
        print(render(g))
        print(f"  --> extracted {ex.shape[1]}x{ex.shape[0]} (position gone):")
        print(show_chars(ex))


def prove_translation_invariance():
    """Place ONE fixed object at many positions on many canvases. If every
    extraction yields the SAME crop, position has been normalized away."""
    print("\n" + "=" * 60)
    print("  PAYOFF — same object, 50 random placements/canvases")
    print("=" * 60)
    rng = np.random.default_rng(3)
    size = 4
    crops = set()
    for _ in range(50):
        W = int(rng.integers(8, 600))
        H = int(rng.integers(8, 600))
        x0 = int(rng.integers(0, W - size))
        y0 = int(rng.integers(0, H - size))
        g = np.zeros((H, W), dtype=int)
        for dx in range(size):
            for dy in range(size):
                g[H - 1 - (y0 + dy), x0 + dx] = 1
        ex = extract(g)
        crops.add(ex.tobytes())
    print(f"  placed a {size}x{size} square at 50 different spots,")
    print(f"  on canvases from 8x8 up to ~600x600.")
    print(f"  distinct extracted crops: {len(crops)}")
    if len(crops) == 1:
        print("  => ALL 50 extractions are byte-identical.")
        print("     Position and canvas size are gone. Translation = solved")
        print("     by extraction. Recognition on the crop now generalizes.")
    else:
        print("  => extractions differ -- normalization is not clean.")


if __name__ == "__main__":
    demo()
    prove_translation_invariance()
