"""
COLLECTIVE SIGNALS — enumerate what the nets find when every individual is
weak but the group moves together (owner, 2026-07-04: "a strong significant
collective signal, but a weak individual signal? how do we enumerate that?"
+ "a negative value can be higher than the starting point... darkening vs
brightening" — responses are SIGNED, both directions, always).

  K1  strong collective / weak individuals: y = 3*mean(x0..x7). Each
      column alone is faint; the common mode is loud. interrogate() must
      say so — signed, gated (coherent shift beats sign-scrambled shifts
      AND any single feature) — and MINT mean(x0..x7) as a node.
  K2  DARKENING: y = -2*mean(...). The response must be reported as
      FALLING with the collective (up-shift response negative) — the sign
      is the fact, never the magnitude.
  K3  refusal: y = x0 - x1 + x2 has three drivers but NO common mode
      (mixed signs). A coherent-shift claim would be WRONG; the
      sign-scrambled null must beat it and nothing may be minted.
  K4  REUSE: with mean(x0..x7) minted, the previously-unsayable
      cos(3*mean(...)) becomes UNDERSTOOD directly.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from isaac import Isaac

rng = np.random.default_rng(83)


def line(c="-", n=70):
    print(c * n)


# ═══ K1: the loud common mode of faint individuals ═══
line("=")
print("K1 — y = 3*mean(x0..x7): weak alone, strong together")
line("=")
isaac = Isaac()
n = 900
X = rng.normal(0, 1, (n, 8))
y = 3.0 * X.mean(1) + rng.normal(0, 0.15, n)
cap = isaac.capture_net("k1", X, y)
h = isaac.interrogate("k1")
for s_ in h["english"]:
    print(f"    - {s_}")
col = h["collective"]
k1 = (col is not None and col["up"] > 0 and col["down"] < 0
      and col["ratio"] >= 2.0
      and any(c["op"] == "mean" for c in isaac.composites))
print(f"  minted: {[c['name'] for c in isaac.composites]}")

# ═══ K2: darkening — the sign IS the fact ═══
line("=")
print("K2 — y = -2*mean(...): the response FALLS as the collective rises")
line("=")
isaac2 = Isaac()
y2 = -2.0 * X.mean(1) + rng.normal(0, 0.1, n)
isaac2.capture_net("k2", X, y2)
h2 = isaac2.interrogate("k2")
col2 = h2["collective"]
if col2:
    print(f"    coherent up-shift response: {col2['up']:+.2f}  "
          f"(darkening); down-shift: {col2['down']:+.2f} (brightening)")
k2 = col2 is not None and col2["up"] < 0 and col2["down"] > 0

# ═══ K3: three drivers, NO common mode — must refuse ═══
line("=")
print("K3 — y = x0 - x1 + x2: drivers yes, collective NO (mixed signs)")
line("=")
isaac3 = Isaac()
X3 = rng.normal(0, 1, (n, 3))
y3 = X3[:, 0] - X3[:, 1] + X3[:, 2] + rng.normal(0, 0.05, n)
isaac3.capture_net("k3", X3, y3)
h3 = isaac3.interrogate("k3")
print(f"    collective claim: "
      f"{'NONE (correct refusal)' if h3['collective'] is None else 'CLAIMED - WRONG'}")
k3 = h3["collective"] is None and not any(
    c["op"] == "mean" for c in isaac3.composites)

# ═══ K4: the minted collective is SPENT on a new unsayable ═══
line("=")
print("K4 — reuse: cos(3*mean(x0..x7)), cold vs with the learned collective")
line("=")
Xc = rng.normal(0, 1, (1200, 8))
yc = np.cos(3.0 * Xc.mean(1)) + rng.normal(0, 0.03, 1200)
cold = Isaac().discover(Xc, yc, name="cold")
print(f"    cold engine: {cold['verdict']} (R2 {cold['r2']:.2f})")
warm = isaac.discover(Xc, yc, name="warm")     # k1's isaac owns mean(...)
print(f"    with the collective: {warm['verdict']} (R2 {warm['r2']:.3f})")
print(f"    equation: {warm['equation'][:70]}")
k4 = (cold["verdict"] != "UNDERSTOOD" and warm["verdict"] == "UNDERSTOOD"
      and "mean(" in warm["equation"])

line("=")
print(f"K1 collective found, signed, minted   : {'PASS' if k1 else 'FAIL'}")
print(f"K2 darkening reported as darkening    : {'PASS' if k2 else 'FAIL'}")
print(f"K3 mixed signs refused                : {'PASS' if k3 else 'FAIL'}")
print(f"K4 collective reused on a new problem : {'PASS' if k4 else 'FAIL'}")
ok = k1 and k2 and k3 and k4
print(f"VERDICT: {'WORKS — the common mode is enumerable, signed, and reusable' if ok else 'SPEC NOT MET'}")
line("=")
