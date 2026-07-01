"""
HOLON TEST — point the existing Sections (observe / crystallize / route) at a
pixel holon. No new operation, no encoder. Pixels instead of nodes. See what
types emerge.

Two framings:
  A) RAW pixels: each row observed as a sequence of '0'/'1'. (The addendum's
     worry: 0 and 1 have near-identical neighbor profiles -> trivial types.)
  B) LOCAL DIFFERENCE: each on-cell presented by its relational role -- how many
     on-neighbors it has (valence), the free 'local' channel. Cells with the same
     role (edge / corner / interior) should crystallize together if the holon
     claim holds.

We do not pre-judge. We print what types come out.
"""

import numpy as np
from isaac import Isaac


def shapes():
    sq = np.array([
        [1, 1, 1, 1, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 1, 1, 1, 1]])
    line = np.array([
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [1, 1, 1, 1, 1],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0]])
    cross = np.array([
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [1, 1, 1, 1, 1],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0]])
    return {"square": sq, "line": line, "cross": cross}


def valence(grid):
    """Free 'local' channel: each cell's count of on-neighbors (4-connected).
    This is a difference (cell vs neighbors), not a coordinate."""
    H, W = grid.shape
    v = np.zeros_like(grid)
    for y in range(H):
        for x in range(W):
            if grid[y, x] == 0:
                continue
            n = 0
            for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                yy, xx = y + dy, x + dx
                if 0 <= yy < H and 0 <= xx < W and grid[yy, xx] == 1:
                    n += 1
            v[y, x] = n
    return v


def print_types(isaac, label):
    print(f"\n  --- {label}: {len(isaac.types)} types ---")
    for name, t in isaac.types.items():
        members = sorted(str(m) for m in t["members"])
        print(f"    {members}")


def framing_A():
    print("=" * 60)
    print("  A) RAW PIXELS — rows of 0/1 straight into the net")
    print("=" * 60)
    isaac = Isaac()
    for name, g in shapes().items():
        isaac.observe_matrix(g)
    isaac.consolidate()
    print_types(isaac, "raw pixel types")


def framing_B():
    print("\n" + "=" * 60)
    print("  B) LOCAL DIFFERENCE — each on-cell as its valence (role)")
    print("=" * 60)
    isaac = Isaac()
    for name, g in shapes().items():
        v = valence(g)
        # walk rows; present each cell's role token in sequence
        for row in v:
            seq = [f"deg{int(c)}" for c in row if c > 0]
            if len(seq) >= 2:
                isaac.observe(seq)
        # also walk columns so vertical relations are seen
        for col in v.T:
            seq = [f"deg{int(c)}" for c in col if c > 0]
            if len(seq) >= 2:
                isaac.observe(seq)
    isaac.consolidate()
    print_types(isaac, "role types")
    # what roles even exist?
    allv = []
    for g in shapes().values():
        allv += [int(c) for c in valence(g).flatten() if c > 0]
    from collections import Counter
    print(f"\n  valence distribution across shapes: {dict(Counter(allv))}")
    print("  (deg1=endpoint/tip, deg2=edge/line, deg3=T-junction, deg4=cross-center)")


def dir_sig(grid, y, x):
    """Directional neighborhood signature: which of U/D/L/R are on.
    A horizontal-line cell = 'LR', vertical = 'UD', cross-center = 'UDLR',
    a left tip = 'R'. Distinct per role AND orientation -- a richer relation."""
    H, W = grid.shape
    s = ""
    for tag, (dy, dx) in [("U", (-1, 0)), ("D", (1, 0)),
                          ("L", (0, -1)), ("R", (0, 1))]:
        yy, xx = y + dy, x + dx
        if 0 <= yy < H and 0 <= xx < W and grid[yy, xx] == 1:
            s += tag
    return s or "iso"


def framing_C():
    print("\n" + "=" * 60)
    print("  C) DIRECTIONAL — each on-cell as which neighbors are on")
    print("=" * 60)
    isaac = Isaac()
    from collections import Counter
    sigs = Counter()
    for name, g in shapes().items():
        H, W = g.shape
        for row_i in range(H):
            seq = []
            for col_i in range(W):
                if g[row_i, col_i] == 1:
                    sg = dir_sig(g, row_i, col_i)
                    seq.append(sg)
                    sigs[sg] += 1
            if len(seq) >= 2:
                isaac.observe(seq)
        for col_i in range(W):
            seq = []
            for row_i in range(H):
                if g[row_i, col_i] == 1:
                    seq.append(dir_sig(g, row_i, col_i))
            if len(seq) >= 2:
                isaac.observe(seq)
    isaac.consolidate()
    print_types(isaac, "directional types")
    print(f"\n  signature distribution: {dict(sigs)}")
    print("  (LR=horizontal edge, UD=vertical edge, UDLR=cross center, single=tip)")


if __name__ == "__main__":
    framing_A()
    framing_B()
    framing_C()
