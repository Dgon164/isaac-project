"""
LEARNING LOOP — brick #2b.  Attempt -> compare -> learn from the difference.

The correction that drives this file: we do NOT give Isaac the method. We give
him the grid and the answer; he makes an attempt; he learns from attempt-minus-
truth. (Predictive coding.) Feature extraction is something he LEARNS, never
something we install. The harness computes truth ONLY to supply the comparison
target -- it never produces Isaac's answer.

The point being tested: the ANSWER'S REPRESENTATION decides whether learning
transfers across translation.

  ABSOLUTE target: "the center is at (cr,cc)".  Every position has a different
      answer -> a novel position has no learnable shared answer -> no transfer.

  RELATIVE target: "the corners are at offsets (-h,-h),(+h,+h),(-h,+h),(+h,-h)
      from the center".  For a fixed size this answer is THE SAME at every
      position -> every example reinforces one answer -> a novel position falls
      back to that dominant answer, which is correct -> transfer.

This is your 4x4-square example: corners are fixed offsets from center, position
does not matter. Relative encoding is what makes localization translation-invariant.
"""

import numpy as np
from isaac import Isaac

GRID = 11
SIZE = 3            # fixed size here; the offset answer is then constant
H = SIZE // 2       # half-size -> the corner offset magnitude


def make_grid(r, c):
    g = np.zeros((GRID, GRID), dtype=int)
    g[r:r + SIZE, c:c + SIZE] = 1
    return g


def flat(grid):
    return [str(int(v)) for v in grid.flatten()]


def positions():
    return [(r, c) for r in range(GRID - SIZE + 1)
            for c in range(GRID - SIZE + 1)]


def run(target_mode, train_pos, test_pos):
    """target_mode = 'absolute' or 'relative'.
    Returns (learning_curve, train_acc, test_acc)."""
    isaac = Isaac()

    def truth_token(r, c):
        cr, cc = r + H, c + H            # the object's center (we may KNOW it)
        if target_mode == "absolute":
            return f"ctr_{cr}_{cc}"
        else:
            # corner offsets from center -- identical for every position
            return f"off_{H}"            # the whole relative answer collapses to h

    # ── the loop: attempt, compare, learn ──────────────────────
    curve = []          # running accuracy of Isaac's ATTEMPT before learning
    seen = 0
    correct = 0
    rng = np.random.default_rng(0)
    stream = list(train_pos)
    rng.shuffle(stream)
    for (r, c) in stream:
        g = make_grid(r, c)
        truth = truth_token(r, c)
        # ATTEMPT (Isaac's guess, before being told)
        attempt, _ = isaac.lookup(flat(g) + ["ask"])
        seen += 1
        correct += (attempt == truth)
        if seen % 10 == 0:
            curve.append(correct / seen)
        # COMPARE happened above; LEARN from the answer
        isaac.observe(flat(g) + ["ask", truth])
        isaac.consolidate()

    def acc(pos):
        ok = 0
        for (r, c) in pos:
            g = make_grid(r, c)
            attempt, _ = isaac.lookup(flat(g) + ["ask"])
            ok += (attempt == truth_token(r, c))
        return ok / len(pos)

    return curve, acc(train_pos), acc(test_pos)


def main():
    allp = positions()
    train = [p for p in allp if (p[0] + p[1]) % 2 == 0]
    test = [p for p in allp if (p[0] + p[1]) % 2 == 1]  # novel positions

    print("=" * 64)
    print(f"  PREDICT -> COMPARE -> LEARN   ({SIZE}x{SIZE} square, grid {GRID})")
    print(f"  train positions: {len(train)}   novel test positions: {len(test)}")
    print("=" * 64)

    for mode in ("absolute", "relative"):
        curve, tr, te = run(mode, train, test)
        print(f"\n  TARGET = {mode.upper()}")
        curve_str = " ".join(f"{x:.0%}" for x in curve)
        print(f"    attempt accuracy while learning: {curve_str}")
        print(f"    final on TRAIN (seen positions): {tr:.0%}")
        print(f"    final on TEST  (novel positions): {te:.0%}")

    print("\n" + "=" * 64)
    print("  reading:")
    print("  ABSOLUTE -> memorizes seen positions, ~0% on novel (answer differs")
    print("             everywhere, nothing to transfer).")
    print("  RELATIVE -> transfers to novel positions (one position-invariant")
    print("             answer; novel grids fall back to it correctly).")
    print("  => translation-invariance lives in HOW the answer is encoded.")
    print("     Relative gets you POSITION-free structure; an absolute center")
    print("     still needs ONE anchor read from pixels (the next brick).")
    print("=" * 64)


if __name__ == "__main__":
    main()
