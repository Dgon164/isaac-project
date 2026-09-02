"""OPERATOR INDUCTION (owner question, 2026-09-01: can he learn a
rule ABOUT the data — bit shift, increment, decrement — not just a
fit TO the data?).

The classic symbolic recipe, his courts wrapped around it:
  hypothesis space = compositions (depth <= 2) of primitive discrete
  operators, some parameterized (add k / mul k / xor k, k solved
  from the first pair and verified on the rest);
  the court = the program must reproduce EVERY training pair, then
  every HELD-OUT pair exactly; pure noise must be REFUSED;
  THE LIBRARY (DreamCoder's lesson = his growing-grammar law):
  every induced operator joins the vocabulary under its own name,
  so later inductions search over earlier discoveries — stage 2's
  target is unreachable at the depth budget without stage 1's
  abstraction.

Induced operators are recorded in the FACTS LAYER as rules with
origin=induced and their court receipt — the first induced rules to
enter the layer.
"""
import os
import random
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "..", "code"))
_argv = list(sys.argv)
sys.argv = [_argv[0]]
from isaac import Isaac  # noqa: E402

PRIMS = {
    "inc": lambda x: x + 1,
    "dec": lambda x: x - 1,
    "dbl": lambda x: x * 2,
    "neg": lambda x: -x,
    "shl": lambda x: x << 1 if x >= 0 else None,
    "shr": lambda x: x >> 1 if x >= 0 else None,
    "sq": lambda x: x * x,
}
PARAM_PRIMS = {
    "add_k": lambda k: (lambda x: x + k),
    "mul_k": lambda k: (lambda x: x * k) if k not in (0,) else None,
    "xor_k": lambda k: (lambda x: x ^ k if x >= 0 else None),
}


def apply_chain(chain, x):
    for name, fn in chain:
        x = fn(x)
        if x is None:
            return None
    return x


def induce(pairs, library, depth=2):
    """Search compositions up to `depth` over primitives + library.
    A program answers only if it reproduces every pair. Returns
    (chain_names, fn) or None."""
    vocab = dict(PRIMS)
    vocab.update(library)
    # parameterized: solve k from the first pair when used alone or
    # as the last step (v1 scope), small integer k
    x0, y0 = pairs[0]

    def candidates():
        for n1, f1 in vocab.items():
            yield [(n1, f1)]
        for pn, maker in PARAM_PRIMS.items():
            for k in range(-9, 10):
                f = maker(k)
                if f:
                    yield [(f"{pn}({k})", f)]
        if depth >= 2:
            names = list(vocab.items())
            for n1, f1 in names:
                for n2, f2 in names:
                    yield [(n1, f1), (n2, f2)]
                for pn, maker in PARAM_PRIMS.items():
                    for k in range(-9, 10):
                        f = maker(k)
                        if f:
                            yield [(n1, f1), (f"{pn}({k})", f)]
                            yield [(f"{pn}({k})", f), (n1, f1)]

    tried = 0
    for chain in candidates():
        tried += 1
        if all(apply_chain(chain, x) == y for x, y in pairs):
            return [n for n, _ in chain], \
                (lambda c: lambda x: apply_chain(c, x))(list(chain)), \
                tried
    return None, None, tried


def make_task(program, n=10, lo=0, hi=40, seed=0):
    rng = random.Random(seed)
    xs = rng.sample(range(lo, hi), n)
    return [(x, program(x)) for x in xs[:6]], \
        [(x, program(x)) for x in xs[6:]]


m = Isaac(fast=True)
library = {}
print("STAGE 1 — the basic operators, hidden programs -> induced "
      "rules\n")
targets = [
    ("increment", lambda x: x + 1),
    ("decrement", lambda x: x - 1),
    ("bit-shift-left", lambda x: x << 1),
    ("bit-shift-right", lambda x: x >> 1),
    ("negate-then-add-3", lambda x: -x + 3),
    ("double-then-inc (secret L1)", lambda x: x * 2 + 1),
    ("times-3-minus-2", lambda x: x * 3 - 2),
]
solved = 0
for name, prog in targets:
    train, held = make_task(prog, seed=hash(name) % 999)
    t0 = time.perf_counter()
    chain, fn, tried = induce(train, library)
    ms = 1000 * (time.perf_counter() - t0)
    if chain and all(fn(x) == y for x, y in held):
        solved += 1
        print(f"  v {name:28s} -> {' then '.join(chain):24s} "
              f"held-out 4/4  ({tried} programs tried, {ms:.0f}ms)")
        if name.startswith("double-then-inc"):
            library["L1"] = fn
            m.fact_add("op_rule", chain, kind="rule",
                       origin="induced",
                       text=f"L1(x) = {' then '.join(chain)}")
    else:
        print(f"  x {name:28s} -> no program survived the court "
              f"({tried} tried, {ms:.0f}ms)")

print("\nSTAGE 2 — THE LIBRARY LESSON: target = L1(L1(x)) = 4x+3, "
      "depth 4 raw (beyond budget 2)")
prog2 = lambda x: 4 * x + 3  # noqa: E731
train2, held2 = make_task(prog2, seed=7)
t0 = time.perf_counter()
c_no, f_no, tried_no = induce(train2, {})
print(f"  without library: "
      f"{'SOLVED ' + ' then '.join(c_no) if c_no else 'refused'} "
      f"({tried_no} tried)")
c_yes, f_yes, tried_yes = induce(train2, library)
ms = 1000 * (time.perf_counter() - t0)
if c_yes and all(f_yes(x) == y for x, y in held2):
    print(f"  WITH library:    SOLVED -> {' then '.join(c_yes)}  "
          f"held-out 4/4  ({tried_yes} tried, {ms:.0f}ms total)")
else:
    print(f"  WITH library:    still refused ({tried_yes} tried)")

print("\nSTAGE 3 — the null: 6 random pairs, no hidden program")
rng = random.Random(3)
noise = [(rng.randrange(40), rng.randrange(200)) for _ in range(6)]
c_n, f_n, tried_n = induce(noise, library)
print(f"  {'REFUSED (correct)' if not c_n else 'FALSE PROGRAM: ' + str(c_n)}"
      f"  ({tried_n} programs tried)")

print("\nSTAGE 4 — operator identities (term-rewriting seed): "
      "extensional check")
tests = list(range(0, 30))
same = all(PRIMS["shl"](x) == PRIMS["dbl"](x) for x in tests)
print(f"  shl(x) == dbl(x) on 0..29: {same} -> "
      f"'bit-shift-left IS doubling' recordable as an identity")

print(f"\ninduced rules in the facts layer: "
      f"{[f['text'] for f in m.facts_query(kind='rule', origin='induced')]}")
print(f"score: {solved}/{len(targets)} stage-1 operators induced")
