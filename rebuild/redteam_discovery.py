"""
RED TEAM — attacking my own design decisions in discover().

Every mechanism added today fixed a failure; each can be exploited in the
opposite direction. Attacks designed WITH knowledge of the internals:

A1 PARSIMONY BIAS     I charge scale-atoms 2% R2 to stop cosine-as-parabola
                      impostors. Inverse exploit: plant a TRUE wide cosine —
                      does the toll make the engine report a polynomial?
A2 COMPLETION KNIFE   trials reaching R2>=0.995 outrank all others. Exploit:
                      a law with a term worth ~0.5% — completion may accept
                      the incomplete form and the gate may drop the crumb.
A3 EDGE BLIND SPOT    scope label checks RADIAL edges of the observed range.
                      Exploit: bimodal sampling with an interior HOLE — a
                      surrogate can be wrong in the hole yet labeled
                      form-true.
A4 FALSE 'NO RULE'    the worst epistemic failure: a DETERMINISTIC rule
                      (high-freq sin, beyond refine reach) + noise dims that
                      swamp the 5-NN capture -> engine may claim NO RULE
                      where a perfect rule exists.
A5 GROWTH IMPOSTOR    exp atoms are DECAY-only (k>0). Exploit: y=e^(0.5x) —
                      a cubic fits iid samples at R2~0.999 -> wrong form
                      may pass as UNDERSTOOD, even 'form-true'.
A6 SORTED-DATA TRAP   discover() splits train/held-out SEQUENTIALLY. Exploit:
                      pass data sorted by a feature — train sees half the
                      range only.
A7 WILD SCALES        no input standardization. Features in units of 1e6 and
                      1e-3 — do transcendental atoms poison the search?
A8 NaN POISON         one NaN row — crash, garbage, or honest handling?

Verdicts: KILL (design flaw demonstrated) / SURVIVED / FLESH WOUND (degraded
but honest). Report what the engine DID, not what I hoped.
"""
import sys
import numpy as np

sys.path.insert(0, r"C:\Users\jtwee\Documents\isaac_project\code")
from isaac import Isaac

rng = np.random.default_rng(66)
n = 1600


def attack(name, X, y, judge):
    isaac = Isaac()
    try:
        res = isaac.discover(np.asarray(X, float), np.asarray(y, float))
    except Exception as e:
        print(f"{name}: CRASH — {type(e).__name__}: {e}")
        return "CRASH"
    verdict = judge(res)
    print(f"{name}: {verdict}")
    print(f"    -> {res['verdict']} [{res['scope'].split(' ')[0]}] "
          f"R2 {res['r2']:.3f} edge {res['r2_edge']:.3f} "
          f"cap {res['captured_r2']:.3f}")
    print(f"    eq: {res['equation'][:100]}")
    return verdict


print("=" * 74)
print("RED TEAM vs discover()")
print("=" * 74)

# A1 parsimony bias: TRUE law is a wide cosine
for k in (0.25, 0.4):
    X = rng.uniform(-3, 3, (n, 3))
    y = 5.0 * np.cos(k * X[:, 0]) + rng.normal(0, 0.02, n)
    attack(f"A1 true wide cosine k={k}", X, y,
           lambda r: ("SURVIVED (found the cosine)" if "cos" in r["equation"]
                      and "x0*x0" not in r["equation"] else
                      "KILL (parsimony toll suppressed the true cosine)"))

# A2 completion knife: main term + a 0.5%-variance crumb
X = rng.normal(0, 1, (n, 4))
y = X[:, 0] * X[:, 1] + 0.07 * X[:, 2] + rng.normal(0, 0.005, n)
attack("A2 completion vs 0.5% crumb", X, y,
       lambda r: ("SURVIVED (crumb recovered)" if "x2" in r["equation"]
                  else "KILL (completion bonus ate the small term)"))

# A3 edge blind spot: interior hole, surrogate wrong in the hole
x0 = np.concatenate([rng.normal(-2, 0.3, n // 2), rng.normal(2, 0.3, n // 2)])
X = np.column_stack([x0, rng.normal(0, 1, (n, 2))])
y = X[:, 0] ** 2 + rng.normal(0, 0.02, n)
attack("A3 bimodal hole (y=x0^2)", X, y,
       lambda r: ("SURVIVED (true form)" if "x0*x0" in r["equation"]
                  else f"KILL (surrogate labeled {r['scope'].split(' ')[0]} "
                       "with an unobserved hole)"))

# A4 false NO RULE: deterministic rule beyond reach + NN swamped
X = np.column_stack([rng.uniform(-3, 3, (n, 1)), rng.normal(0, 1, (n, 30))])
y = np.sin(9.0 * X[:, 0])                       # deterministic, zero noise
attack("A4 deterministic sin(9x) + 30 noise dims", X, y,
       lambda r: ("KILL (claimed NO RULE against a deterministic rule)"
                  if r["verdict"] == "NO RULE" else
                  f"FLESH WOUND (honest {r['verdict']})"))

# A5 growth impostor: exp growth not in the library
X = rng.normal(0, 1, (n, 3))
y = np.exp(0.5 * X[:, 0]) + rng.normal(0, 0.01, n)
attack("A5 exp growth (library is decay-only)", X, y,
       lambda r: ("KILL (polynomial/wrong form passed as UNDERSTOOD "
                  f"[{r['scope'].split(' ')[0]}])"
                  if r["verdict"] == "UNDERSTOOD"
                  and "exp" not in r["equation"] else
                  "SURVIVED (honest or found a usable exp form)"))

# A6 sorted-data trap: sequential split sees half the range
X = rng.normal(0, 1, (n, 3))
order = np.argsort(X[:, 0])
Xs, ys = X[order], (X[order][:, 0] ** 2 + rng.normal(0, 0.02, n))
attack("A6 sorted input (y=x0^2)", Xs, ys,
       lambda r: ("SURVIVED (true form despite covariate shift)"
                  if "x0*x0" in r["equation"] and r["r2"] > 0.9 else
                  "KILL (sequential split broke on sorted data)"))

# A7 wild scales, no standardization
X = np.column_stack([rng.normal(0, 1e6, n), rng.normal(0, 1e-3, n),
                     rng.normal(0, 1, n)])
y = (X[:, 0] / 1e6) * (X[:, 1] / 1e-3) + rng.normal(0, 0.02, n)
attack("A7 features at 1e6 and 1e-3 scales", X, y,
       lambda r: ("SURVIVED (recovered product across 9 orders of magnitude)"
                  if "x0*x1" in r["equation"] and r["r2"] > 0.95 else
                  "KILL (unscaled inputs poisoned the search)"))

# A8 NaN poison
X = rng.normal(0, 1, (n, 3))
y = X[:, 0] * X[:, 1] + rng.normal(0, 0.02, n)
X[7, 1] = np.nan
attack("A8 one NaN cell", X, y,
       lambda r: ("FLESH WOUND (no crash; verdict "
                  f"{r['verdict']})" if r["verdict"] != "UNDERSTOOD"
                  or r["r2"] > 0.9 else "KILL"))
