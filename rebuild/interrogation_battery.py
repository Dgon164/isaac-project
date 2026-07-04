"""
INTERROGATION BATTERY — make the captured explicit (owner, 2026-07-04:
"there is a correlation that it is detecting. how do we enumerate that and
make it explicit... even if they aren't specifically correct, they can at
least point in the direction to say this is a pattern as a deliverable.")

  I1  the stuck case, unstuck: sin(3*x0*x1) with a bystander column.
      Captured (was: honestly unsayable). interrogate() must deliver the
      pattern in English — drivers, joint action, dependence THROUGH THE
      PRODUCT, periodic along it, frequency ~3 — each claim past its null.
      Then graduate_composite(): re-discover in the composite coordinate
      -> the law, exact, in a coordinate Isaac chose himself.
  I2  no false structure: an additive function must earn NO interaction
      claim and NO composite claim.
  I3  a different composite: (x0+x1)^2 -> the SUM, then graduated exactly.
"""
import sys

import numpy as np

import os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from isaac import Isaac

rng = np.random.default_rng(61)


def line(c="-", n=70):
    print(c * n)


# ═══ I1: the stuck case becomes a deliverable, then a law ═══
line("=")
print("I1 — sin(3*x0*x1) + bystander: enumerate the pattern, then say it")
line("=")
isaac = Isaac()
n = 700
X = rng.uniform(-1.5, 1.5, (n, 3))                # x2 = bystander
y = np.sin(3.0 * X[:, 0] * X[:, 1]) + rng.normal(0, 0.03, n)
cap = isaac.capture_net("i1", X, y)
print(f"  capture: {cap['status']} (R2 {cap['r2']:.3f} vs null "
      f"{cap['null']:.3f})")
h = isaac.interrogate("i1")
print("  THE DELIVERABLE (English, each claim gated):")
for s in h["english"]:
    print(f"    - {s}")
drv_ok = h["drivers"][0] > 0.2 and h["drivers"][1] > 0.2 \
    and h["drivers"][2] < 0.1
int_ok = any(v >= 0.1 for v in h["interactions"].values())
comp = [c for c in h["composites"] if c["through"] == "product"
        and set(c["features"]) == {0, 1}]
comp_ok = bool(comp)
freq_ok = comp and comp[0]["shape"] == "periodic" \
    and comp[0]["freq_estimate"] and 2.0 <= comp[0]["freq_estimate"] <= 4.5
grad = isaac.graduate_composite("i1", X, y)
print(f"  graduate via composite: {grad['status']}"
      f"  -> {grad.get('equation', '—')}")
g_ok = grad["status"].startswith("GRADUATED") and grad["r2"] >= 0.95 \
    and ("(x0*x1)" in grad["equation"] or "(x1*x0)" in grad["equation"])
i1 = drv_ok and int_ok and comp_ok and freq_ok and g_ok

# ═══ I2: no false structure on an additive function ═══
line("=")
print("I2 — additive control (x0^2 + x1): no joint claim may be invented")
line("=")
isaac = Isaac()
X = rng.uniform(-1.5, 1.5, (700, 3))
y = X[:, 0] ** 2 + X[:, 1] + rng.normal(0, 0.03, 700)
cap = isaac.capture_net("i2", X, y)
h = isaac.interrogate("i2")
for s in h["english"]:
    print(f"    - {s}")
false_int = any(v >= 0.1 for v in h["interactions"].values())
false_comp = bool(h["composites"])
print(f"  false interaction claimed: {'YES' if false_int else 'NO'};  "
      f"false composite claimed: {'YES' if false_comp else 'NO'}")
i2 = not false_int and not false_comp

# ═══ I3: a different composite — the SUM ═══
line("=")
print("I3 — (x0+x1)^2: the dependence flows through the SUM")
line("=")
isaac = Isaac()
X = rng.uniform(-1.5, 1.5, (700, 2))
y = (X[:, 0] + X[:, 1]) ** 2 + rng.normal(0, 0.03, 700)
cap = isaac.capture_net("i3", X, y)
h = isaac.interrogate("i3")
for s in h["english"]:
    print(f"    - {s}")
comp3 = [c for c in h["composites"] if c["through"] == "sum"]
grad3 = isaac.graduate_composite("i3", X, y) if comp3 else None
if grad3:
    print(f"  graduate via composite: {grad3['status']}"
          f"  -> {grad3.get('equation', '—')}")
i3 = bool(comp3) and grad3 and grad3["status"].startswith("GRADUATED") \
    and grad3["r2"] >= 0.95

line("=")
print(f"I1 stuck case -> deliverable -> exact law : {'PASS' if i1 else 'FAIL'}")
print(f"I2 no invented structure                  : {'PASS' if i2 else 'FAIL'}")
print(f"I3 sum-composite found and graduated      : {'PASS' if i3 else 'FAIL'}")
print(f"VERDICT: {'WORKS — the captured is enumerable, and pointing at the pattern can BECOME the law' if (i1 and i2 and i3) else 'SPEC NOT MET'}")
line("=")
