"""
COMBINATIONS ARE THINGS — memorized and REUSED (owner, 2026-07-04:
"x0,x1 in this relationship... should have a node... enumerate and then
use that... it's combinatorial. it should be able to memorize and reuse
those combinations. a topological venn diagram... dimensionless.")

  R1  REUSE, same session: Isaac learns the product-combination from ONE
      problem (sin(3*x0*x1), via capture -> interrogation, which MINTS
      comb:(x1*x0)). A DIFFERENT previously-unsayable problem arrives —
      sin(3*x0*x1) + 0.5*x2 — and discover() now solves it DIRECTLY,
      because the learned combination is a first-class column every
      future discovery draws on.
  R2  REUSE, across sessions: the combination rides the ledger. A fresh
      Isaac loads the ledger and solves the new problem cold.
  R3  DISTINCTNESS: (x0*x1), (x0+x1), (x1*x2) are three different THINGS
      — separate nodes, separate provenance. ab is not a and b.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from isaac import Isaac

rng = np.random.default_rng(71)
LEDGER = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "runs", "2026-07-03", "reuse_ledger.jsonl")
if os.path.exists(LEDGER):
    os.remove(LEDGER)


def line(c="-", n=70):
    print(c * n)


def new_challenge(n=1200):
    # THE canonical unsayable: sin(3*x0*x1) (+ a plain term) — PARTIAL
    # forever in raw coordinates (engine self-test case (d)). NORMAL
    # inputs, like the self-test: the product's tails are where
    # surrogate clouds die
    X = rng.normal(0, 1, (n, 3))
    y = np.sin(3.0 * X[:, 0] * X[:, 1]) + 0.5 * X[:, 2] \
        + rng.normal(0, 0.03, n)
    return X, y


# ═══ R0: baseline — the new challenge IS unsayable without the combination
line("=")
print("R0 — control: sin(3*x0*x1) + 0.5*x2 WITHOUT the learned combination")
line("=")
isaac0 = Isaac()
Xc, yc = new_challenge()
r0 = isaac0.discover(Xc, yc, name="cold")
print(f"  verdict: {r0['verdict']} (R2 {r0['r2']:.2f}) — "
      f"{'unsayable, as expected' if r0['verdict'] != 'UNDERSTOOD' else 'unexpectedly solved!'}")
r0_ok = r0["verdict"] != "UNDERSTOOD"

# ═══ R1: learn the combination on problem A, spend it on problem B ═══
line("=")
print("R1 — learn the combination on an EASY product problem; spend it on the canonical stuck one")
line("=")
isaac = Isaac()
isaac.ledger_path = LEDGER
n = 700
Xa = rng.normal(0, 1, (n, 3))
z_ = Xa[:, 0] * Xa[:, 1]                          # an EASY lesson: a
ya = z_ ** 2 - 0.5 * z_ + rng.normal(0, 0.03, n)  # smooth bowl in the product
isaac.capture_net("lesson", Xa, ya)
isaac.interrogate("lesson")                      # mints comb:(xi*xj)
combs = [c["name"] for c in isaac.composites]
print(f"  combinations now owned: {combs}")
r1 = isaac.discover(Xc, yc, name="reuse")
print(f"  new challenge: {r1['verdict']} (R2 {r1['r2']:.3f})")
print(f"  equation: {r1['equation'][:70]}")
Xf, yf = new_challenge(400)
yp = isaac.apply_law("reuse", Xf)
r2f = 1 - float(np.sum((yf - yp) ** 2)) / float(np.sum((yf - yf.mean()) ** 2))
print(f"  applied to fresh raw data: R2 {r2f:.3f}")
r1_ok = (bool(combs) and r1["verdict"] == "UNDERSTOOD" and r2f >= 0.95
         and ("(x0*x1)" in r1["equation"] or "(x1*x0)" in r1["equation"]))

# ═══ R2: the combination survives the session boundary ═══
line("=")
print("R2 — a fresh Isaac inherits the combination through the ledger")
line("=")
isaac2 = Isaac()
info = isaac2.load_ledger(LEDGER)
print(f"  ledger loaded: {info['records']} records; combinations "
      f"inherited: {[c['name'] for c in isaac2.composites]}")
r2r = isaac2.discover(Xc, yc, name="inherited")
print(f"  new challenge, cold engine + inherited combination: "
      f"{r2r['verdict']} (R2 {r2r['r2']:.3f})")
print(f"  equation: {r2r['equation'][:70]}")
r2_ok = bool(isaac2.composites) and r2r["verdict"] == "UNDERSTOOD"

# ═══ R3: distinct combinations are distinct THINGS ═══
line("=")
print("R3 — ab is not a and b: three combinations, three nodes")
line("=")
isaac.register_composite("sum", [0, 1], provenance="R3 demo")
isaac.register_composite("product", [1, 2], provenance="R3 demo")
nodes = [n_ for n_ in isaac.net.all_nodes()
         if str(n_).startswith("comb:")]
print(f"  combination nodes: {sorted(nodes)}")
provs = {c["name"]: c["provenance"] for c in isaac.composites}
for nm, pv in provs.items():
    print(f"    {nm}: from {pv}")
r3_ok = len(nodes) >= 3 and len(set(nodes)) == len(nodes)

line("=")
print(f"R0 unsayable without the combination : {'PASS' if r0_ok else 'FAIL'}")
print(f"R1 learned once, spent elsewhere     : {'PASS' if r1_ok else 'FAIL'}")
print(f"R2 inherited across sessions         : {'PASS' if r2_ok else 'FAIL'}")
print(f"R3 combinations are distinct things  : {'PASS' if r3_ok else 'FAIL'}")
ok = r0_ok and r1_ok and r2_ok and r3_ok
print(f"VERDICT: {'WORKS — the vocabulary grows with experience' if ok else 'SPEC NOT MET'}")
line("=")
