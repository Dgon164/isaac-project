"""ARC PROBE 1 — observe, resolve (owner, 2026-09-01).

First contact with ARC-AGI: for each task, observe the example
pairs, try to induce the transformation as SHARED STRUCTURE that
holds on every pair (his rule: evidence decides, one counterexample
kills), and apply it to the test input. Five inducers, weakest
honest floor first:

  R0 identity   output == input, every pair
  R1 constant   every pair's output is the same grid
  R2 colormap   same shape, one consistent color->color mapping
  R3 transform  one fixed flip/rotation/transpose fits every pair
  R4 scale/tile output = input tiled or pixel-scaled by constant k

A task counts SOLVED only if every test output matches exactly.
Unsolved = the ask class, counted. Expectations set honestly: these
five catch only the shallow end; the point is the map of what is
missing, not the score.
"""
import json
import os
import sys
from glob import glob

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "data", "arc-agi", "data", "training")
if not os.path.isdir(DIR):
    print("SKIP: arc data not present")
    sys.exit(77)


def flip_h(g):
    return [row[::-1] for row in g]


def flip_v(g):
    return g[::-1]


def transpose(g):
    return [list(r) for r in zip(*g)]


def rot90(g):
    return [list(r) for r in zip(*g[::-1])]


TRANSFORMS = {
    "flip_h": flip_h, "flip_v": flip_v, "transpose": transpose,
    "rot90": rot90, "rot180": lambda g: flip_h(flip_v(g)),
    "rot270": lambda g: rot90(rot90(rot90(g))),
}


def induce_identity(pairs):
    if all(p["input"] == p["output"] for p in pairs):
        return lambda g: g
    return None


def induce_constant(pairs):
    o0 = pairs[0]["output"]
    if all(p["output"] == o0 for p in pairs):
        return lambda g: o0
    return None


def induce_colormap(pairs):
    cmap = {}
    for p in pairs:
        i, o = p["input"], p["output"]
        if len(i) != len(o) or any(len(a) != len(b)
                                   for a, b in zip(i, o)):
            return None
        for ri, ro in zip(i, o):
            for a, b in zip(ri, ro):
                if cmap.setdefault(a, b) != b:
                    return None
    return lambda g: [[cmap.get(c, c) for c in row] for row in g]


def induce_transform(pairs):
    for name, fn in TRANSFORMS.items():
        if all(fn(p["input"]) == p["output"] for p in pairs):
            return fn
    return None


def induce_scale(pairs):
    def factors(p):
        i, o = p["input"], p["output"]
        if not i or not i[0] or len(o) % len(i) or \
                len(o[0]) % len(i[0]):
            return None
        return len(o) // len(i), len(o[0]) // len(i[0])
    f0 = factors(pairs[0])
    if not f0 or f0 == (1, 1) or any(factors(p) != f0 for p in pairs):
        return None
    ky, kx = f0

    def tile(g):
        return [[g[r % len(g)][c % len(g[0])]
                 for c in range(len(g[0]) * kx)]
                for r in range(len(g) * ky)]

    def pixel(g):
        return [[g[r // ky][c // kx]
                 for c in range(len(g[0]) * kx)]
                for r in range(len(g) * ky)]
    for fn in (tile, pixel):
        if all(fn(p["input"]) == p["output"] for p in pairs):
            return fn
    return None


INDUCERS = [("identity", induce_identity),
            ("constant", induce_constant),
            ("colormap", induce_colormap),
            ("transform", induce_transform),
            ("scale", induce_scale)]

solved, by_rule, unsolved = [], {}, 0
for path in sorted(glob(os.path.join(DIR, "*.json"))):
    task = json.load(open(path))
    tid = os.path.basename(path)[:-5]
    got = None
    for name, ind in INDUCERS:
        fn = ind(task["train"])
        if fn is not None and all(fn(t["input"]) == t["output"]
                                  for t in task["test"]):
            got = name
            break
    if got:
        solved.append((tid, got))
        by_rule[got] = by_rule.get(got, 0) + 1
    else:
        unsolved += 1

print(f"ARC-AGI training set, first contact: "
      f"{len(solved)}/400 tasks solved, {unsolved} filed as asks")
for name, n in sorted(by_rule.items(), key=lambda x: -x[1]):
    ids = [t for t, r in solved if r == name][:4]
    print(f"  {name:10s} {n:3d}   e.g. {', '.join(ids)}")
print("\n(view any task id at arcprize.org / the JSONs in "
      "data/arc-agi/data/training)")
