"""
GREY EDGES — how many edges are grey?

Shapes drawn as outlines where each edge is independently WHITE or GREY. The
grey is a query, not the answer: he has to find the edges AND read which are
grey. Non-congruent grey edges count separately (each polygon side is its own
edge). Named checks from the steer: triangle w/ 1 grey -> 1; heptagon w/ 3 grey
-> 3.

We feed the raw value field + the answer, attempt/compare/learn, and report what
he does. No forecasting.
"""

import numpy as np
from isaac import Isaac

RNG = np.random.default_rng(0)
SZ = 21
TOK = {0: "_", 1: "W", 2: "g"}   # background, white edge, grey edge


def poly_vertices(n, cx=SZ // 2, cy=SZ // 2, r=8, rot=0.0):
    return [(cx + r * np.cos(rot + 2 * np.pi * k / n),
             cy + r * np.sin(rot + 2 * np.pi * k / n)) for k in range(n)]


def draw_line(grid, p0, p1, val):
    """Rasterize a segment with a color value."""
    x0, y0 = p0; x1, y1 = p1
    steps = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
    for t in np.linspace(0, 1, steps):
        x = int(round(x0 + (x1 - x0) * t)); y = int(round(y0 + (y1 - y0) * t))
        if 0 <= x < SZ and 0 <= y < SZ:
            grid[y, x] = val


def make_shape(n, grey_mask, r=8, rot=0.0):
    """Polygon outline; grey_mask[i]=True colors edge i grey, else white."""
    v = poly_vertices(n, r=r, rot=rot)
    g = np.zeros((SZ, SZ), int)
    for i in range(n):
        val = 2 if grey_mask[i] else 1
        draw_line(g, v[i], v[(i + 1) % n], val)
    return g


def flat(grid):
    return [TOK[int(v)] for v in grid.flatten()]


def render(grid):
    return "\n".join("    " + "".join(TOK[int(v)] for v in row) for row in grid)


def teach(isaac, grid, n_grey):
    isaac.observe(flat(grid) + [f"grey_{n_grey}"])


def ask(isaac, grid):
    ans, conf = isaac.lookup(flat(grid))
    return (ans, conf)


def main():
    isaac = Isaac()

    # ---- training set: varied shapes, sizes, rotations, colorings ----
    n_train = 0
    for _ in range(400):
        n = int(RNG.integers(3, 8))            # triangle..heptagon
        r = int(RNG.integers(6, 9))
        rot = float(RNG.uniform(0, np.pi))
        # random number of grey edges
        n_grey = int(RNG.integers(0, n + 1))
        mask = np.zeros(n, bool)
        mask[RNG.choice(n, n_grey, replace=False)] = True if n_grey else False
        g = make_shape(n, mask, r=r, rot=rot)
        teach(isaac, g, int(mask.sum()))
        n_train += 1
    isaac.consolidate()
    print(f"  trained on {n_train} grey/white-edged shapes")

    # ---- named checks ----
    print("\n" + "=" * 56)
    print("  NAMED CHECKS")
    print("=" * 56)
    tri = make_shape(3, np.array([True, False, False]), r=8, rot=0.3)
    print("\n  triangle, 1 grey edge (true grey=1):")
    print(render(tri))
    print(f"    Isaac said: {ask(isaac, tri)}")

    hep_mask = np.array([True, False, True, False, True, False, False])
    hep = make_shape(7, hep_mask, r=9, rot=0.1)
    print("\n  heptagon, 3 grey edges (true grey=3):")
    print(render(hep))
    print(f"    Isaac said: {ask(isaac, hep)}")

    # ---- held-out test set: novel colorings/shapes ----
    print("\n" + "=" * 56)
    print("  HELD-OUT TEST (novel shapes/colorings)")
    print("=" * 56)
    correct = near = total = 0
    by_true = {}
    for _ in range(120):
        n = int(RNG.integers(3, 8))
        r = int(RNG.integers(6, 9))
        rot = float(RNG.uniform(0, np.pi))
        n_grey = int(RNG.integers(0, n + 1))
        mask = np.zeros(n, bool)
        if n_grey:
            mask[RNG.choice(n, n_grey, replace=False)] = True
        g = make_shape(n, mask, r=r, rot=rot)
        true = int(mask.sum())
        ans, _ = ask(isaac, g)
        got = int(ans.split("_")[1]) if isinstance(ans, str) and ans.startswith("grey_") else -1
        total += 1
        correct += (got == true)
        near += (abs(got - true) <= 1)
        by_true.setdefault(true, [0, 0])
        by_true[true][0] += (got == true); by_true[true][1] += 1

    print(f"  exact: {correct}/{total} = {correct/total:.0%}   "
          f"within 1: {near}/{total} = {near/total:.0%}")
    print("  accuracy by true grey-count:")
    for t in sorted(by_true):
        ok, tot = by_true[t]
        print(f"    {t} grey: {ok}/{tot}")


if __name__ == "__main__":
    main()
