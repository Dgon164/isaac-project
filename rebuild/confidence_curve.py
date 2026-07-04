"""
EXTRAPOLATED CONFIDENCE — measure the decay curve, then validate it.
(Owner's design, 2026-07-03: "maybe just a boundary confidence? what about
extrapolated confidence?" — the binary form-true stamp becomes graded,
measured belief.)

Two halves, no circularity:
  CALIBRATE (60 worlds): play cold, grade every kept law on hidden data at
    hull-exceedance bands delta = 0.1 / 0.3 / 0.6 / 1.0 spans beyond the
    observed range -> the measured survival curve of extrapolating claims.
  VALIDATE (60 FRESH worlds): law_confidence() predicts per-point belief
    using that curve; reliability check — group predictions into bins and
    compare predicted confidence against the actual hold rate. Also
    scored against the flat one-number baseline (the audit's 68%).
"""
import sys
import time

import numpy as np

import os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from isaac import Isaac
from calibration_audit import make_world

rng = np.random.default_rng(202)
BANDS = [0.1, 0.3, 0.6, 1.0]
KINDS = (["poly"] * 12 + ["trig"] * 10 + ["exp"] * 7 + ["power"] * 7
         + ["linsum"] * 9 + ["outclass"] * 8 + ["noise"] * 7)


def line(c="-", n=70):
    print(c * n)


def band_points(w, delta, n_pts=300):
    """Hidden inputs whose hull-exceedance is ~delta spans."""
    span = w["hi"] - w["lo"]
    lo_b = w["hi"] + max(delta - 0.1, 0.0) * span
    hi_b = w["hi"] + delta * span
    return rng.uniform(lo_b, hi_b, (n_pts, w["d"]))


def held(w, isaac, name, Xh, thresh=0.7):
    yt = w["f"](Xh)
    yp = isaac.apply_law(name, Xh)
    if yp is None:
        return None
    ss = float(np.sum((yt - yt.mean()) ** 2))
    return (1 - float(np.sum((yt - yp) ** 2)) / max(ss, 1e-12)) >= thresh


def play_deck(kinds, label):
    out = []
    t0 = time.time()
    for wi, kind in enumerate(kinds):
        w = make_world(kind)
        isaac = Isaac()
        name = f"{label}{wi}"
        res = isaac.discover(w["X"], w["y"], name=name)
        if res["verdict"] not in ("UNDERSTOOD", "PARTIAL"):
            continue
        out.append((w, isaac, name, res))
    print(f"  {label}: {len(out)} kept laws from {len(kinds)} worlds "
          f"[{time.time()-t0:.0f}s]")
    return out


# ── 1. CALIBRATE: the measured survival curve ──────────────────────────
line("=")
print("1. MEASURE the decay: 60 calibration worlds, graded at 4 bands")
line("=")
cal = play_deck(KINDS, "c")
curve = {0.0: []}
for w, isaac, name, res in cal:
    m = isaac.net.get_meta(f"law:{name}", "model")
    curve[0.0].append(float(np.clip(m["r2_edge"], 0, 1)) >= 0.7)
    for b in BANDS:
        curve.setdefault(b, []).append(
            held(w, isaac, name, band_points(w, b)))
decay = {}
print(f"\n  {'delta (spans beyond)':>22s} {'held':>10s} {'rate':>7s}")
for b in sorted(curve):
    vals = [v for v in curve[b] if v is not None]
    rate = sum(vals) / max(len(vals), 1)
    decay[b] = round(rate, 3)
    print(f"  {b:22.1f} {sum(vals):5d}/{len(vals):<4d} {rate*100:6.0f}%")
print(f"\n  THE MEASURED CURVE: {decay}")

# ── 2. VALIDATE on fresh worlds: is predicted confidence calibrated? ───
line("=")
print("2. VALIDATE: 60 FRESH worlds; law_confidence() vs what happened")
line("=")
val = play_deck(KINDS, "v")
pred, actual = [], []
flat = 0.68                                      # the audit's one number
flat_gap = []
for w, isaac, name, res in val:
    for b in BANDS:
        Xh = band_points(w, b)
        h = held(w, isaac, name, Xh)
        if h is None:
            continue
        c = isaac.law_confidence(name, Xh, decay=decay)
        pred.append(float(np.mean(c)))
        actual.append(h)
        flat_gap.append((flat, h))

pred = np.array(pred); actual = np.array(actual, float)
print(f"\n  {len(pred)} extrapolation claims graded; reliability bins:")
print(f"  {'predicted conf':>16s} {'n':>5s} {'actual hold rate':>18s}")
gaps = []
for lo_b, hi_b in ((0, .3), (.3, .5), (.5, .7), (.7, .85), (.85, 1.01)):
    sel = (pred >= lo_b) & (pred < hi_b)
    if sel.sum() == 0:
        continue
    p_mean = pred[sel].mean()
    a_rate = actual[sel].mean()
    gaps.append(abs(p_mean - a_rate) * sel.sum())
    print(f"  {lo_b:.2f}-{hi_b:.2f} (mean {p_mean:.2f}) {sel.sum():5d} "
          f"{a_rate*100:16.0f}%")
ece = sum(gaps) / len(pred)
brier = float(np.mean((pred - actual) ** 2))
brier_flat = float(np.mean((flat - actual) ** 2))
print(f"\n  calibration error (ECE): {ece:.3f}")
print(f"  Brier score: graded confidence {brier:.3f}  vs  "
      f"flat 68% baseline {brier_flat:.3f}  "
      f"({'BETTER' if brier < brier_flat else 'NOT better'})")

line("=")
ok = ece < 0.15 and brier < brier_flat
print(f"VERDICT: {'WORKS' if ok else 'PARTIAL (see numbers)'} — the binary "
      f"stamp becomes graded belief:\nboundary confidence inside the hull, "
      f"measured-decay confidence beyond it,\nvalidated on worlds the curve "
      f"never saw.")
line("=")
