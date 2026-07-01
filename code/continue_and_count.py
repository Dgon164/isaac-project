"""
Two direct tests, per the steer — no cathedral.

(B) CONTINUATION: give him a line, ask where the next pixel goes. Then arcs.
    Encoded as RELATIVE TURN at each step (the free differentiation of heading):
    a line is 'straight straight straight...', an arc is a constant small turn.
    Relative -> a line is the same token sequence whichever way it points, so it
    should generalize across position AND orientation. Predict the next turn ->
    place the next pixel. We render his continuation so we can SEE it.

(A) EDGE COUNT: show him a shape's boundary turn-sequence, tell him the count,
    a few times, test novel shapes. circle=1, triangle=3, square=4. Does he
    figure it out, or memorize? (If he can't, that's critical -- we want to know.)
"""

import numpy as np
from isaac import Isaac

# 8 compass headings, indexed 0..7 (E, NE, N, NW, W, SW, S, SE)
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]


def turn_tok(t):
    """Relative turn in eighths: 0=straight, +k=left, -k=right."""
    t = ((t + 4) % 8) - 4
    return f"t{t:+d}"


# ─────────────────── (B) CONTINUATION ───────────────────
def path_turns(headings):
    return [turn_tok(headings[i+1] - headings[i]) for i in range(len(headings)-1)]


def make_path(start_dir, curvature, n):
    """Heading sequence: starts at start_dir, turns by `curvature` each step."""
    return [(start_dir + curvature * i) % 8 for i in range(n)]


def teach_continuation(isaac):
    # lines (curvature 0) and arcs (curvature +1, -1) at EVERY starting heading
    for d in range(8):
        for k in (0, 1, -1):
            seq = path_turns(make_path(d, k, 8))
            if len(seq) >= 2:
                isaac.observe(seq)
    isaac.consolidate()


def continue_path(isaac, prefix_headings, steps):
    """Given a few headings, predict the next turns and roll the path forward."""
    headings = list(prefix_headings)
    turns = path_turns(headings)
    out_dirs = list(headings)
    for _ in range(steps):
        ctx = turns[-3:] if len(turns) >= 1 else ["t+0"]
        pn = isaac.predict_next(ctx)
        if not pn:
            break
        pred = pn["prediction"]               # like 't+0' or 't+1'
        try:
            dt = int(pred[1:])
        except (ValueError, IndexError):
            break
        nh = (out_dirs[-1] + dt) % 8
        out_dirs.append(nh)
        turns.append(turn_tok(dt))
    return out_dirs


def render_path(dirs, start=(20, 20)):
    pts = [start]
    for d in dirs[1:]:
        dx, dy = DIRS[d % 8]
        pts.append((pts[-1][0] + dx, pts[-1][1] + dy))
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    x0, y0 = min(xs), min(ys)
    W = max(xs) - x0 + 1; H = max(ys) - y0 + 1
    grid = [["." for _ in range(W)] for _ in range(H)]
    for (x, y) in pts:
        grid[y - y0][x - x0] = "#"
    return "\n".join("    " + "".join(r) for r in grid)


def test_continuation():
    isaac = Isaac()
    teach_continuation(isaac)
    print("=" * 60)
    print("  (B) CONTINUATION — give a few steps, he predicts the rest")
    print("=" * 60)

    cases = [
        ("line pointing NE (orientation never trained alone)", make_path(1, 0, 4), 0, 8),
        ("arc curving left, start E", make_path(0, 1, 4), 1, 8),
        ("arc curving right, start N", make_path(2, -1, 4), -1, 8),
    ]
    for label, prefix, true_k, steps in cases:
        dirs = continue_path(isaac, prefix, steps)
        cont_turns = path_turns(dirs)[len(prefix)-1:]
        ok = all(t == turn_tok(true_k) for t in cont_turns) if cont_turns else False
        print(f"\n  {label}")
        print(f"    predicted continuation turns: {cont_turns}  "
              f"{'(correct)' if ok else '(WRONG)'}")
        print(render_path(dirs))


# ─────────────────── (A) EDGE COUNT ───────────────────
RES = 24  # finer heading resolution (15 deg/step) so corners != curvature


def polygon_headings(n_sides, per_side=6):
    """A CLOSED convex polygon as headings on a 24-dir compass: n_sides straight
    runs, a sharp corner (exterior angle 360/n) between each, loop closed so all
    n corners are present. A circle = RES tiny 1-step turns (one smooth edge)."""
    if n_sides == 0:  # circle
        return [(i % RES) for i in range(RES + 1)]
    turn = round(RES / n_sides)            # exterior angle in steps (e.g. tri=8)
    headings, h = [], 0
    for s in range(n_sides):
        headings += [h % RES] * per_side
        h += turn
    headings += [h % RES]                  # close the loop (the n-th corner)
    return headings


def edge_count_oracle(headings):
    """Answer key: count SHARP turns (>=45deg) = edges. A circle's 1-step turns
    are gentle -> 0 sharp -> reported as 1 smooth edge."""
    turns = [((headings[i+1]-headings[i]+RES//2) % RES)-RES//2
             for i in range(len(headings)-1)]
    sharp = sum(1 for t in turns if abs(t) >= 3)   # >=45deg is a corner
    return sharp if sharp > 0 else 1


def rturn_tok(a, b):
    """Relative turn token at RES resolution."""
    t = ((b - a + RES // 2) % RES) - RES // 2
    return f"T{t:+d}"


def test_edge_count():
    print("\n" + "=" * 60)
    print("  (A) EDGE COUNT — show boundary turns + answer, then test novel")
    print("=" * 60)
    isaac = Isaac()
    shapes = {"triangle": 3, "square": 4, "pentagon": 5, "hexagon": 6, "circle": 0}

    # teach: turn-sequence -> edge count, several side-lengths each
    for name, n in shapes.items():
        for ps in (4, 5, 6, 7):
            h = polygon_headings(n, ps)
            turns = [rturn_tok(h[i], h[i+1]) for i in range(len(h)-1)]
            true = edge_count_oracle(h)
            if len(turns) >= 2:
                isaac.observe(turns + [f"edges_{true}"])
    isaac.consolidate()

    print("  oracle (answer key) on the turn-signal:")
    for name, n in shapes.items():
        h = polygon_headings(n, 6)
        print(f"    {name:9} -> oracle says {edge_count_oracle(h)} edges")

    print("\n  Isaac on NOVEL side-lengths (did he learn, or memorize?):")
    correct = 0
    for name, n in shapes.items():
        h = polygon_headings(n, 8)  # novel side length
        turns = [rturn_tok(h[i], h[i+1]) for i in range(len(h)-1)]
        ans, conf = isaac.lookup(turns)
        true = edge_count_oracle(h)
        got = ans if isinstance(ans, str) and ans.startswith("edges_") else "?"
        ok = got == f"edges_{true}"
        correct += ok
        print(f"    {name:9} true edges_{true:<2} -> Isaac said {got:10} "
              f"{'OK' if ok else 'X'}")
    print(f"\n  edge-count generalization: {correct}/{len(shapes)}")


if __name__ == "__main__":
    test_continuation()
    test_edge_count()
