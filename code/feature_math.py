"""
FEATURE MATH — rung 1: concepts as FUNCTIONAL FORMS, recognized by fit.

A concept is not a stored pattern or a box — it's a FORM:
  circle = points equidistant from their center   (residual = radial spread)
  line   = points on a common axis                (residual = perpendicular spread)
Recognition = "which form does this data realize, and how tightly" — the lowest
residual against a genuinely-present form wins (a floor, so a blob that fits
nothing weakly isn't forced into a class). No training. No coordinates stored.

Because the form is invariant and only its parameters (center, radius, slope)
move, recognition is scale- and position-invariant FOR FREE — which a box,
being axis-aligned ranges, can never be. The closing demo proves it: a circle
and a square at the same center and extent have the IDENTICAL bounding box, so
any box/range method sees them as the same thing, while the form residual
separates them cleanly.

Run:  python feature_math.py
"""
import numpy as np
rng = np.random.default_rng(0)


# ---- shape generators: random center + scale + position every time ----
def circle(n=60):
    c = rng.uniform(-5, 5, 2); r = rng.uniform(0.5, 4); th = rng.uniform(0, 2*np.pi, n)
    return c + r*np.c_[np.cos(th), np.sin(th)] + rng.normal(0, 0.02*r, (n, 2))

def line(n=60):
    c = rng.uniform(-5, 5, 2); a = rng.uniform(0, np.pi); L = rng.uniform(1, 5)
    t = rng.uniform(-L, L, n); d = np.array([np.cos(a), np.sin(a)])
    return c + t[:, None]*d + rng.normal(0, 0.02*L, (n, 2))

def square(n=60):
    c = rng.uniform(-5, 5, 2); s = rng.uniform(1, 4)
    side = rng.integers(0, 4, n); t = rng.uniform(-s, s, n); p = np.empty((n, 2))
    for i, (sd, tt) in enumerate(zip(side, t)):
        p[i] = [tt, s] if sd == 0 else [tt, -s] if sd == 1 else [s, tt] if sd == 2 else [-s, tt]
    return c + p + rng.normal(0, 0.02*s, (n, 2))

def blob(n=60):
    c = rng.uniform(-5, 5, 2); s = rng.uniform(1, 4)
    return c + rng.uniform(-s, s, (n, 2))


# ---- the FORMS: fit the form, return the residual (how well it realizes it) ----
def circle_residual(p):
    x, y = p[:, 0], p[:, 1]                             # fit the CENTER (Kasa least-squares),
    A = np.c_[2*x, 2*y, np.ones(len(p))]                # not the centroid — the form's parameter
    a, b, cc = np.linalg.lstsq(A, x*x + y*y, rcond=None)[0]
    c = np.array([a, b]); r = np.linalg.norm(p - c, axis=1)
    return r.std() / (r.mean() + 1e-9)                 # radial spread, scale-normalized (the residual)

def line_residual(p):
    q = p - p.mean(0); _, _, vt = np.linalg.svd(q, full_matrices=False)
    perp = q @ vt[1]; ext = np.linalg.norm(q, axis=1).max() + 1e-9
    return perp.std() / ext                            # perpendicular spread, normalized

FORMS = {"circle": circle_residual, "line": line_residual}
FLOOR = 0.10                                           # a form must genuinely FIT, not just be closest


def recognize(p):
    res = {name: f(p) for name, f in FORMS.items()}
    best = min(res, key=res.get)
    return best if res[best] < FLOOR else "neither", res


def main():
    print("=" * 60)
    print("  FEATURE MATH — recognize by FORM FIT (scale/position free)")
    print("=" * 60)
    gens = {"circle": circle, "line": line, "square": square, "blob": blob}
    truth = {"circle": "circle", "line": "line", "square": "neither", "blob": "neither"}
    N = 2000; hits = 0; byclass = {k: [0, 0] for k in gens}
    for _ in range(N):
        kind = rng.choice(list(gens))
        pred, _ = recognize(gens[kind]())
        ok = (pred == truth[kind]); hits += ok
        byclass[kind][0] += ok; byclass[kind][1] += 1
    print(f"  overall accuracy (circle/line/neither): {hits/N:.3f}   (chance ~0.33)")
    for k, (c, t) in byclass.items():
        print(f"     {k:<8} -> {truth[k]:<8} : {c/t:.3f}")

    # ---- residual separation (form is present vs not) ----
    print("\n  median residuals (low = the form is realized):")
    for kind, gen in gens.items():
        rs = np.array([[circle_residual(p := gen()), line_residual(p)] for _ in range(300)])
        print(f"     {kind:<8} circle_resid={np.median(rs[:,0]):.3f}  line_resid={np.median(rs[:,1]):.3f}")

    # ---- the proof: a box cannot see form ----
    print("\n" + "=" * 60)
    print("  WHY A BOX CAN'T: circle vs square, SAME center & extent")
    print("=" * 60)
    c = np.zeros(2); r = 3.0
    th = np.linspace(0, 2*np.pi, 60, endpoint=False)
    circ = c + r*np.c_[np.cos(th), np.sin(th)]
    sq = square.__wrapped__ if hasattr(square, "__wrapped__") else None
    t = np.linspace(-r, r, 15)
    sqr = np.vstack([np.c_[t, np.full(15, r)], np.c_[t, np.full(15, -r)],
                     np.c_[np.full(15, r), t], np.c_[np.full(15, -r), t]])
    def bbox(p): return p[:, 0].min(), p[:, 0].max(), p[:, 1].min(), p[:, 1].max()
    print(f"  circle bbox : {tuple(round(v,1) for v in bbox(circ))}")
    print(f"  square bbox : {tuple(round(v,1) for v in bbox(sqr))}   <- IDENTICAL")
    print(f"  -> any box/range method: circle and square are the same object.")
    print(f"  circle_residual(circle) = {circle_residual(circ):.3f}")
    print(f"  circle_residual(square) = {circle_residual(sqr):.3f}   <- form sees the difference")


if __name__ == "__main__":
    main()
