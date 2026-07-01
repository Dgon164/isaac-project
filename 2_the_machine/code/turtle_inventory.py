"""
AUTO-INVENTORY + THE TURTLE LOOP.

What this tests (the user's scenario, made runnable):
  - he automatically tracks everything in a scene into working memory
    (a slot per recognized kind, plus an 'unknown' bucket)
  - asked "how many turtles?", he can hold TWO honest facts at once:
      (a) "turtle" is not a word I know            <- unknown LABEL  (no doors)
      (b) but 1 shape here matches nothing I know  <- unknown THING  (the residual)
  - we confirm  turtle := that unknown shape  -> he mints it
  - next scene: he now counts turtles, at NEW positions (translation generalizes)
  - a SCALED turtle shrugs again -> the honest limit that motivates vector mapping

The boundary, stated plainly:
  WIRED RETINA (cheap, allowed, NOT cognition): segment the scene into separate
  shapes (connected components) and crop each to its bounding box. Cropping is
  what deletes translation -- the same 'extraction' the notes endorse.
  HIS (cognition): recognition is lookup(signature)->name, his matmul. The
  inventory lives in his working memory. The unknown/confirm/generalize logic is
  the shrug + mint + set-difference he already has.
"""

import numpy as np
from isaac import Isaac


# ── wired retina ───────────────────────────────────────────────────
def components(scene):
    """Connected components (4-conn). Returns a list of cropped bitmaps,
    each a separate shape. This is perception's grouping step, not thought."""
    H, W = scene.shape
    seen = np.zeros_like(scene, dtype=bool)
    shapes = []
    for y in range(H):
        for x in range(W):
            if scene[y, x] == 1 and not seen[y, x]:
                # BFS this blob
                stack = [(y, x)]; seen[y, x] = True; cells = []
                while stack:
                    cy, cx = stack.pop(); cells.append((cy, cx))
                    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and scene[ny, nx] == 1 \
                                and not seen[ny, nx]:
                            seen[ny, nx] = True; stack.append((ny, nx))
                ys = [c[0] for c in cells]; xs = [c[1] for c in cells]
                y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
                crop = np.zeros((y1 - y0 + 1, x1 - x0 + 1), dtype=int)
                for (cy, cx) in cells:
                    crop[cy - y0, cx - x0] = 1
                shapes.append(crop)
    return shapes


def signature(bitmap):
    """Canonical form of a cropped shape: its size + bits, as ONE token.
    Translation-free (already cropped). NOT scale/rotation-free -- on purpose."""
    h, w = bitmap.shape
    bits = "".join(str(int(v)) for v in bitmap.flatten())
    return f"sig{h}x{w}_{bits}"


# ── his side ───────────────────────────────────────────────────────
def teach_shape(isaac, bitmap, name):
    """Learn: this signature IS this named shape. One door, his matmul recall."""
    isaac.observe([signature(bitmap), name])

def knows_word(isaac, word):
    """Is this a word he has ANY structure for? (unknown LABEL test)"""
    return bool(isaac.net.doors.get(word)) or \
        any(word in tgts for tgts in isaac.net.doors.values())

def recognize(isaac, bitmap):
    """His recognition: signature -> name, or None on a shrug."""
    name, conf = isaac.lookup([signature(bitmap)])
    return name if (name is not None and conf >= 1.0) else None

def take_inventory(isaac, scene, mem="scene"):
    """Auto-track everything present into working memory. A slot per known
    kind; an 'unknown' bucket (with stashed signatures) for the residual."""
    isaac.scratch.clear(mem + "_unknown_sigs")
    inv = {}
    for shape in components(scene):
        name = recognize(isaac, shape)
        if name is None:
            inv["unknown"] = inv.get("unknown", 0) + 1
            isaac.scratch.append(mem + "_unknown_sigs", signature(shape))
        else:
            inv[name] = inv.get(name, 0) + 1
    for k, v in inv.items():
        isaac.scratch.write(f"{mem}:{k}", v)        # the inventory lives in him
    return inv


def ask_how_many(isaac, name, inv, mem="scene"):
    """His honest answer. Two independent facts, always both reported when true:
      - do I know the WORD?            (knows_word: any doors)
      - is there an unnamed RESIDUAL?  (the 'unknown' bucket)
    The residual is surfaced even for known words -- a shape I can't match could
    be a hard instance (wrong size/angle) of the very thing being asked about."""
    unknown = inv.get("unknown", 0)
    if knows_word(isaac, name):
        n = inv.get(name, 0)
        if unknown:
            return (f"{n} that i recognize as '{name}'. but i'm also tracking "
                    f"{unknown} shape(s) i can't identify -- one could be a "
                    f"'{name}' i fail to match (different size/angle?).")
        return f"{n}"
    if unknown:
        return (f"i don't know what a '{name}' is (no such concept) -- but i'm "
                f"tracking {unknown} shape(s) here that match nothing i know. "
                f"could one of those be a '{name}'?")
    return f"i don't know what a '{name}' is, and i see nothing unaccounted for."


# ── shapes ─────────────────────────────────────────────────────────
SQUARE = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]])
LINE   = np.array([[1, 1, 1, 1, 1]])
CROSS  = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])
TURTLE = np.array([[0, 1, 0],                       # the novel shape
                   [1, 1, 1],
                   [1, 0, 1]])
TURTLE_BIG = np.array([[0, 0, 1, 1, 0, 0],          # a 2x-scaled turtle
                       [0, 0, 1, 1, 0, 0],
                       [1, 1, 1, 1, 1, 1],
                       [1, 1, 1, 1, 1, 1],
                       [1, 1, 0, 0, 1, 1],
                       [1, 1, 0, 0, 1, 1]])


def place(canvas_shape, items):
    """Drop shapes onto a blank canvas at given top-left positions (gaps keep
    them as separate components)."""
    scene = np.zeros(canvas_shape, dtype=int)
    for bmp, (y, x) in items:
        h, w = bmp.shape
        scene[y:y + h, x:x + w] = bmp
    return scene


def show(inv):
    return "{" + ", ".join(f"{k}:{v}" for k, v in sorted(inv.items())) + "}"


def main():
    isaac = Isaac()
    for bmp, name in [(SQUARE, "square"), (LINE, "line"), (CROSS, "cross")]:
        teach_shape(isaac, bmp, name)
    isaac.consolidate()

    print("=" * 72)
    print("  AUTO-INVENTORY + TURTLE LOOP")
    print("=" * 72)
    print("  taught (named): square, line, cross.   'turtle' is NOT a word yet.")
    print("-" * 72)

    # scene 1: two squares (different spots), a line, and the novel shape
    scene1 = place((20, 20), [
        (SQUARE, (1, 1)), (SQUARE, (1, 10)),     # same shape, two positions
        (LINE,   (8, 2)),
        (TURTLE, (14, 12)),                      # the unknown
    ])
    inv1 = take_inventory(isaac, scene1)
    print("\n  SCENE 1 ->", show(inv1))
    print("    (two squares at different positions both counted: translation OK)")

    print("\n  Q: how many squares?")
    print("  A:", ask_how_many(isaac, "square", inv1))
    print("\n  Q: how many turtles?")
    print("  A:", ask_how_many(isaac, "turtle", inv1))

    # confirmation: bind 'turtle' to the unknown signature he stashed, then mint
    unknown_sig = isaac.scratch.read("scene_unknown_sigs")
    unknown_sig = unknown_sig[-1] if isinstance(unknown_sig, list) else unknown_sig
    print("\n  [confirmation arrives] -> that unknown shape is a 'turtle'.")
    isaac.observe([unknown_sig, "turtle"])       # mint the new concept
    isaac.consolidate()
    print("  minted. 'turtle' is now a word he knows:", knows_word(isaac, "turtle"))

    # scene 2: turtles at NEW positions (+ knowns) -> does it generalize?
    scene2 = place((20, 20), [
        (TURTLE, (1, 1)), (TURTLE, (2, 14)), (TURTLE, (12, 6)),  # 3 turtles, new spots
        (SQUARE, (12, 15)),
    ])
    inv2 = take_inventory(isaac, scene2)
    print("\n  SCENE 2 (turtles at new positions) ->", show(inv2))
    print("  Q: how many turtles?")
    print("  A:", ask_how_many(isaac, "turtle", inv2))
    print("    -> translation GENERALIZES: recognized turtles wherever they sat.")

    # scene 3: a SCALED turtle -> the honest limit
    scene3 = place((20, 20), [(TURTLE_BIG, (2, 2)), (LINE, (15, 5))])
    inv3 = take_inventory(isaac, scene3)
    print("\n  SCENE 3 (a 2x-scaled turtle) ->", show(inv3))
    print("  Q: how many turtles?")
    print("  A:", ask_how_many(isaac, "turtle", inv3))
    print("    -> SCALE does NOT generalize: the big turtle reads as unknown.")
    print("       This is the wall vector-mapping exists to solve (size/rotation")
    print("       invariance). The signature is translation-free, not scale-free.")

    print("\n" + "=" * 72)
    print("  What worked, his way: auto-inventory in working memory; the dual")
    print("  honest-unknown (no such WORD + N unnamed THINGS); provisional bind")
    print("  -> confirm -> mint; translation generalization for free.")
    print("  What's exposed: identity is still tied to the exact normalized")
    print("  bitmap, so scale/rotation shrug. That residual IS the next problem.")


if __name__ == "__main__":
    main()
