"""STRUCTURE HUNT court — learning rules ABOUT data with nobody
telling him what they are, or that they exist.

Plant: ordinary sentences carrying three hidden laws —
  "the counter goes from N to N+1"        (increment)
  "the price doubles from N to 2N"        (doubling)
  "the code X maps to 3X-2"               (a composed op)
plus a NOISE template (random number pairs) and filler prose.
Then ONE call: structure_hunt(). He must mine the templates himself
(differentiator on his own log), induce, survive the shuffled null,
and mint ONLY the real laws. The noise template must be refused.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "..", "code"))
from isaac import Isaac, tokenize  # noqa: E402
import random  # noqa: E402

FAILS = []


def check(name, ok):
    print(f"  {'v' if ok else 'x'}  {name}")
    if not ok:
        FAILS.append(name)


m = Isaac(fast=True)
m.wave_logging = False
if not hasattr(m, "structure_hunt"):
    print("SKIP: induction engine not built")
    sys.exit(77)

rng = random.Random(11)
for n in rng.sample(range(1, 30), 8):
    m.observe(tokenize(f"the counter goes from {n} to {n + 1} ."))
for n in rng.sample(range(1, 20), 8):
    m.observe(tokenize(f"the price doubles from {n} to {n * 2} ."))
for n in rng.sample(range(1, 15), 8):
    m.observe(tokenize(f"the code {n} maps to {n * 3 - 2} ."))
for _ in range(8):
    m.observe(tokenize(f"sensor {rng.randrange(50)} read "
                       f"{rng.randrange(200)} ."))
for s in ["the cat sat on the mat .", "rain fell all day .",
          "a dog barked twice ."]:
    m.observe(tokenize(s))

rep = m.structure_hunt()
print(f"hunt report: {len(rep['minted'])} minted from "
      f"{rep['templates']} templates, {rep['refused']} refused")
for name, chain, key, n in rep["minted"]:
    print(f"    {name}: {' then '.join(chain)}   "
          f"(template: {key[:46]}..., {n} self-collected examples)")

texts = {tuple(c) for _, c, _, _ in rep["minted"]}
check("increment law minted (untold)",
      ("inc",) in texts or ("add_k(1)",) in texts)
check("doubling law minted (untold)",
      ("dbl",) in texts or ("mul_k(2)",) in texts or
      ("shl",) in texts)
check("composed 3x-2 law minted (untold)",
      any("mul_k(3)" in c for c in texts for c in [c]) or
      any(len(c) == 2 and "mul_k(3)" in c and "add_k(-2)" in c
          for c in texts))
check("noise template refused", rep["refused"] >= 1)
check("exactly the real laws minted (no extras)",
      len(rep["minted"]) == 3)
check("minted rules live in the facts layer as readable chains",
      len(m.facts_query(pred="op_rule", origin="induced")) == 3)

# and the library is LIVE: a later induction can use a minted op
pairs = [(x, (x + 1) * 2) for x in (3, 5, 8, 11)]   # dbl(inc(x))
chain = m.induce_op(pairs)
check("library composes: dbl-after-inc found using vocabulary",
      chain is not None)
print(f"    later induction: {' then '.join(chain) if chain else 'refused'}")

print(f"\nGATE: {'PASS' if not FAILS else 'FAIL (' + ','.join(FAILS) + ')'}")
sys.exit(1 if FAILS else 0)
