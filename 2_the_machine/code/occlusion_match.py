"""
PARTIAL MATCH under occlusion — vote, don't require exact.

Each visible stroke-pixel votes for every shape it is consistent with. A pixel
on the main diagonal votes for '\\' AND for 'X' (X contains that diagonal). So
when an X loses a diagonal to occlusion, the surviving pixels still vote for
'\\' fully, and for 'X' only partially -- the two become tied/ambiguous. That
ambiguity is the correct answer: a half-covered X really could be a '\\'.

This uses Isaac's own voting (predict_next), not an exact lookup. The point is
graceful degradation and the discrimination/robustness tradeoff you flagged.
"""

import numpy as np
from isaac import Isaac

N = 5  # 5x5 glyphs


def coords(name):
    bs = [(i, i) for i in range(N)]                 # \  main diagonal
    sl = [(i, N - 1 - i) for i in range(N)]         # /  anti-diagonal
    glyphs = {
        "backslash": set(bs),
        "slash": set(sl),
        "X": set(bs) | set(sl),
        "plus": {(2, y) for y in range(N)} | {(x, 2) for x in range(N)},
    }
    return glyphs[name]


def tok(x, y):
    return f"p{x}_{y}"


def teach(isaac):
    for name in ["backslash", "slash", "X", "plus"]:
        for (x, y) in coords(name):
            # each pixel is a voter for this glyph's label
            isaac.observe([tok(x, y), f"is_{name}"])
    isaac.consolidate()


def vote(isaac, visible):
    """Return ranked (label, votes) from the visible pixels."""
    ctx = [tok(x, y) for (x, y) in visible]
    res = isaac.predict_next(ctx)
    if not res:
        return []
    cands = res["all_candidates"]
    ranked = sorted(((k[len("is_"):], v) for k, v in cands.items()
                     if k.startswith("is_")), key=lambda t: -t[1])
    return ranked


def show(visible):
    grid = [["." for _ in range(N)] for _ in range(N)]
    for (x, y) in visible:
        grid[y][x] = "#"
    return "\n".join("    " + "".join(r) for r in grid)


def main():
    isaac = Isaac()
    teach(isaac)

    full_X = coords("X")
    slash_pixels = coords("slash")

    print("=" * 60)
    print("  OCCLUDING AN X — partial votes, one anti-diagonal pixel at a time")
    print("=" * 60)

    # progressively remove the '/' diagonal from the X
    order = sorted(slash_pixels)  # cover the slash stroke step by step
    visible = set(full_X)
    for step in range(len(order) + 1):
        ranked = vote(isaac, visible)
        top = ranked[:3]
        top_str = "  ".join(f"{n}:{v}" for n, v in top)
        covered = step
        print(f"\n  covered {covered}/{len(order)} of the '/' stroke:")
        print(show(visible))
        print(f"    votes -> {top_str}")
        if step < len(order):
            visible.discard(order[step])

    print("\n" + "=" * 60)
    print("  reading: full X wins X. As the '/' stroke is covered, '\\' catches")
    print("  up and ties/passes X -- the surviving pixels are equally a '\\' or")
    print("  an occluded X. Partial match degrades gracefully into the right")
    print("  sub-shape; the tie IS the honest answer, and wants context to break.")
    print("=" * 60)


if __name__ == "__main__":
    main()
