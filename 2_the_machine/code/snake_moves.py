"""
WHICH WAY SHOULD THE SNAKE GO? — multi-answer, cardinal-only.

Two corrections baked in:
  - Snake moves are CARDINAL (up/down/left/right). Diagonal is not a move.
    So 'food is up-right' is not an action -- the actions are {up, right}.
  - Some questions have MORE THAN ONE right answer. Food up-right -> up AND right
    are both valid. That is exactly what check() is for: ask each candidate move
    'is this a good move?' and keep all that pass. lookup() (argmax) returns only
    ONE and drops the other -- so it is the wrong tool for a multi-answer question.

A 'compound' answer here is just the UNION of simple cardinal moves. We teach the
simple moves; the compound falls out of asking check() about each one.
"""

import numpy as np
from isaac import Isaac

RNG = np.random.default_rng(3)
N = 12
DIRS = ["up", "down", "left", "right"]


def sgn(x):
    return "pos" if x > 0 else ("neg" if x < 0 else "zero")


def scene():
    hr, hc = int(RNG.integers(0, N)), int(RNG.integers(0, N))
    while True:
        fr, fc = int(RNG.integers(0, N)), int(RNG.integers(0, N))
        if (fr, fc) != (hr, hc):
            break
    return (hr, hc), (fr, fc)


def good_moves(head, food):
    """Ground truth: every cardinal move that reduces the gap to the food.
    On-axis food -> one move; off-axis (diagonal) food -> two moves."""
    (hr, hc), (fr, fc) = head, food
    m = set()
    if fr < hr: m.add("up")
    if fr > hr: m.add("down")
    if fc < hc: m.add("left")
    if fc > hc: m.add("right")
    return m


def enc(head, food):
    """Relative encoding (signs) -> generalizes across positions."""
    (hr, hc), (fr, fc) = head, food
    return [f"food_dx_{sgn(fc - hc)}", f"food_dy_{sgn(fr - hr)}"]


def teach(isaac, n=400):
    for _ in range(n):
        h, f = scene()
        ctx = enc(h, f)
        for mv in good_moves(h, f):              # teach EACH valid move (multi)
            isaac.observe(ctx + [f"go_{mv}"])
    isaac.consolidate()


def his_moves_check(isaac, head, food):
    """Multi-answer: ask check() about every cardinal move, keep all that pass."""
    ctx = enc(head, food)
    out = set()
    for d in DIRS:
        ok, conf = isaac.check(ctx, f"go_{d}")
        if ok:
            out.add(d)
    return out


def his_move_lookup(isaac, head, food):
    """Single-answer (argmax): the one top move. Misses co-valid moves."""
    ans, conf = isaac.lookup(enc(head, food))
    return ans.replace("go_", "") if ans else None


def main():
    isaac = Isaac()
    teach(isaac)

    print("=" * 72)
    print("  WHICH WAY SHOULD THE SNAKE GO?  (cardinal only, multi-answer)")
    print("=" * 72)

    # score the FULL set on novel scenes: check() vs lookup()
    n = 300
    set_exact = lookup_exact = lookup_partial = 0
    for _ in range(n):
        h, f = scene()
        truth = good_moves(h, f)
        got = his_moves_check(isaac, h, f)
        if got == truth:
            set_exact += 1
        one = his_move_lookup(isaac, h, f)
        if {one} == truth:               # lookup right only if there's ONE answer
            lookup_exact += 1
        if one in truth:                 # lookup's single answer is at least valid
            lookup_partial += 1

    print(f"\n  on {n} novel scenes, recovering the COMPLETE valid move set:")
    print(f"    check() over all 4 moves : {set_exact/n:5.0%} exact-set match")
    print(f"    lookup() single move     : {lookup_exact/n:5.0%} exact-set match "
          f"(only wins when the truth is a single move)")
    print(f"    lookup()'s one move valid: {lookup_partial/n:5.0%} (it's never WRONG,"
          f" it just stops at one)")

    # worked examples: a diagonal-food scene (two answers) and an on-axis one
    print("\n  EXAMPLES:")
    cases = [((5, 5), (2, 9), "food up-and-right"),
             ((5, 5), (5, 9), "food straight right"),
             ((5, 5), (8, 2), "food down-and-left")]
    for h, f, label in cases:
        truth = good_moves(h, f)
        got = his_moves_check(isaac, h, f)
        one = his_move_lookup(isaac, h, f)
        print(f"    {label:<20} truth={sorted(truth)}")
        print(f"        check()  -> {sorted(got)}   (all valid moves)")
        print(f"        lookup() -> ['{one}']        (one move — would miss the other)")

    print("\n" + "=" * 72)
    print("  Multi-answer needs check(): it returns the whole valid set, so a")
    print("  diagonal food yields BOTH cardinal moves. lookup() isn't wrong, it's")
    print("  just single-valued -- it stops at one and drops the rest. No diagonal")
    print("  move is ever produced; compound = the union of simple cardinal moves.")


if __name__ == "__main__":
    main()
