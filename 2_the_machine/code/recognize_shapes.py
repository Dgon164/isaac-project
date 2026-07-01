"""
RECOGNITION — brick #1.  Can Isaac name what a grid IS?

Rules respected:
  - Isaac receives ONLY the raw grid (1s and 0s) + the correct answer token.
  - Querying passes the raw grid in; the answer comes from Isaac.lookup,
    not from any logic I wrote. No feature extraction. No decide().

Two questions, kept separate and honest:
  (1) RECALL    — show a trained pattern back exactly. Does he name it?
  (2) ROBUSTNESS— flip 1 or 2 pixels (noise). Does the name survive?

Everything is printed as a bitmap so you can see exactly what he is shown.
"""

import numpy as np
from isaac import Isaac

RNG = np.random.default_rng(3)
SZ = 5  # 5x5 grids


# ── the patterns (raw 1s and 0s) ───────────────────────────────
# Each is a hand-drawn 5x5. The NAME is the correct answer, not a hint
# painted onto the pixels.
PATTERNS = {
    "square": [
        "11111",
        "10001",
        "10001",
        "10001",
        "11111",
    ],
    "cross": [
        "00100",
        "00100",
        "11111",
        "00100",
        "00100",
    ],
    "L": [
        "10000",
        "10000",
        "10000",
        "10000",
        "11111",
    ],
    "digit_1": [
        "00100",
        "01100",
        "00100",
        "00100",
        "01110",
    ],
    "digit_7": [
        "11111",
        "00001",
        "00010",
        "00100",
        "01000",
    ],
}


def to_grid(rows):
    return np.array([[int(c) for c in r] for r in rows], dtype=int)


def show(grid):
    return "\n".join("    " + "".join("#" if v else "." for v in row)
                     for row in grid)


def flat_tokens(grid):
    """Lossless tokenization: each cell is '0' or '1', read row by row.
    No labels, no extraction — just the pixels."""
    return [str(int(v)) for v in grid.flatten()]


def teach(isaac, name, grid):
    """Show the raw grid, then the correct answer, as one sequence."""
    isaac.observe(flat_tokens(grid) + [f"this_is_{name}"])


def ask(isaac, grid):
    """Pass raw pixels in; read what Isaac says. Returns (name, confidence)."""
    ans, conf = isaac.lookup(flat_tokens(grid))
    name = ans[len("this_is_"):] if isinstance(ans, str) \
        and ans.startswith("this_is_") else None
    return name, conf


def add_noise(grid, k):
    """Flip exactly k random pixels."""
    g = grid.copy()
    idx = RNG.choice(SZ * SZ, size=k, replace=False)
    flat = g.flatten()
    flat[idx] = 1 - flat[idx]
    return flat.reshape(SZ, SZ)


def main():
    grids = {n: to_grid(r) for n, r in PATTERNS.items()}

    print("=" * 60)
    print("  WHAT ISAAC IS SHOWN (raw 1s and 0s)")
    print("=" * 60)
    for n, g in grids.items():
        print(f"\n  {n}:")
        print(show(g))

    isaac = Isaac()
    for n, g in grids.items():
        teach(isaac, n, g)
    isaac.consolidate()

    # ── (1) RECALL: exact patterns back ────────────────────────
    print("\n" + "=" * 60)
    print("  (1) RECALL — show the exact trained grid back")
    print("=" * 60)
    recall_ok = 0
    for n, g in grids.items():
        pred, conf = ask(isaac, g)
        mark = "OK " if pred == n else "XX "
        recall_ok += pred == n
        print(f"  {mark} {n:<9} -> said: {str(pred):<9} (conf {conf:.2f})")
    print(f"\n  recall: {recall_ok}/{len(grids)}")

    # ── (2) ROBUSTNESS: flip pixels ────────────────────────────
    for k in (1, 2):
        print("\n" + "=" * 60)
        print(f"  (2) ROBUSTNESS — flip {k} pixel(s), 20 tries each pattern")
        print("=" * 60)
        for n, g in grids.items():
            ok = 0
            trials = 20
            for _ in range(trials):
                ng = add_noise(g, k)
                pred, _ = ask(isaac, ng)
                ok += pred == n
            print(f"  {n:<9} survived noise: {ok}/{trials} = {ok/trials:.0%}")

    print("\n" + "=" * 60)
    print("  reading: high recall + low noise-survival means he RECOGNIZES")
    print("  exact patterns but matches too literally to tolerate change.")
    print("  high on both would mean real, robust recognition.")
    print("=" * 60)


if __name__ == "__main__":
    main()
