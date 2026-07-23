"""
THE WORKBOOK — teach him like a regular person (owner, 2026-07-23):
fill in the blank, multiple choice, use the word in a sentence.
Wrong answers get the truth repeated, then a retest — trials to
mastery, measured as a curve.

The formats ARE instruments on his native ops:
  cloze-end   = lookup at a lived seam (recall)
  cloze-mid   = lookup from left context only (the mid-seam wall,
                measured on purpose)
  choice      = check() confidence per option (recognition)
  use-it      = whole retrieval (production)

Predictions filed before first run (agenda conventions):
  W1 cloze-end >= 80% round 1 · W2 cloze-mid LOW round 1 (expected
  wall) · W3 choice > cloze-mid · W4 use-it >= 80% · W5 the curve
  rises with re-teaching.

    python workbook.py
"""
import os
import sys
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "..", "code"))
from isaac import Isaac, tokenize  # noqa: E402

LESSON = [
    "the cat sleeps on the warm bed",
    "the dog runs in the green park",
    "the bird sings from the tall tree",
    "the fish swims in the cold river",
    "the horse eats the fresh grass",
    "the mouse hides under the old floor",
]
ROUNDS = 3
RETEACH = 2


def content_words(seq):
    df = Counter(t for s in LESSON for t in tokenize(s))
    return [t for t in seq if df[t] <= 2]


def drill(isaac, rng):
    """One full worksheet. Returns per-format (right, total, misses)."""
    score = {f: [0, 0, []] for f in
             ("cloze-end", "cloze-mid", "choice", "use-it")}
    wholes = Counter(tuple(s) for s in isaac.observed_sequences)

    for sent in LESSON:
        toks = tokenize(sent)

        # fill in the blank — at the end
        ans, _ = isaac.lookup(toks[:-1])
        ok = ans == toks[-1]
        score["cloze-end"][0] += ok
        score["cloze-end"][1] += 1
        if not ok:
            score["cloze-end"][2].append(sent)

        # fill in the blank — in the middle (left context only)
        mid = len(toks) // 2
        ans, _ = isaac.lookup(toks[:mid])
        ok = ans == toks[mid]
        score["cloze-mid"][0] += ok
        score["cloze-mid"][1] += 1
        if not ok:
            score["cloze-mid"][2].append(sent)

        # multiple choice — his check() confidence per option
        truth = toks[-1]
        others = [tokenize(s)[-1] for s in LESSON
                  if tokenize(s)[-1] != truth]
        opts = [truth] + list(rng.choice(others, 2, replace=False))
        rng.shuffle(opts)
        confs = [(isaac.check(toks[:-1], o)[1], o) for o in opts]
        pick = max(confs)[1]
        ok = pick == truth
        score["choice"][0] += ok
        score["choice"][1] += 1
        if not ok:
            score["choice"][2].append(sent)

    # use the word in a sentence — production from one word
    for sent in LESSON:
        toks = tokenize(sent)
        word = content_words(toks)[0] if content_words(toks) else toks[1]
        cands = [(cnt, seq) for seq, cnt in wholes.items()
                 if word in seq and len(seq) >= 4]
        said = list(max(cands)[1]) if cands else []
        ok = bool(said) and word in said and " ".join(said) in LESSON
        score["use-it"][0] += ok
        score["use-it"][1] += 1
        if not ok:
            score["use-it"][2].append(sent)
    return score


if __name__ == "__main__":
    rng = np.random.default_rng(11)
    isaac = Isaac()
    isaac.wave_logging = False

    print("=" * 70)
    print("  THE WORKBOOK — schoolwork as instrument")
    print("=" * 70)
    print(f"\n  lesson: {len(LESSON)} sentences, taught x3")
    for _ in range(3):
        for s in LESSON:
            isaac.observe(tokenize(s))
    isaac.consolidate()

    curves = {}
    for rnd in range(1, ROUNDS + 1):
        score = drill(isaac, rng)
        row = "  ".join(f"{f} {s[0]}/{s[1]}"
                        for f, s in score.items())
        print(f"  round {rnd}:  {row}")
        for f, s in score.items():
            curves.setdefault(f, []).append(s[0] / max(s[1], 1))
        # the regular-person loop: the truth, repeated, for misses
        missed = sorted({m for s in score.values() for m in s[2]})
        for sent in missed:
            for _ in range(RETEACH):
                isaac.observe(tokenize(sent))
        if missed:
            isaac.consolidate()

    print("\n  the curves (round 1 -> {}):".format(ROUNDS))
    for f, c in curves.items():
        arrow = " -> ".join(f"{v:.0%}" for v in c)
        print(f"    {f:10s} {arrow}")

    w1 = curves["cloze-end"][0] >= 0.8
    w2 = curves["cloze-mid"][0] <= 0.5          # the wall, measured
    w3 = curves["choice"][0] > curves["cloze-mid"][0]
    w4 = curves["use-it"][0] >= 0.8
    w5 = all(c[-1] >= c[0] for c in curves.values())
    for name, held, note in [
            ("W1 cloze-end native", w1, f"{curves['cloze-end'][0]:.0%}"),
            ("W2 mid-seam wall shown", w2, f"{curves['cloze-mid'][0]:.0%}"),
            ("W3 recognition > recall", w3,
             f"{curves['choice'][0]:.0%} vs {curves['cloze-mid'][0]:.0%}"),
            ("W4 production", w4, f"{curves['use-it'][0]:.0%}"),
            ("W5 the curve rises", w5, "")]:
        print(f"    {'HOLDS ' if held else 'FAILS '} {name}  {note}")
