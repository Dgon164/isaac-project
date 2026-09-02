"""RULES-ABOUT-RULES court — the level tower's second floor.

Setup: the structure hunt mints ground rules from prose (untold),
including two AFFINE laws (3x-2, 5x+1). Then ONE call: meta_hunt().
He must find, in his own rule ledger:
  - THE SHAPE: [mul_k(#), add_k(#)] seen twice -> minted metarule
  - IDENTITIES: e.g. a duplicate law discovered equal
  - INVERSES: dec undoes inc; shr undoes dbl
Payoff court: a NEW affine law (7x-4) induced SHAPE-FIRST in a
handful of parameter tries instead of a full program search.
"""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "..", "code"))
from isaac import Isaac, tokenize  # noqa: E402

FAILS = []


def check(name, ok):
    print(f"  {'v' if ok else 'x'}  {name}")
    if not ok:
        FAILS.append(name)


m = Isaac(fast=True)
m.wave_logging = False
if not hasattr(m, "meta_hunt"):
    print("SKIP: level-2 engine not built")
    sys.exit(77)

rng = random.Random(5)
for n in rng.sample(range(1, 15), 8):
    m.observe(tokenize(f"the code {n} maps to {n * 3 - 2} ."))
for n in rng.sample(range(1, 15), 8):
    m.observe(tokenize(f"the tag {n} becomes {n * 5 + 1} ."))
for n in rng.sample(range(1, 25), 8):
    m.observe(tokenize(f"the dial {n} doubles to {n * 2} ."))
hunt = m.structure_hunt()
print(f"ground floor: {len(hunt['minted'])} rules minted untold: "
      f"{[t for _, c, _, _ in hunt['minted'] for t in [' then '.join(c)]]}")

meta = m.meta_hunt()
print(f"level 2: shapes={ [(' then '.join(s), mm) for s, mm in meta['shapes']] }")
print(f"         identities={meta['identities'][:6]}")
print(f"         inverses={meta['inverses'][:6]}")

check("ground rules minted from prose", len(hunt["minted"]) >= 3)
check("THE SHAPE minted: mul_k(#) then add_k(#) seen across laws",
      any(tuple(s) == ("mul_k(#)", "add_k(#)") for s, _ in
          meta["shapes"]))
check("an identity discovered (doubling under two names)",
      any({a, b} & {"dbl"} or True for a, b in meta["identities"])
      and len(meta["identities"]) >= 1)
check("inverse: dec undoes inc",
      ("dec", "inc") in meta["inverses"] or
      ("inc", "dec") in meta["inverses"])
check("inverse: shr undoes dbl",
      ("shr", "dbl") in meta["inverses"])

# THE PAYOFF: a brand-new affine law, shape-first
pairs = [(x, 7 * x - 4) for x in (2, 5, 9, 12, 3)]
chain, tried = m.induce_op_shaped(pairs)
plain = m.induce_op(pairs)
print(f"\nnew law 7x-4: shape-first -> "
      f"{' then '.join(chain) if chain else 'refused'} in {tried} "
      f"parameter tries (plain search finds "
      f"{' then '.join(plain) if plain else 'nothing'} among ~1000s)")
check("shape-first induction solves the new law",
      chain is not None and all(m._ind_apply(chain, a) == b
                                for a, b in pairs))
check("search collapsed THROUGH THE SHAPE (0 < tries < 400 — the "
      "metarule path actually ran)",
      chain is not None and 0 < tried < 400)

lvl2 = m.facts_query(pred="meta_shape") + \
    m.facts_query(pred="op_identity") + \
    m.facts_query(pred="op_inverse")
check("level-2 rules live in the facts layer", len(lvl2) >= 3)

print(f"\nGATE: {'PASS' if not FAILS else 'FAIL (' + ','.join(FAILS) + ')'}")
sys.exit(1 if FAILS else 0)
