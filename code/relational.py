"""
FEATURE MATH — rung 2: RELATIONAL structures (functions between forms).

The relational MECHANISM, isolated from perception. "8 = two circles, aligned,
touching" is an EQUATION between the circles' parameters:
  8          : dist(c1,c2) = r1+r2 (touching)  AND  |dx| = 0 (vertically aligned)
  infinity   : dist = r1+r2                     AND  |dy| = 0 (horizontally aligned)
  separated  : dist > r1+r2
  overlapping: dist < r1+r2
  circle(0)  : one circle

This tests the relational recognizer on the component PARAMETERS — i.e., fed the
circles a working form-detector would hand it. (Recovering those circles from a
raw merged point cloud is a SEPARATE perception problem — clustering and RANSAC
both struggle on touching/overlapping circles; that is the front-end, not the
relation.) Here we prove the relation itself discriminates the concepts.

Run:  python relational.py
"""
import numpy as np
rng = np.random.default_rng(0)

TOUCH_T, ALIGN_T = 0.15, 0.20


def gen(kind):
    """An arrangement, parameterized: list of (center, radius). Random pos/scale."""
    c = rng.uniform(-3, 3, 2); r1 = rng.uniform(0.8, 1.5); r2 = rng.uniform(0.8, 1.5)
    if kind == "circle(0)":
        return [(c, (r1 + r2) / 2)]
    dirv = {"8": np.array([0., 1.]), "infinity": np.array([1., 0.])}.get(kind)
    if dirv is None:                                            # separated/overlapping: any axis
        a = rng.uniform(0, 2*np.pi); dirv = np.array([np.cos(a), np.sin(a)])
    dirv = dirv / np.linalg.norm(dirv)
    if kind == "separated":     sep = (r1 + r2) + rng.uniform(0.8, 1.6)
    elif kind == "overlapping": sep = (r1 + r2) * rng.uniform(0.4, 0.7)
    else:                       sep = r1 + r2                   # 8 / infinity: touching
    return [(c, r1), (c + dirv * sep, r2)]


def recognize(circles):
    """Relational recognition: read the equations between the forms' parameters."""
    if len(circles) == 1:
        return "circle(0)"
    (c1, r1), (c2, r2) = circles
    d = np.linalg.norm(c1 - c2); dx = abs(c1[0]-c2[0]); dy = abs(c1[1]-c2[1])
    touch = abs(d - (r1 + r2)) / (r1 + r2)                      # 0 = touching
    if touch < TOUCH_T:
        if dx / d < ALIGN_T: return "8"                        # aligned vertically (dx=0)
        if dy / d < ALIGN_T: return "infinity"                 # aligned horizontally (dy=0)
        return "two-touching(diag)"
    return "separated" if d > r1 + r2 else "overlapping"


def main():
    print("=" * 60)
    print("  RELATIONAL FEATURE MATH (rung 2) — the relation IS the concept")
    print("  [components given; perception/segmentation is a separate problem]")
    print("=" * 60)
    kinds = ["8", "infinity", "separated", "overlapping", "circle(0)"]
    N = 3000; hits = 0; by = {k: [0, 0] for k in kinds}
    for _ in range(N):
        k = kinds[int(rng.integers(0, len(kinds)))]
        ok = (recognize(gen(k)) == k); hits += ok
        by[k][0] += ok; by[k][1] += 1
    print(f"  overall accuracy: {hits/N:.3f}   (chance ~0.20)")
    for k in kinds:
        print(f"     {k:<12} : {by[k][0]/by[k][1]:.3f}")
    print("\n  8 vs infinity: identical components (two touching circles), identical")
    print("  'touching' equation — they differ ONLY in the alignment axis (dx=0 vs")
    print("  dy=0). Same parts, different relation, different concept. That's rung 2.")


if __name__ == "__main__":
    main()
