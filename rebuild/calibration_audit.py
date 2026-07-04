"""
THE CALIBRATION AUDIT (owner's priority 4, tier 5.2): the ONE trust number.

Until now every verdict Isaac issued was self-graded. Here the GM deals
~100 worlds with KNOWN truth; Isaac plays each cold (discover only, no
peeking); every claim he makes — verdict, scope label, accounting — is
graded externally on hidden data, half INSIDE his observed range, half
BEYOND it (form-true either survives out there or it was never form-true).

Deck (sampled, seeds fixed, all re-runnable):
  poly/product laws (in-class)   trig & exp laws (in-class)
  power laws (in-class)          plain linear sums (the KNOWN pathology)
  out-of-class (nested/gated)    pure noise (refusal is the win)
across noise levels {0.02..0.8 x signal} and n in {150, 400, 1200}.

Outputs:
  P(beyond-range holds | claimed form-true)      <- THE trust number
  P(inside holds       | claimed UNDERSTOOD)
  false-discovery rate on noise worlds
  honesty on out-of-class worlds
  accounting error |claimed articulated% - true law share|
"""
import sys
import time

import numpy as np

import os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from isaac import Isaac

rng = np.random.default_rng(101)


def line(c="-", n=70):
    print(c * n)


# ───────────────────────────── the deck ─────────────────────────────
def make_world(kind):
    d = int(rng.integers(2, 5))
    n = int(rng.choice([150, 400, 1200]))
    noise = float(rng.choice([0.02, 0.1, 0.3, 0.8]))
    lo, hi = -2.0, 2.0
    if kind == "poly":
        i, j, k = rng.integers(0, d, 3)
        c1, c2 = rng.uniform(0.5, 2, 2)
        f = lambda X: c1 * X[:, i] * X[:, j] + c2 * X[:, k] ** 2
    elif kind == "trig":
        i = int(rng.integers(0, d))
        a, k1 = rng.uniform(1, 4), float(rng.choice([0.5, 1.0, 2.0]))
        f = lambda X: a * np.cos(k1 * X[:, i])
    elif kind == "exp":
        i = int(rng.integers(0, d))
        k1 = float(rng.choice([0.5, 1.0]))
        f = lambda X: 2.0 * np.exp(-k1 * np.abs(X[:, i]))
    elif kind == "power":
        lo, hi = 0.5, 3.0
        i = int(rng.integers(0, d))
        a = float(rng.choice([0.5, 1.5, 2.0]))
        f = lambda X: 1.5 * X[:, i] ** a
    elif kind == "linsum":                      # the known pathology
        w = rng.uniform(0.5, 1.5, d)
        f = lambda X: X @ w
    elif kind == "outclass":
        i, j = rng.integers(0, d, 2)
        which = rng.random()
        if which < 0.5:
            f = lambda X: np.sin(3.0 * X[:, i] * X[:, j])
        else:
            thr = float(rng.uniform(-0.3, 0.3))
            f = lambda X: np.where(X[:, j] > thr,
                                   2.0 * X[:, i] * X[:, j], 0.3 * X[:, i])
    else:                                        # noise
        f = lambda X: np.zeros(len(X))
        noise = 1.0
    X = rng.uniform(lo, hi, (n, d))
    y0 = f(X)
    sd = noise * max(y0.std(), 1e-9) if kind != "noise" else 1.0
    y = y0 + rng.normal(0, sd, n)
    true_share = 100 * y0.var() / max(y0.var() + sd ** 2, 1e-12)
    return dict(kind=kind, X=X, y=y, f=f, lo=lo, hi=hi, d=d, n=n,
                true_share=true_share, sd=sd)


def grade(w, isaac, name):
    """External R2 on hidden inputs, inside and beyond the observed range."""
    out = {}
    span = w["hi"] - w["lo"]
    for tag, (a, b) in (("inside", (w["lo"], w["hi"])),
                        ("beyond", (w["hi"], w["hi"] + 0.6 * span))):
        Xh = rng.uniform(a, b, (400, w["d"]))
        yt = w["f"](Xh)
        yp = isaac.apply_law(name, Xh)
        if yp is None:
            out[tag] = None
            continue
        ss = float(np.sum((yt - yt.mean()) ** 2))
        out[tag] = 1 - float(np.sum((yt - yp) ** 2)) / max(ss, 1e-12)
    return out


# ───────────────────────────── play the deck (main only) ─────────────────────────────
if __name__ == "__main__":
    DECK = (["poly"] * 20 + ["trig"] * 15 + ["exp"] * 10 + ["power"] * 10
            + ["linsum"] * 15 + ["outclass"] * 15 + ["noise"] * 15)
    if __name__ != "__main__":                # imported (for make_world/grade):
        DECK = []                             # don't play the deck on import
    print(f"CALIBRATION AUDIT — {len(DECK)} worlds, external grading, "
          f"seeds fixed\n" if DECK else "", end="")
    t0 = time.time()
    rows = []
    for wi, kind in enumerate(DECK):
        w = make_world(kind)
        isaac = Isaac()
        name = f"w{wi}"
        res = isaac.discover(w["X"], w["y"], name=name)
        g = grade(w, isaac, name) if res["verdict"] in ("UNDERSTOOD", "PARTIAL") \
            else dict(inside=None, beyond=None)
        rows.append(dict(kind=kind, verdict=res["verdict"], scope=res["scope"],
                         r2_self=res["r2"], art=res["accounting"]["articulated"],
                         true_share=w["true_share"], gi=g["inside"],
                         gb=g["beyond"]))
        if (wi + 1) % 20 == 0:
            print(f"  ... {wi+1}/{len(DECK)} worlds played "
                  f"[{time.time()-t0:.0f}s]")

    # ───────────────────────────── the numbers ─────────────────────────────
    line("=")
    print("VERDICT MIX (his claims across the deck)")
    line("=")
    for v in ("UNDERSTOOD", "PARTIAL", "CAPTURED", "NO RULE"):
        ks = [r for r in rows if r["verdict"] == v]
        print(f"  {v:11s} {len(ks):3d}  "
              f"({', '.join(sorted(set(r['kind'] for r in ks))) or '—'})")

    line("=")
    print("THE TRUST NUMBERS (externally graded, hidden data)")
    line("=")
    ft = [r for r in rows if r["verdict"] == "UNDERSTOOD"
          and r["scope"].startswith("form-true") and r["gb"] is not None]
    ft_ok = [r for r in ft if r["gb"] >= 0.7]
    print(f"  claimed FORM-TRUE and it HELD beyond his data:   "
          f"{len(ft_ok)}/{len(ft)}"
          f"  = {100*len(ft_ok)/max(len(ft),1):.0f}%   <- THE trust number")
    un = [r for r in rows if r["verdict"] == "UNDERSTOOD" and r["gi"] is not None]
    un_ok = [r for r in un if r["gi"] >= 0.7]
    print(f"  claimed UNDERSTOOD and it held INSIDE his data:  "
          f"{len(un_ok)}/{len(un)}"
          f"  = {100*len(un_ok)/max(len(un),1):.0f}%")
    nz = [r for r in rows if r["kind"] == "noise"]
    fd = [r for r in nz if r["verdict"] not in ("NO RULE", "CAPTURED")]
    print(f"  noise worlds falsely given a law:                "
          f"{len(fd)}/{len(nz)}")
    oc = [r for r in rows if r["kind"] == "outclass"]
    oc_ft = [r for r in oc if r["verdict"] == "UNDERSTOOD"
             and r["scope"].startswith("form-true")
             and (r["gb"] is None or r["gb"] < 0.7)]
    print(f"  out-of-class worlds claimed form-true & failed:  "
          f"{len(oc_ft)}/{len(oc)}")
    ls = [r for r in rows if r["kind"] == "linsum"]
    ls_bad = [r for r in ls if r["verdict"] == "UNDERSTOOD"
              and r["gb"] is not None and r["gb"] < 0.7]
    print(f"  linear-sum worlds (known pathology) that fooled him: "
          f"{len(ls_bad)}/{len(ls)}")

    line("=")
    print("ACCOUNTING CALIBRATION (claimed articulated% vs GM truth)")
    line("=")
    acc = [r for r in rows if r["verdict"] in ("UNDERSTOOD", "PARTIAL")]
    errs = [abs(r["art"] - r["true_share"]) for r in acc]
    print(f"  worlds with a kept law: {len(acc)};  "
          f"mean |claimed - true| = {np.mean(errs):.1f} pts;  "
          f"median {np.median(errs):.1f};  worst {max(errs):.1f}")
    for lo_b, hi_b in ((0, 10), (10, 25), (25, 100)):
        k = sum(1 for e in errs if lo_b <= e < hi_b)
        print(f"    error {lo_b:3d}-{hi_b:3d} pts: {k:3d} worlds")

    line("=")
    by_scope = {}
    for r in rows:
        if r["verdict"] == "UNDERSTOOD" and r["gb"] is not None:
            key = "form-true" if r["scope"].startswith("form-true") \
                else "range-valid"
            by_scope.setdefault(key, []).append(r["gb"] >= 0.7)
    print("SCOPE LABEL CALIBRATION (does the label predict beyond-range fate?)")
    line("=")
    for k, v in by_scope.items():
        print(f"  labeled {k:11s}: {sum(v)}/{len(v)} held beyond "
              f"({100*sum(v)/len(v):.0f}%)")
    print(f"\n[{time.time()-t0:.0f}s total]")
