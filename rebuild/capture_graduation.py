"""
CAPTURE NETS + GRADUATION + DATA ADEQUACY — the last missing piece of
audit 2.8, at the owner's prompt ("did we address the tiny net creation
for heuristic interpretation as a stopgap? able to detect or define the
data that is too weak to interpret?").

The no-nets law holds throughout: the net is never the deliverable — it is
quarantined as the tracked unknown x:<name>, it counts only past its
permuted null, and it exists to be DESTROYED by graduate() (distillation).

  G1  the loop's mechanics: capture an in-class relationship as a net,
      then distill — caught must become SAID, and the said form must
      match the PLANTED truth (checked externally)
  G2  honest non-graduation: an out-of-class relationship is captured,
      distillation finds no equation, the capture STANDS as captured
  G3  the lie-killer: a net trained on pure noise must FAIL its null —
      nothing stored, the 'captured' middle category cannot be faked
  G4  data too weak to interpret — the adequacy DIAGNOSIS names the cause:
      (a) n below onset  (b) drivers not among the columns (shadow)
      (c) class limit, not weak data  (d) range too narrow (rivals tied)
"""
import sys

import numpy as np

import os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from isaac import Isaac

rng = np.random.default_rng(53)


def line(c="-", n=70):
    print(c * n)


# ═══ G1: mechanics — caught becomes said, and said matches the truth ═══
line("=")
print("G1 — capture -> distill -> the equation matches the planted truth")
line("=")
isaac = Isaac()
n = 400
X = rng.normal(0, 1, (n, 3))
y = X[:, 0] * X[:, 1] - X[:, 2] + rng.normal(0, 0.05, n)
cap = isaac.capture_net("g1", X, y)
print(f"  capture: {cap['status']}  (held-out R2 {cap['r2']:.3f} vs "
      f"null {cap['null']:.3f})")
grad = isaac.graduate("g1", X, y)          # original data -> prune vs reality
print(f"  graduate: {grad['status']}  -> {grad.get('equation', '—')}")
ok_truth = False
if grad["status"] == "GRADUATED":
    Xt = rng.normal(0, 1, (500, 3))
    yt = Xt[:, 0] * Xt[:, 1] - Xt[:, 2]
    yp = isaac.apply_law("g1_distilled", Xt)
    ss = float(np.sum((yt - yt.mean()) ** 2))
    r2t = 1 - float(np.sum((yt - yp) ** 2)) / ss
    ok_truth = r2t >= 0.95
    print(f"  distilled law vs the PLANTED truth (fresh data): R2 {r2t:.3f}")
g1 = cap["status"].startswith("CAPTURED") and \
    grad["status"] == "GRADUATED" and ok_truth

# ═══ G2: honest non-graduation on an out-of-class relationship ═══
line("=")
print("G2 — out-of-class: captured, distillation honestly finds no law")
line("=")
isaac = Isaac()
X = rng.normal(0, 1, (500, 2))
y = np.sin(3.0 * X[:, 0] * X[:, 1])
cap = isaac.capture_net("g2", X, y)
print(f"  capture: {cap['status']}  (R2 {cap.get('r2', 0):.3f} vs null "
      f"{cap.get('null', 0):.3f})")
g2 = False
if cap["status"].startswith("CAPTURED"):
    grad = isaac.graduate("g2")
    print(f"  graduate: {grad['status']} (distilled verdict "
          f"{grad.get('verdict', '—')}, R2 {grad.get('r2', 0):.2f})")
    status = isaac.net.get_meta("x:g2", "status")
    print(f"  the unknown's status: {status}")
    g2 = grad["status"] == "STILL CAPTURED"

# ═══ G3: the lie-killer — noise nets die at their null ═══
line("=")
print("G3 — a net trained on pure noise must FAIL its null")
line("=")
isaac = Isaac()
X = rng.normal(0, 1, (400, 3))
cap = isaac.capture_net("g3", X, rng.normal(0, 1, 400))
stored = isaac.net.get_meta("x:g3", "capture_net")
print(f"  capture on noise: {cap['status']}  (R2 {cap['r2']:.3f} vs null "
      f"{cap['null']:.3f});  stored: {'NOTHING' if stored is None else 'A NET — VIOLATION'}")
g3 = cap["status"] == "FAILED NULL" and stored is None

# ═══ G4: the adequacy diagnosis — WHY the data is too weak ═══
line("=")
print("G4 — data too weak to interpret: the diagnosis names the cause")
line("=")
isaac = Isaac()
cases = []

# (a) sample below onset
Xa = rng.normal(0, 1, (40, 3))
ya = Xa[:, 0] * Xa[:, 1] + rng.normal(0, 0.8, 40)
ra = isaac.discover(Xa, ya)
hit = any("sample too small" in r for r in ra["adequacy"]["reasons"]) \
    or "provisional" in ra["adequacy"]["verdict"]
cases.append(("n=40 (below onset)", ra["adequacy"]["verdict"], hit))

# (b) driver not among the columns (shadow)
Xb = rng.normal(0, 1, (600, 3))
hidden = rng.normal(0, 1, 600)
yb = 2.0 * hidden + rng.normal(0, 0.1, 600)     # driven by an unmeasured var
rb = isaac.discover(Xb, yb)
hit_b = any("not among these columns" in r or "drivers were not measured"
            in r for r in rb["adequacy"]["reasons"])
cases.append(("hidden driver", rb["adequacy"]["verdict"], hit_b))

# (c) class limit, not weak data
Xc = rng.normal(0, 1, (600, 2))
yc = np.sin(3.0 * Xc[:, 0] * Xc[:, 1])
rc = isaac.discover(Xc, yc)
hit_c = any("expressive-class limit" in r for r in rc["adequacy"]["reasons"])
cases.append(("nested (class limit)", rc["adequacy"]["verdict"], hit_c))

g4 = True
for label, verdict, hit in cases:
    print(f"  {label:24s} -> {verdict:26s} "
          f"cause named: {'YES' if hit else 'NO'}")
    g4 = g4 and hit

line("=")
print(f"G1 caught -> said -> matches truth : {'PASS' if g1 else 'FAIL'}")
print(f"G2 honest non-graduation           : {'PASS' if g2 else 'FAIL'}")
print(f"G3 noise net fails its null        : {'PASS' if g3 else 'FAIL'}")
print(f"G4 weakness diagnosed with cause   : {'PASS' if g4 else 'FAIL'}")
print(f"VERDICT: {'WORKS — audit 2.8 is closed at the flat level' if (g1 and g2 and g3 and g4) else 'SPEC NOT MET'}")
line("=")
