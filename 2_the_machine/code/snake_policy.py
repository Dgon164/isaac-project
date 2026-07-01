"""
HIS MOVE POLICY — positives AND negatives, the decision run in him.

Snake is mostly about what you CAN'T do. So we teach negatives: a move into a
body cell or a wall is blocked. The policy is his, as a composition of learned
check()s -- the same negative-first shape as can_check():

    for each cardinal move d:
        1. NEGATIVE FIRST: check 'is d blocked?'  -> if yes, rule it out
        2. POSITIVE:       check 'is d toward food?' -> if yes, it's a good move
    if no good move survives, fall back to ANY non-blocked move (survival)

Every predicate is his check() over learned doors. Two things are taught:
    food module (positive):  food-direction signs  -> go_<d>   (multi-answer)
    block module (negative):  neighbor content      -> blocked  (body/wall)
The retina only LOOKS (food relative position; what's in the 4 neighbor cells).
The deciding -- rule out, then keep -- is his.
"""

import numpy as np
from isaac import Isaac

RNG = np.random.default_rng(5)
N = 12
DIRS = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}


def sgn(x):
    return "pos" if x > 0 else ("neg" if x < 0 else "zero")


# ── world ──────────────────────────────────────────────────────────
def gen_snake(L):
    head = (int(RNG.integers(1, N - 1)), int(RNG.integers(1, N - 1)))
    cells = [head]
    while len(cells) < L:
        cr, cc = cells[-1]
        opts = [(cr + dr, cc + dc) for dr, dc in DIRS.values()
                if 0 <= cr + dr < N and 0 <= cc + dc < N
                and (cr + dr, cc + dc) not in cells]
        if not opts:
            break
        cells.append(opts[int(RNG.integers(len(opts)))])
    return cells


def random_scene():
    cells = gen_snake(int(RNG.integers(2, 6)))
    occupied = set(cells)
    while True:
        f = (int(RNG.integers(0, N)), int(RNG.integers(0, N)))
        if f not in occupied:
            return cells, f


def neighbor_content(cells, food, d):
    (hr, hc) = cells[0]
    dr, dc = DIRS[d]
    nr, nc = hr + dr, hc + dc
    if not (0 <= nr < N and 0 <= nc < N):
        return "wall"
    if (nr, nc) in set(cells[1:]):
        return "body"
    if (nr, nc) == food:
        return "food"
    return "empty"


def toward_food(cells, food, d):
    (hr, hc), (fr, fc) = cells[0], food
    return ((d == "up" and fr < hr) or (d == "down" and fr > hr) or
            (d == "left" and fc < hc) or (d == "right" and fc > hc))


# ── teaching: positives and NEGATIVES ──────────────────────────────
def teach(isaac):
    # block module (the NEGATIVE): content alone decides blocked/open
    for _ in range(60):
        isaac.observe(["neighbor", "body", "blocked"])
        isaac.observe(["neighbor", "wall", "blocked"])
        isaac.observe(["neighbor", "empty", "open"])
        isaac.observe(["neighbor", "food", "open"])
    # food module (the POSITIVE): which cardinal moves head toward the food
    for _ in range(400):
        cells, food = random_scene()
        (hr, hc), (fr, fc) = cells[0], food
        ctx = [f"food_dx_{sgn(fc - hc)}", f"food_dy_{sgn(fr - hr)}"]
        for d in DIRS:
            if toward_food(cells, food, d):
                isaac.observe(ctx + [f"go_{d}"])
    isaac.consolidate()


# ── his decision ───────────────────────────────────────────────────
def his_move(isaac, cells, food):
    (hr, hc), (fr, fc) = cells[0], food
    food_ctx = [f"food_dx_{sgn(fc - hc)}", f"food_dy_{sgn(fr - hr)}"]

    def blocked(d):                               # NEGATIVE, his check
        ok, _ = isaac.check(["neighbor", neighbor_content(cells, food, d)], "blocked")
        return ok

    def heads_to_food(d):                         # POSITIVE, his check
        ok, _ = isaac.check(food_ctx, f"go_{d}")
        return ok

    good = {d for d in DIRS if not blocked(d) and heads_to_food(d)}  # rule out, then keep
    if good:
        return good, "toward food"
    safe = {d for d in DIRS if not blocked(d)}    # survival fallback
    return safe, "survival (no open move toward food)"


# ── eval + render ──────────────────────────────────────────────────
def render(cells, food):
    g = np.full((N, N), ".", dtype="<U1")
    for c in cells[1:]:
        g[c] = "~"
    g[cells[0]] = "H"
    g[food] = "*"
    return "\n".join("   " + " ".join(r) for r in g)


def main():
    isaac = Isaac()
    teach(isaac)

    print("=" * 72)
    print("  HIS MOVE POLICY  (negatives taught: body / wall block a move)")
    print("=" * 72)

    n = 400
    suicidal = optimal = survived = had_choice = 0
    for _ in range(n):
        cells, food = random_scene()
        chosen, _ = his_move(isaac, cells, food)
        open_dirs = {d for d in DIRS if neighbor_content(cells, food, d) in ("empty", "food")}
        good = {d for d in DIRS if d in open_dirs and toward_food(cells, food, d)}
        if chosen & (set(DIRS) - open_dirs):       # picked a blocked move?
            suicidal += 1
        if good:
            had_choice += 1
            if chosen == good:                     # picked exactly the safe-toward-food moves
                optimal += 1
        elif open_dirs and chosen == open_dirs:
            survived += 1

    print(f"\n  on {n} novel scenes:")
    print(f"    never moved into a body/wall : {(n-suicidal)/n:5.0%}  "
          f"(the negatives held)")
    print(f"    picked exactly the safe moves")
    print(f"    toward food (when any exist) : {optimal/max(had_choice,1):5.0%}")

    print("\n  EXAMPLES (note the body ruling out a move toward the food):")
    # food is up-right, but a body cell sits directly above the head
    cells = [(6, 6), (5, 6), (4, 6)]               # head (6,6), body goes UP
    food = (3, 9)                                  # up AND right
    print(render(cells, food))
    chosen, why = his_move(isaac, cells, food)
    print(f"    food is up-right; body is directly UP.")
    print(f"    his move: {sorted(chosen)}  ({why})")
    print(f"    -> 'up' is toward food but RULED OUT (body); 'right' survives.\n")

    # food straight left, but body is to the left -> survival
    cells = [(6, 6), (6, 5), (6, 4)]               # body goes LEFT
    food = (6, 1)                                  # straight left
    print(render(cells, food))
    chosen, why = his_move(isaac, cells, food)
    print(f"    food is straight left; body blocks LEFT.")
    print(f"    his move: {sorted(chosen)}  ({why})")
    print(f"    -> the only food-ward move is blocked, so he picks a safe move to live.")

    print("\n" + "=" * 72)
    print("  The decision is his: negatives checked first rule moves out, positives")
    print("  keep the ones toward food, survival covers the rest. Teaching negatives")
    print("  is what makes him stop walking into himself.")


if __name__ == "__main__":
    main()
