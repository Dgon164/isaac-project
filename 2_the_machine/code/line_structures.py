"""
STRUCTURE ENUMERATION — compose line-scan run-widths into shape types.

The type is the DERIVATIVE of the run-width profile down the shape:
  width constant            -> straight sides -> rectangle (square if W==H, line if thin)
  width changes linearly    -> triangle / wedge
  width changes non-linearly-> curve / round
Position is where the runs start (constant start = aligned edge; moving start =
slant or curve).

Two parts:
  ORACLE (answer key) -- classify from the profile, to show the width-derivative
    IS the structure signature. Classical, never ships as Isaac's output.
  ISAAC -- feed the width-DELTA profile as observations; see if structure-types
    crystallize (constant vs ramp vs curve).
"""

import numpy as np
from isaac import Isaac


def runs_widths(grid):
    """Per-row: the width of the (first) on-run in that row. 0 if empty row.
    Also the run's start column (position)."""
    H, W = grid.shape
    widths, starts = [], []
    for y in range(H):
        on = np.where(grid[y] == 1)[0]
        if len(on) == 0:
            continue
        # width = span of the row's on-pixels (handles single run cleanly)
        widths.append(int(on.max() - on.min() + 1))
        starts.append(int(on.min()))
    return widths, starts


def classify(grid):
    """ORACLE: name the structure from its width profile."""
    w, s = runs_widths(grid)
    if not w:
        return "empty"
    H = len(w)
    Wmax = max(w)
    if H == 1:
        return "line(horizontal)"
    if Wmax == 1:
        return "line(vertical)"
    d1 = np.diff(w)
    # constant width?
    if np.all(d1 == 0):
        aspect = Wmax / H
        if 0.8 <= aspect <= 1.25:
            return "square"
        if aspect > 4 or aspect < 0.25:
            return "line(thick)"
        return "rectangle"
    # linear change? (constant nonzero slope, or symmetric ramp up/down)
    d2 = np.diff(d1)
    if np.all(d2 == 0):
        return "triangle/wedge"
    # symmetric rise-then-fall with changing slope -> curve
    half = len(d1) // 2
    if np.all(d1[:half] >= 0) and np.all(d1half_neg(d1, half)):
        return "curve/round"
    return "irregular"


def d1half_neg(d1, half):
    return d1[-half:] <= 0 if half > 0 else [True]


def width_delta_tokens(grid):
    """ISAAC input: the sign of width-change down the shape.
    constant -> '0' run; triangle -> '+' run; curve -> '+...-' """
    w, _ = runs_widths(grid)
    toks = []
    for a, b in zip(w, w[1:]):
        toks.append("winc" if b > a else ("wdec" if b < a else "wsame"))
    return toks


def shapes():
    S = {}
    g = np.zeros((13, 13), int); g[2:11, 6] = 1; S["vline"] = g
    g = np.zeros((13, 13), int); g[6, 2:11] = 1; S["hline"] = g
    g = np.zeros((13, 13), int); g[3:10, 3:8] = 1; S["rectangle"] = g
    g = np.zeros((13, 13), int); g[3:9, 3:9] = 1; S["square"] = g
    g = np.zeros((13, 13), int)
    for r in range(6):                      # triangle: width grows linearly
        g[3 + r, 6 - r:6 + r + 1] = 1
    S["triangle"] = g
    g = np.zeros((13, 13), int)             # disk: width rises then falls
    cy, cx, rad = 6, 6, 5
    for y in range(13):
        for x in range(13):
            if (y - cy) ** 2 + (x - cx) ** 2 <= rad * rad:
                g[y, x] = 1
    S["disk"] = g
    return S


def main():
    S = shapes()
    print("=" * 60)
    print("  ORACLE — structure from width profile (the answer key)")
    print("=" * 60)
    for name, g in S.items():
        w, s = runs_widths(g)
        print(f"  {name:12} widths={w}")
        print(f"  {'':12} -> {classify(g)}")

    # ---- Isaac: do structure-types crystallize from width-deltas? ----
    isaac = Isaac()
    for name, g in S.items():
        toks = width_delta_tokens(g)
        if len(toks) >= 2:
            isaac.observe(toks)
            isaac.observe(toks)  # show each twice for stable profiles
    isaac.consolidate()
    print("\n" + "=" * 60)
    print(f"  ISAAC — types from width-delta profiles: {len(isaac.types)}")
    print("=" * 60)
    for tname, t in isaac.types.items():
        print(f"    {sorted(str(m) for m in t['members'])}")
    print("\n  per-shape delta profile:")
    for name, g in S.items():
        print(f"    {name:12} {width_delta_tokens(g)}")


if __name__ == "__main__":
    main()
