"""
TRANSLATION — brick #2.  Where is the object, and how big?

Goal: Isaac reports an object's CENTER and SIZE from raw pixels, and we ask
whether that survives TRANSLATION (the same object at positions never seen).

Rule 1 line held carefully:
  - Correct center/size labels are computed ONLY to teach (curriculum =
    "questions with correct answers"). A teacher is allowed to know the answer.
  - At QUERY time, nothing is computed. We pass the raw grid + a question cue
    ('ask_center' / 'ask_size') and read what ISAAC returns. The localization
    is his, not ours. No scan loop, no centroid(), no bounding_box().

Train positions and test positions are DISJOINT (split by (r+c) parity), so
every test grid is a translation Isaac has never seen.
"""

import numpy as np
from isaac import Isaac

GRID = 9
SIZES = (3, 5)  # square blocks; size is a real, non-trivial readout


def make_grid(size, r, c):
    """A size x size block of 1s with top-left at (r, c). Raw pixels."""
    g = np.zeros((GRID, GRID), dtype=int)
    g[r:r + size, c:c + size] = 1
    return g


def center_of(size, r, c):
    return (r + size // 2, c + size // 2)


def positions(size):
    """All valid top-left positions for a size x size block."""
    return [(r, c) for r in range(GRID - size + 1)
            for c in range(GRID - size + 1)]


def flat(grid):
    return [str(int(v)) for v in grid.flatten()]


def show(grid):
    return "\n".join("    " + "".join("#" if v else "." for v in row)
                     for row in grid)


def teach(isaac, grid, cr, cc, size):
    isaac.observe(flat(grid) + ["ask_center", f"ctr_{cr}_{cc}"])
    isaac.observe(flat(grid) + ["ask_size", f"sz_{size}"])


def ask_center(isaac, grid):
    ans, conf = isaac.lookup(flat(grid) + ["ask_center"])
    if isinstance(ans, str) and ans.startswith("ctr_"):
        try:
            _, r, c = ans.split("_")
            return (int(r), int(c)), conf
        except ValueError:
            pass
    return None, conf


def ask_size(isaac, grid):
    ans, conf = isaac.lookup(flat(grid) + ["ask_size"])
    if isinstance(ans, str) and ans.startswith("sz_"):
        try:
            return int(ans.split("_")[1]), conf
        except ValueError:
            pass
    return None, conf


def main():
    isaac = Isaac()

    # Build train/test split: train where (r+c) even, test where odd.
    train, test = [], []
    for size in SIZES:
        for (r, c) in positions(size):
            (train if (r + c) % 2 == 0 else test).append((size, r, c))

    # show a couple examples of what Isaac is shown
    print("=" * 60)
    print("  EXAMPLES OF WHAT ISAAC IS SHOWN (raw pixels)")
    print("=" * 60)
    for size, r, c in (train[0], test[0]):
        cr, cc = center_of(size, r, c)
        print(f"\n  size {size} block, top-left ({r},{c}), "
              f"true center ({cr},{cc}):")
        print(show(make_grid(size, r, c)))

    # teach (curriculum: correct labels allowed)
    for size, r, c in train:
        cr, cc = center_of(size, r, c)
        teach(isaac, make_grid(size, r, c), cr, cc, size)
    isaac.consolidate()

    def score(dataset):
        ctr_exact = ctr_near = sz_exact = n = 0
        for size, r, c in dataset:
            g = make_grid(size, r, c)
            cr, cc = center_of(size, r, c)
            pc, _ = ask_center(isaac, g)
            ps, _ = ask_size(isaac, g)
            n += 1
            if pc == (cr, cc):
                ctr_exact += 1
            if pc is not None and abs(pc[0]-cr) + abs(pc[1]-cc) <= 1:
                ctr_near += 1
            if ps == size:
                sz_exact += 1
        return ctr_exact/n, ctr_near/n, sz_exact/n, n

    tr = score(train)
    te = score(test)

    print("\n" + "=" * 60)
    print("  RESULTS")
    print("=" * 60)
    print(f"  train positions: {tr[3]}   test positions (novel): {te[3]}")
    print(f"\n  {'':16}{'center exact':>14}{'center<=1':>12}{'size exact':>12}")
    print(f"  {'TRAIN (seen)':16}{tr[0]:>13.0%}{tr[1]:>12.0%}{tr[2]:>12.0%}")
    print(f"  {'TEST (novel)':16}{te[0]:>13.0%}{te[1]:>12.0%}{te[2]:>12.0%}")
    print("\n" + "=" * 60)
    print("  reading: high TRAIN + low TEST center  => he MEMORIZES where")
    print("  objects were, does not LOCALIZE by translation. That's the gap")
    print("  'differentiation' would need to close.")
    print("=" * 60)


if __name__ == "__main__":
    main()
