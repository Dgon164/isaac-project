"""
DISCOVERY ENGINE — full-pass test battery (failure modes and limits).

Tests the ENGINE's discover() end to end (isaac.Isaac.discover), not a
harness copy. Every run logged to discovery_battery_results.csv as it runs.

Experiments (hypotheses up front):
  E1  noise floor        — at what noise/signal ratio does recovery break,
                           and does it break HONESTLY (verdict downgrades,
                           never fake UNDERSTOOD)?
  E2  sample onset       — how many examples before a law is recoverable?
  E3  distractors        — irrelevant features: does it admit false terms?
  E4  law size           — how many terms can it recover at once?
  E5  small terms        — detection floor for a weak term beside a strong one
  E6  collinear inputs   — near-duplicate features: misattribution risk
  E7  off-grid scales    — how far can refine reach beyond the atom grid
                           (grid max k=3; hypothesis: reach ~ x2 per sweep)
  E8  beyond the class   — laws it CANNOT say (nested nonlinearity, degree 4):
                           must land PARTIAL/CAPTURED, NEVER fake UNDERSTOOD
  E9  verdict calibration— pure noise x 20 seeds: false-discovery rate
  E10 extrapolation      — train on center, judge on edges: does the scope
                           label (form-true vs range-valid) tell the truth?
  E11 heavy tails        — lognormal / t-distributed inputs
"""
import csv
import sys
import time
import numpy as np

sys.path.insert(0, r"C:\Users\jtwee\Documents\isaac_project\code")
from isaac import Isaac

CSV = "discovery_battery_results.csv"


def shape(label):
    """Term shape ignoring scale constants: kinds + features."""
    import re
    return re.sub(r"\d+\.?\d*(?=\*x|\*\()", "K", label)


def run(exp, param, X, y, want_shapes=None, want_verdict=None, seeds_note=""):
    t0 = time.time()
    isaac = Isaac()
    res = isaac.discover(X, y)
    secs = time.time() - t0
    got = [t.strip() for t in res["equation"].replace("+", " +")
           .replace("-", " -").split()] if res["equation"] else []
    exact = None
    if want_shapes is not None:
        got_shapes = set()
        for part in res["equation"].split(" "):
            if "*" in part:
                got_shapes.add("*".join(sorted(part.split("*")[1:])))
        want = {"*".join(sorted(w.split("*"))) for w in want_shapes}
        exact = got_shapes == want
    verdict_ok = (res["verdict"] == want_verdict) if want_verdict else None
    row = dict(exp=exp, param=str(param), verdict=res["verdict"],
               r2=round(res["r2"], 4), r2_edge=round(res["r2_edge"], 4),
               captured=round(res["captured_r2"], 4),
               exact_form=exact, verdict_ok=verdict_ok,
               scope=res["scope"].split(" ")[0], secs=round(secs, 1),
               equation=res["equation"][:110])
    with open(CSV, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(row))
        if f.tell() == 0:
            w.writeheader()
        w.writerow(row)
    print(f"{exp:18s} {str(param):>14s}  {res['verdict']:10s} "
          f"R2 {res['r2']:6.3f} edge {res['r2_edge']:6.3f} "
          f"{'exact' if exact else ('     ' if exact is None else 'WRONG')}"
          f"  [{secs:.0f}s]  {res['equation'][:60]}")
    return res, exact


def main():
    open(CSV, "w").close()
    rng = np.random.default_rng(101)
    n = 1600

    print("\nE1 noise floor (law: x0*x1 + x2^2 - x3)")
    for sig in (0.02, 0.1, 0.2, 0.4, 0.8, 1.5):
        X = rng.normal(0, 1, (n, 5))
        y0 = X[:, 0] * X[:, 1] + X[:, 2] ** 2 - X[:, 3]
        y = y0 + rng.normal(0, sig * y0.std(), n)
        run("E1_noise", sig, X, y, want_shapes={"x0*x1", "x2*x2", "x3"})

    print("\nE2 sample onset (same law, noise 0.05)")
    for m in (100, 200, 400, 800, 1600, 3200):
        X = rng.normal(0, 1, (m, 5))
        y0 = X[:, 0] * X[:, 1] + X[:, 2] ** 2 - X[:, 3]
        y = y0 + rng.normal(0, 0.05 * y0.std(), m)
        run("E2_samples", m, X, y, want_shapes={"x0*x1", "x2*x2", "x3"})

    print("\nE3 distractor features (n=1600, noise 0.05)")
    for d in (5, 10, 20, 40):
        X = rng.normal(0, 1, (n, d))
        y0 = X[:, 0] * X[:, 1] + X[:, 2] ** 2 - X[:, 3]
        y = y0 + rng.normal(0, 0.05 * y0.std(), n)
        run("E3_distract", d, X, y, want_shapes={"x0*x1", "x2*x2", "x3"})

    print("\nE4 law size (k random var-product terms, d=8)")
    for k in (1, 2, 3, 4, 5, 6):
        X = rng.normal(0, 1, (n, 8))
        terms, y0 = [], np.zeros(n)
        for _ in range(k):
            i, j = rng.integers(0, 8), rng.integers(0, 8)
            terms.append(f"x{min(i,j)}*x{max(i,j)}")
            y0 = y0 + X[:, i] * X[:, j]
        y = y0 + rng.normal(0, 0.03 * y0.std(), n)
        run("E4_terms", k, X, y, want_shapes=set(terms))

    print("\nE5 small-term floor (x0*x1 + eps*x2^2, noise 0.02)")
    for eps in (1.0, 0.3, 0.1, 0.05, 0.02):
        X = rng.normal(0, 1, (n, 5))
        y0 = X[:, 0] * X[:, 1] + eps * X[:, 2] ** 2
        y = y0 + rng.normal(0, 0.02 * (X[:, 0] * X[:, 1]).std(), n)
        run("E5_smallterm", eps, X, y, want_shapes={"x0*x1", "x2*x2"})

    print("\nE6 collinear inputs (x1 = x0 + delta*noise; law: x0*x2)")
    for delta in (1.0, 0.3, 0.1, 0.03):
        X = rng.normal(0, 1, (n, 4))
        X[:, 1] = X[:, 0] + delta * rng.normal(0, 1, n)
        y0 = X[:, 0] * X[:, 2]
        y = y0 + rng.normal(0, 0.03 * y0.std(), n)
        run("E6_collinear", delta, X, y)

    print("\nE7 off-grid scale reach (y = sin(k*x0); grid max 3)")
    for k in (0.7, 1.3, 2.5, 4.5, 6.0, 9.0):
        X = rng.uniform(-3, 3, (n, 2))
        y = np.sin(k * X[:, 0]) + rng.normal(0, 0.02, n)
        run("E7_scale", k, X, y)

    print("\nE8 beyond the class — must NOT fake UNDERSTOOD")
    X = rng.normal(0, 1, (n, 4))
    run("E8_nested", "sin(3*x0*x1)",
        X, np.sin(3 * X[:, 0] * X[:, 1]) + rng.normal(0, 0.02, n))
    y4 = X[:, 0] * X[:, 1] * X[:, 2] * X[:, 3]
    run("E8_degree4", "x0*x1*x2*x3", X, y4 + rng.normal(0, 0.03 * y4.std(), n))
    run("E8_rational", "1/(1+x0^2)",
        X, 1.0 / (1 + X[:, 0] ** 2) + rng.normal(0, 0.01, n))

    print("\nE9 verdict calibration: pure noise x 20")
    false_disc = 0
    for s in range(20):
        r = np.random.default_rng(500 + s)
        X = r.normal(0, 1, (800, 5))
        isaac = Isaac()
        res = isaac.discover(X, r.normal(0, 1, 800))
        false_disc += res["verdict"] != "NO RULE"
    print(f"E9_null: verdicts other than NO RULE: {false_disc}/20")
    with open(CSV, "a", newline="") as f:
        f.write(f"E9_null,20seeds,false_discoveries={false_disc}/20\n")

    print("\nE10 extrapolation truth-telling: y=x2^2, judged on range edges")
    for spread in (1.0, 2.0, 3.0):
        X = rng.normal(0, spread, (n, 4))
        y = X[:, 2] ** 2 + rng.normal(0, 0.05, n)
        run("E10_extrap", spread, X, y, want_shapes={"x2*x2"})

    print("\nE11 heavy-tailed inputs (law: x0*x1*cos(x2-x3))")
    for dist in ("normal", "lognormal", "student_t3"):
        if dist == "normal":
            V = rng.normal(0, 1, (n, 2))
        elif dist == "lognormal":
            V = rng.lognormal(0, 0.5, (n, 2))
        else:
            V = rng.standard_t(3, (n, 2))
        X = np.column_stack([V, rng.normal(0, 1, (n, 2))])
        y0 = X[:, 0] * X[:, 1] * np.cos(X[:, 2] - X[:, 3])
        y = y0 + rng.normal(0, 0.02 * y0.std(), n)
        run("E11_tails", dist, X, y)

    print("\ndone —", CSV)


if __name__ == "__main__":
    main()
