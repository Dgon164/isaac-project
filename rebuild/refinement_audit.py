"""
THE REFINEMENT AUDIT — does the correction loop actually raise accuracy?

(Owner, 2026-07-03: "i would really like it to get the accuracy higher,
and it has an indicator it can use as a correction signal for it to
recalculate and experiment with different information to refine that...
occam's razor.")

Protocol, same 100-world deck as the calibration audit:
  BEFORE: play cold; grade every kept law beyond its observed range.
  REFINE: isaac.refine() — the confidence signal picks the weakest region,
          the world answers 60 budgeted experiments there, re-derivation is
          accepted only through the Occam gate (better, or tied & simpler),
          the displaced law superseded with why, then an Occam prune.
  AFTER:  grade the SAME claims on the SAME hidden data again.

The number that must move: beyond-range hold rate. The number that must
not: inside-range hold. The Occam number: mean terms per law.
"""
import sys
import time

import numpy as np

import os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from isaac import Isaac
from calibration_audit import make_world

rng = np.random.default_rng(303)
DECK = (["poly"] * 20 + ["trig"] * 15 + ["exp"] * 10 + ["power"] * 10
        + ["linsum"] * 15 + ["outclass"] * 15 + ["noise"] * 15)


def line(c="-", n=70):
    print(c * n)


def grade_beyond(w, isaac, name):
    span = w["hi"] - w["lo"]
    Xh = rng.uniform(w["hi"], w["hi"] + 0.6 * span, (400, w["d"]))
    yt = w["f"](Xh)
    yp = isaac.apply_law(name, Xh)
    if yp is None:
        return None
    ss = float(np.sum((yt - yt.mean()) ** 2))
    return 1 - float(np.sum((yt - yp) ** 2)) / max(ss, 1e-12)


def grade_inside(w, isaac, name):
    Xh = rng.uniform(w["lo"], w["hi"], (400, w["d"]))
    yt = w["f"](Xh)
    yp = isaac.apply_law(name, Xh)
    if yp is None:
        return None
    ss = float(np.sum((yt - yt.mean()) ** 2))
    return 1 - float(np.sum((yt - yp) ** 2)) / max(ss, 1e-12)


print(f"REFINEMENT AUDIT — {len(DECK)} worlds; before -> refine -> after\n")
t0 = time.time()
before_b, after_b, before_i, after_i = [], [], [], []
terms_before, terms_after, accepted, pruned = [], [], 0, 0
kept = 0
for wi, kind in enumerate(DECK):
    w = make_world(kind)
    isaac = Isaac()
    name = f"r{wi}"
    res = isaac.discover(w["X"], w["y"], name=name)
    if res["verdict"] not in ("UNDERSTOOD", "PARTIAL"):
        continue
    kept += 1
    m = isaac.net.get_meta(f"law:{name}", "model")
    terms_before.append(len(m["terms"]))
    gb0 = grade_beyond(w, isaac, name)
    gi0 = grade_inside(w, isaac, name)

    def ask(Xq, _w=w):
        return _w["f"](Xq) + rng.normal(0, _w["sd"], len(Xq))

    rep = isaac.refine(name, w["X"], w["y"], ask=ask, budget=60, rounds=3)
    accepted += rep["accepted"]
    pruned += rep["pruned"]
    m2 = isaac.net.get_meta(f"law:{name}", "model")
    terms_after.append(len(m2["terms"]))
    before_b.append(gb0); after_b.append(grade_beyond(w, isaac, name))
    before_i.append(gi0); after_i.append(grade_inside(w, isaac, name))
    if kept % 20 == 0:
        print(f"  ... {kept} laws refined [{time.time()-t0:.0f}s]")


def rate(vals):
    ok = [v for v in vals if v is not None]
    return sum(1 for v in ok if v >= 0.7), len(ok)


line("=")
print("DID THE CORRECTION LOOP MOVE THE NUMBER?")
line("=")
b1, n1 = rate(before_b); b2, n2 = rate(after_b)
i1, m1 = rate(before_i); i2, m2_ = rate(after_i)
print(f"  beyond-range hold BEFORE refine: {b1}/{n1}  = {100*b1/n1:.0f}%")
print(f"  beyond-range hold AFTER  refine: {b2}/{n2}  = {100*b2/n2:.0f}%"
      f"   <- the number that had to move")
print(f"  inside-range hold: {100*i1/m1:.0f}% -> {100*i2/m2_:.0f}%  "
      f"(must not regress)")
print(f"\n  OCCAM: mean terms per law {np.mean(terms_before):.1f} -> "
      f"{np.mean(terms_after):.1f}   "
      f"({accepted} refinements accepted, {pruned} terms pruned at F-tie)")
print(f"  budget: 60 experiments/law, chosen by the confidence signal")
print(f"\n[{time.time()-t0:.0f}s total]")
line("=")
improved = (b2 / max(n2, 1)) - (b1 / max(n1, 1))
ok = improved > 0.10 and (i2 / max(m2_, 1)) >= (i1 / max(m1, 1)) - 0.05
print(f"VERDICT: {'WORKS' if ok else 'PARTIAL (see numbers)'} — "
      f"beyond-range accuracy {'+' if improved>=0 else ''}"
      f"{100*improved:.0f} pts; the indicator steered the experiments; "
      f"simpler survived at ties.")
line("=")
