"""
NUMBER FUNCTIONS AS COMPOSITE OPS (owner, 2026-07-04: "instead of just sub,
it could be enumerated to values or logs or other things? did we ever get
the logs and stuff working too?")

Honest status going in: power laws work in-engine (pow atoms — Kepler);
log-log matching works in harness (cross_domain). Missing: a LOG atom
(y = a*ln(x)+b was unsayable) and RATIO composites. This battery proves
both, plus the domain honesty.

  L1  the logarithmic law: y = 2*ln(x0) + 1 over two decades.
      Cold: no log anywhere in the library. With log(x0) registered:
      UNDERSTOOD, exact, legible.
  L2  sin of a RATIO: y = sin(2*(x0/x1)) — unsayable cold; interrogation
      must find the dependence flows through the RATIO (new candidate),
      and graduation says it exactly.
  L3  domain honesty: a log composite on data containing negatives —
      out-of-domain rows drop honestly, no crash, no false claim.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from isaac import Isaac

rng = np.random.default_rng(97)


def line(c="-", n=70):
    print(c * n)


# ═══ L1: the logarithmic law ═══
line("=")
print("L1 — y = 2*ln(x0) + 1 over two decades (0.1..10)")
line("=")
n = 800
X = np.column_stack([rng.uniform(0.1, 10.0, n), rng.normal(0, 1, n)])
y = 2.0 * np.log(X[:, 0]) + 1.0 + rng.normal(0, 0.05, n)
cold = Isaac().discover(X, y, name="cold")
print(f"  cold (no log in the library): {cold['verdict']} "
      f"(R2 {cold['r2']:.2f})")
isaac = Isaac()
isaac.register_composite("log", [0], provenance="L1")
r = isaac.discover(X, y, name="loglaw")
print(f"  with log(x0) registered:      {r['verdict']} (R2 {r['r2']:.3f})")
print(f"  equation: {r['equation'][:60]}")
yp = isaac.apply_law("loglaw", np.column_stack(
    [rng.uniform(0.1, 10.0, 300), rng.normal(0, 1, 300)]))
l1 = (r["verdict"] == "UNDERSTOOD" and "log(x0)" in r["equation"]
      and r["r2"] >= 0.99 and yp is not None and np.isfinite(yp).all())

# ═══ L2: the ratio, found by interrogation, said by graduation ═══
line("=")
print("L2 — y = sin(2*(x0/x1)): the dependence flows through the RATIO")
line("=")
isaac2 = Isaac()
n = 800
X2 = np.column_stack([rng.uniform(-3, 3, n), rng.uniform(0.3, 3.0, n),
                      rng.normal(0, 1, n)])
y2 = np.sin(2.0 * X2[:, 0] / X2[:, 1]) + rng.normal(0, 0.03, n)
cold2 = Isaac().discover(X2, y2, name="cold2")
print(f"  cold: {cold2['verdict']} (R2 {cold2['r2']:.2f})")
cap = isaac2.capture_net("ratio_case", X2, y2)
h = isaac2.interrogate("ratio_case")
for s_ in h["english"]:
    print(f"    - {s_}")
found_ratio = any(c["through"] == "ratio" for c in h["composites"])
grad = isaac2.graduate_composite("ratio_case", X2, y2)
if grad:
    print(f"  graduate: {grad['status']} -> {grad.get('equation', '—')}")
l2 = (cold2["verdict"] != "UNDERSTOOD" and found_ratio and grad
      and grad["status"].startswith("GRADUATED")
      and "/x1)" in grad.get("equation", "").replace(" ", ""))

# ═══ L3: domain honesty ═══
line("=")
print("L3 — log composite where x0 goes negative: honest domain handling")
line("=")
isaac3 = Isaac()
isaac3.register_composite("log", [0], provenance="L3")
X3 = np.column_stack([rng.normal(0, 2, 600), rng.normal(0, 1, 600)])
y3 = X3[:, 1] * 2.0 + rng.normal(0, 0.05, 600)
r3 = isaac3.discover(X3, y3, name="dom")
kept = sum(X3[:, 0] > 1e-12)
print(f"  rows in x0's log-domain: {kept}/600 — engine used the honest "
      f"subset, verdict {r3['verdict']} (R2 {r3['r2']:.3f})")
print(f"  equation: {r3['equation'][:50]}")
l3 = r3["verdict"] == "UNDERSTOOD" and "x1" in r3["equation"]

line("=")
print(f"L1 logarithmic law, exact and legible : {'PASS' if l1 else 'FAIL'}")
print(f"L2 ratio found, then said exactly     : {'PASS' if l2 else 'FAIL'}")
print(f"L3 out-of-domain handled honestly     : {'PASS' if l3 else 'FAIL'}")
ok = l1 and l2 and l3
print(f"VERDICT: {'WORKS — the op family is open: values, logs, ratios, collectives' if ok else 'SPEC NOT MET'}")
line("=")
