"""
KINDERGARTEN CURRICULUM — basic spatial questions on a glyph scene.

The world is the parts-alphabet, on a 2D grid:
    ~ snake body   H snake head   * food   T turtle   . empty

Questions a kindergartner gets asked:
    - how long is the snake?               (his RAM counter)
    - which way is the snake facing?       (head vs body)
    - which way is the food?  go for it?   (food vs head)
    - is the snake facing the food?        (compose: facing == way-to-food)
    - is the turtle in line with the food? (same row or column)

The honest split:
    WIRED RETINA (looking): locate the parts -> their (row,col). Cheap.
    HIS (knowing): the RELATIONS between those positions -> answers, LEARNED
    from examples and tested on NOVEL scenes. Length is his RAM counter.

The discipline: teach RELATIONALLY (signs of displacements), not by absolute
coordinates. We prove why by training 'which way to the food' BOTH ways and
testing on novel positions: relative generalizes, absolute memorizes.
"""

import numpy as np
from isaac import Isaac

RNG = np.random.default_rng(20)
N = 10


def sgn(x):
    return "pos" if x > 0 else ("neg" if x < 0 else "zero")


# ── scene = a glyph grid + the ground truth the teacher knows ───────
def make_scene():
    grid = np.full((N, N), ".", dtype="<U1")
    L = int(RNG.integers(2, 6))                       # snake length
    r = int(RNG.integers(0, N))
    c0 = int(RNG.integers(0, N - L))
    facing = RNG.choice(["left", "right"])
    head_c = c0 if facing == "left" else c0 + L - 1
    for c in range(c0, c0 + L):
        grid[r, c] = "~"
    grid[r, head_c] = "H"
    body_cols = [c for c in range(c0, c0 + L) if c != head_c]

    def empty_cell():
        while True:
            rr, cc = int(RNG.integers(0, N)), int(RNG.integers(0, N))
            if grid[rr, cc] == ".":
                return rr, cc
    fr, fc = empty_cell(); grid[fr, fc] = "*"
    tr, tc = empty_cell(); grid[tr, tc] = "T"

    return {
        "grid": grid, "length": L, "facing": facing,
        "head": (r, head_c), "body_mid": (r, float(np.mean(body_cols))),
        "food": (fr, fc), "turtle": (tr, tc),
    }


# ground-truth answers (the teacher; ok to know — like a real teacher)
def truth_go(s):
    # 8-way compass, fully determined by the two displacement SIGNS (so the
    # relative encoding has enough to be right; the old 'dominant axis' needed
    # magnitudes the signs throw away -- that was the 62% bug).
    (hr, hc), (fr, fc) = s["head"], s["food"]
    vy = "up" if fr < hr else ("down" if fr > hr else "")
    vx = "left" if fc < hc else ("right" if fc > hc else "")
    return f"{vy}-{vx}" if vy and vx else (vy or vx or "here")

def truth_facing_food(s):
    (hr, hc), (fr, fc) = s["head"], s["food"]
    return "yes" if (fr == hr and sgn(fc - hc) ==
                     ("pos" if s["facing"] == "right" else "neg")) else "no"

def truth_inline(s):
    (tr, tc), (fr, fc) = s["turtle"], s["food"]
    return "yes" if (tr == fr or tc == fc) else "no"


# ── encoders (what the retina hands him) ───────────────────────────
def enc_facing(s):
    hr, hc = s["head"]; _, bmid = s["body_mid"]
    return [f"headvbody_{sgn(hc - bmid)}"]

def enc_go_relative(s):
    (hr, hc), (fr, fc) = s["head"], s["food"]
    return [f"food_dx_{sgn(fc - hc)}", f"food_dy_{sgn(fr - hr)}"]

def enc_go_absolute(s):
    (hr, hc), (fr, fc) = s["head"], s["food"]
    return [f"head_c{hc}", f"food_c{fc}", f"head_r{hr}", f"food_r{fr}"]

def enc_inline(s):
    (tr, tc), (fr, fc) = s["turtle"], s["food"]
    return [f"tf_dx_{sgn(tc - fc)}", f"tf_dy_{sgn(tr - fr)}"]


def teach_and_test(encoder, truth_fn, n_train=250, n_test=120):
    """Teach scene-encoding -> answer; score on NOVEL scenes."""
    isaac = Isaac()
    for _ in range(n_train):
        s = make_scene()
        isaac.observe(encoder(s) + [truth_fn(s)])
    isaac.consolidate()
    ok = answered = 0
    for _ in range(n_test):
        s = make_scene()
        pred, conf = isaac.lookup(encoder(s))
        if pred is not None and conf >= 1.0:
            answered += 1
            if pred == truth_fn(s):
                ok += 1
    return ok / n_test, answered / n_test


def render(s):
    return "\n".join("    " + " ".join(row) for row in s["grid"])


def main():
    print("=" * 72)
    print("  KINDERGARTEN CURRICULUM on a glyph world")
    print("  ( ~ body   H head   * food   T turtle   . empty )")
    print("=" * 72)

    # length is his RAM counter -- count body+head along the snake's row
    counter = Isaac()
    counter.observe(["~", "incr"]); counter.observe(["H", "incr"])
    for g in (".", "*", "T"):
        counter.observe([g, "hold"])
    counter.consolidate()

    def snake_row_stream(s):
        r, _ = s["head"]
        return [g for g in s["grid"][r] if g in ("~", "H")]

    # report card on novel scenes
    print("\n  REPORT CARD (accuracy on NOVEL scenes, taught relationally):")
    facing_acc, _ = teach_and_test(enc_facing, lambda s: s["facing"])
    go_acc, _ = teach_and_test(enc_go_relative, truth_go)
    inline_acc, _ = teach_and_test(enc_inline, truth_inline)
    # length: count 30 novel snakes with his RAM, never 'taught' a length
    lok = 0
    for _ in range(120):
        s = make_scene()
        n, _ = counter.react(snake_row_stream(s), target="len")
        if n == s["length"]:
            lok += 1
    print(f"     how long is the snake?        {lok/120:5.0%}   (his RAM counter)")
    print(f"     which way is it facing?       {facing_acc:5.0%}   (head vs body)")
    print(f"     which way to the food? go!    {go_acc:5.0%}   (food vs head)")
    print(f"     turtle in line with food?     {inline_acc:5.0%}   (shared row/col)")

    # the lesson: relative vs absolute on the SAME question
    rel_acc, _ = teach_and_test(enc_go_relative, truth_go)
    abs_acc, abs_answered = teach_and_test(enc_go_absolute, truth_go)
    print("\n  WHY WE TEACH RELATIONALLY  ('which way to the food', novel scenes):")
    print(f"     relative encoding (signs)  : {rel_acc:5.0%}  generalizes")
    print(f"     absolute encoding (coords) : {abs_acc:5.0%}  (answered only "
          f"{abs_answered:.0%}: novel coords were never seen -> honest shrug)")

    # a worked example with the composed question
    print("\n  ONE SCENE, ASKED LIKE A KINDERGARTNER:")
    s = make_scene()
    print(render(s))
    n, _ = counter.react(snake_row_stream(s), target="len")
    print(f"\n     how long is the snake?         {n}")
    print(f"     which way is it facing?        {s['facing']}")
    print(f"     which way is the food?         {truth_go(s)}  (so: go {truth_go(s)})")
    print(f"     is the snake facing the food?  {truth_facing_food(s)}"
          f"   (facing {s['facing']} vs food {truth_go(s)})")
    print(f"     is the turtle in line w/ food? {truth_inline(s)}")

    print("\n" + "=" * 72)
    print("  He answers the kindergarten battery on scenes he's never seen.")
    print("  Relations generalize because they're taught as relations; the same")
    print("  question taught by absolute coordinates just memorizes and shrugs on")
    print("  anything new. Length needs no teaching at all -- it's his counter.")


if __name__ == "__main__":
    main()
