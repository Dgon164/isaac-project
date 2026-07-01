"""
LINE SCAN — pixels as lines, shared run-widths as doors.

Not the directional-signature shortcut. The real thing:
  - scan each ROW into runs, each COLUMN into runs (two cheap parallel sweeps)
  - feed the lines in as OBSERVATIONS
  - a pixel lives in two runs at once (its row-run, its column-run)
  - where two runs CROSS at a shared pixel with the SAME width, that coincidence
    is the door -- the binding topological feature
  - let the crystallizer type over it; shape is what emerges from the agreements

We do not reconstruct the 2D shape. He does, by typing which lines share what.
Expectation (yours): not great, but better than the collapse.
"""

import numpy as np
from collections import Counter
from isaac import Isaac


def runs(line):
    """1-D run detection: list of (start, length) for each on-run."""
    out = []
    i = 0
    n = len(line)
    while i < n:
        if line[i] == 1:
            j = i
            while j < n and line[j] == 1:
                j += 1
            out.append((i, j - i))
            i = j
        else:
            i += 1
    return out


def line_signature(grid):
    """For each on-pixel: (row_run_width, col_run_width). The pair is its role.
    Width is the shared topological feature; the crossing is the bind."""
    H, W = grid.shape
    rw = np.zeros((H, W), dtype=int)
    cw = np.zeros((H, W), dtype=int)
    for y in range(H):
        for (s, L) in runs(grid[y, :]):
            rw[y, s:s + L] = L
    for x in range(W):
        for (s, L) in runs(grid[:, x]):
            cw[s:s + L, x] = L
    return rw, cw


def shapes():
    sq = np.zeros((9, 9), int); sq[2:7, 2:7] = 1                      # filled square
    hl = np.zeros((9, 9), int); hl[4, 1:8] = 1                        # horizontal line
    vl = np.zeros((9, 9), int); vl[1:8, 4] = 1                        # vertical line
    cr = np.zeros((9, 9), int); cr[4, 1:8] = 1; cr[1:8, 4] = 1        # cross
    di = np.zeros((9, 9), int)
    for i in range(7):
        di[1 + i, 1 + i] = 1                                          # diagonal
    el = np.zeros((9, 9), int); el[1:8, 2] = 1; el[7, 2:7] = 1        # L
    return {"square": sq, "hline": hl, "vline": vl,
            "cross": cr, "diag": di, "L": el}


def role_token(r, c):
    """Pixel role from its two run-widths. Long/short per axis -> the vector."""
    def band(w):
        return "0" if w == 0 else ("1" if w == 1 else ("s" if w <= 2 else "L"))
    return f"r{band(r)}_c{band(c)}"


def observe_as_lines(isaac, grid):
    """Feed row-lines and column-lines as observations of role tokens.
    Each line is a sequence; the crystallizer sees how roles follow each other
    along rows and down columns."""
    rw, cw = line_signature(grid)
    H, W = grid.shape
    for y in range(H):
        seq = [role_token(rw[y, x], cw[y, x]) for x in range(W) if grid[y, x]]
        if len(seq) >= 2:
            isaac.observe(seq)
    for x in range(W):
        seq = [role_token(rw[y, x], cw[y, x]) for y in range(H) if grid[y, x]]
        if len(seq) >= 2:
            isaac.observe(seq)


def main():
    isaac = Isaac()
    sh = shapes()

    # what roles even exist, and which shapes carry them?
    role_by_shape = {}
    allroles = Counter()
    for name, g in sh.items():
        rw, cw = line_signature(g)
        H, W = g.shape
        rs = Counter(role_token(rw[y, x], cw[y, x])
                     for y in range(H) for x in range(W) if g[y, x])
        role_by_shape[name] = rs
        allroles.update(rs)

    print("=" * 60)
    print("  LINE-SCAN ROLES per shape  (rL_cL = long both = interior)")
    print("=" * 60)
    for name, rs in role_by_shape.items():
        print(f"  {name:7}: {dict(rs)}")
    print(f"\n  all roles seen: {dict(allroles)}")

    for name, g in sh.items():
        observe_as_lines(isaac, g)
    isaac.consolidate()

    print("\n" + "=" * 60)
    print(f"  CRYSTALLIZED TYPES: {len(isaac.types)}")
    print("=" * 60)
    for tname, t in isaac.types.items():
        print(f"    {sorted(str(m) for m in t['members'])}")

    # the binding test: do two crossing runs of equal width co-occur as a role?
    print("\n" + "=" * 60)
    print("  CROSSING / WIDTH-AGREEMENT CHECK")
    print("=" * 60)
    cross_rw, cross_cw = line_signature(sh["cross"])
    cy, cx = 4, 4  # the crossing center of the cross
    print(f"  cross center ({cy},{cx}): row-run width={cross_rw[cy,cx]}, "
          f"col-run width={cross_cw[cy,cx]} -> role {role_token(cross_rw[cy,cx], cross_cw[cy,cx])}")
    sq_rw, sq_cw = line_signature(sh["square"])
    print(f"  square interior (4,4): row-run width={sq_rw[4,4]}, "
          f"col-run width={sq_cw[4,4]} -> role {role_token(sq_rw[4,4], sq_cw[4,4])}")
    print("  (interior of a filled square = long both axes; a line = long one axis)")


if __name__ == "__main__":
    main()
