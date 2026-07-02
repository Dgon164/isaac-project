"""
IDEALS + KEY IDENTIFIERS — the user's fruit architecture.

  "detect the object, scale it, compare an ideal or selection of similar
   ideals, overlap them... all very similar, but they have unique key
   identifiers."

Genus + differentia, mechanized:
  1. DETECT + REGISTER — canonicalize (position/scale factored out;
     the factored SIZE rejoins as evidence — cherry vs apple IS a size).
  2. IDEALS — each species' crystal concept (observed distributions) is the
     ideal; matching = graded overlap with each ideal.
  3. KEY IDENTIFIERS — within a tied family, the differentia are the doors
     whose class-conditional distributions overlap LEAST between the tied
     siblings (reuses the door-overlap machinery). Decide on those doors.
  4. HONEST LEVEL — if the identifiers cannot be seen (stem occluded), the
     answer is the GENUS ("cherry-or-plum"), not a confident wrong species.

World: cherry (small, stem), apple (big, stem), peach (big, fuzzy, no stem),
nectarine (big, shine spot), plum (mid, dark), black_cherry (small, dark,
stem). Everything round. Random position and size jitter on a 16x16 canvas.
"""
import sys
import numpy as np

sys.path.insert(0, r"C:\Users\jtwee\Documents\isaac_project\code")
from isaac import Isaac
from registration_perception import canonical, resample

rng = np.random.default_rng(8)
KINDS = ["cherry", "apple", "peach", "nectarine", "plum", "black_cherry"]
SPEC = dict(cherry=dict(r=(2.0, 2.8), i=0.55, stem=True, fuzz=False, shine=False),
            apple=dict(r=(4.0, 5.0), i=0.60, stem=True, fuzz=False, shine=False),
            peach=dict(r=(4.0, 5.0), i=0.45, stem=False, fuzz=True, shine=False),
            nectarine=dict(r=(4.0, 5.0), i=0.50, stem=False, fuzz=False, shine=True),
            plum=dict(r=(3.2, 4.0), i=0.25, stem=False, fuzz=False, shine=False),
            black_cherry=dict(r=(2.0, 2.8), i=0.25, stem=True, fuzz=False, shine=False))
CANON = 10                                       # canonical grid
N_FEAT = CANON * CANON + 2                       # pixels + (h, w) pose doors


def fruit(kind):
    s = SPEC[kind]
    rad = rng.uniform(*s["r"])
    cy = rng.uniform(rad + 3.5, 15 - rad - 0.5)  # room for the stem
    cx = rng.uniform(rad + 0.5, 15 - rad - 0.5)
    yy, xx = np.mgrid[0:16, 0:16]
    dist = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
    img = np.where(dist <= rad, s["i"] * rng.uniform(0.92, 1.08), 0.0)
    if s["fuzz"]:                                # peach: rough boundary
        band = (dist > rad - 1.2) & (dist <= rad + 0.8)
        img = np.where(band, s["i"] * rng.uniform(0.2, 1.3, (16, 16)), img)
    if s["shine"]:                               # nectarine: highlight spot
        hy, hx = cy - rad * 0.4, cx + rad * 0.35
        img = np.where(np.sqrt((yy - hy) ** 2 + (xx - hx) ** 2) < 1.2,
                       0.9, img)
    if s["stem"]:                                # thin line out the top
        top = int(round(cy - rad))
        img[max(0, top - 3):top, int(round(cx))] = 0.35
    return np.clip(img + rng.normal(0, 0.015, (16, 16)), 0, 1)


def featurize(img, with_flag=False):
    can, pose = canonical(img)
    can = resample(can, CANON) if can.shape != (CANON, CANON) else can
    h = pose["h"] if pose else 0
    w = pose["w"] if pose else 0
    vec = np.concatenate([can.ravel(), [h, w]])
    if not with_flag:
        return vec
    # truncation cue: an occluded object shows a CUT — the support's first
    # row is unusually wide (round things start narrow). Evidence of
    # occlusion demotes confidence; identity questions go to the identifiers.
    m = img.max()
    flat = False
    if m > 0:
        ys, xs = np.nonzero(img > 0.15 * m)
        if len(ys):
            wbox = xs.max() - xs.min() + 1
            top_w = np.count_nonzero(img[ys.min()] > 0.15 * m)
            flat = top_w >= 0.6 * wbox
    return vec, flat


def make(n_per):
    X, y = [], []
    for ki, kind in enumerate(KINDS):
        for _ in range(n_per):
            X.append(featurize(fruit(kind)))
            y.append(ki)
    return np.array(X), np.array(y)


# ---------------------------------------------------------------- matching
def scores_of(isaac, X):
    calib = isaac.net.get_meta("crystal", "calib")
    H = isaac.apply_lens(calib["lens"], np.atleast_2d(np.asarray(X, float)))
    edges = calib["edges"]
    concepts = [(isaac.net.get_meta(nm, "label"),
                 isaac.net.get_meta(nm, "doors"))
                for nm in sorted(isaac.net.get_doors("crystal", tag="crystal"))]
    S = np.zeros((len(H), len(concepts)))
    for j in range(H.shape[1]):
        idx = np.searchsorted(edges[j], H[:, j])
        for k, (_, ld) in enumerate(concepts):
            S[:, k] += ld[j][idx]
    return S, [lab for lab, _ in concepts]


def differentia(isaac, a, b, top=6):
    """Key identifiers between two ideals: doors whose observed
    distributions overlap least (graded overlap, per door)."""
    la = np.exp(np.array(isaac.net.get_meta(f"concept:{a}", "doors")))
    lb = np.exp(np.array(isaac.net.get_meta(f"concept:{b}", "doors")))
    ov = np.minimum(la, lb).sum(axis=1)          # per-feature overlap coeff
    return list(np.argsort(ov)[:top])


def recognize(isaac, x, tie_margin=4.0, decide_margin=1.5, truncated=False):
    """Match ideals; on a tie consult the pair's key identifiers; if they
    still cannot decide, answer at the GENUS level (the honest tie).
    Evidence of truncation forbids the confident fast path entirely."""
    S, labels = scores_of(isaac, x.reshape(1, -1))
    order = np.argsort(-S[0])
    a, b = str(labels[order[0]]), str(labels[order[1]])
    if not truncated and S[0][order[0]] - S[0][order[1]] >= tie_margin:
        return a, "confident"
    keys = differentia(isaac, a, b)
    calib = isaac.net.get_meta("crystal", "calib")
    edges = calib["edges"]
    sa = sb = 0.0
    for j in keys:
        idx = int(np.searchsorted(edges[j], x[j]))
        sa += isaac.net.get_meta(f"concept:{a}", "doors")[j][idx]
        sb += isaac.net.get_meta(f"concept:{b}", "doors")[j][idx]
    if abs(sa - sb) < decide_margin:
        return f"{a}|{b}", "genus"               # honest: this OR that
    return (a if sa > sb else b), "by-identifier"


# -------------------------------------------------------------------- test
def main():
    print("=" * 72)
    print("IDEALS + DIFFERENTIA — six round fruits, key identifiers")
    print("=" * 72)
    Xtr, ytr = make(220)
    Xte, yte = make(60)
    isaac = Isaac()
    isaac.crystallize_features(Xtr, ytr, lens=None)   # ideals, raw doors

    # 1. species accuracy through the cascade
    hits = ties = 0
    for x, t in zip(Xte, yte):
        ans, how = recognize(isaac, x)
        if "|" in ans:
            ties += 1
            hits += (str(t) in ans.split("|"))    # genus counts if it contains truth
        else:
            hits += (ans == str(t))
    acc = hits / len(yte)
    print(f"\n1. cascade accuracy (genus answers count if they contain the "
          f"truth): {acc*100:.1f}%  ({ties} honest genus answers)")

    # 2. are the key identifiers the PLANTED ones?
    name = {str(i): k for i, k in enumerate(KINDS)}
    pairs = [("0", "1", "size (pose doors 100,101)"),
             ("0", "5", "color/darkness (pixel intensities)"),
             ("2", "3", "fuzz vs shine (boundary/spot pixels)")]
    ok_size = False
    for a, b, expect in pairs:
        keys = differentia(isaac, a, b)
        tag = f"{name[a]} vs {name[b]}"
        print(f"2. {tag:26s} identifiers: {keys}   (planted: {expect})")
        if (a, b) == ("0", "1"):
            ok_size = any(k >= 100 for k in keys)
    print(f"   size doors are the cherry/apple identifier: {ok_size}")

    # 3. honesty under occlusion: hide the stem region -> apple loses its
    # identifier; a confident wrong species is the only true failure
    wrong_conf = genus_or_right = 0
    n_occ = 100
    for _ in range(n_occ):
        img = fruit("apple")
        img[:4, :] = 0                             # stem region occluded
        vec, flat = featurize(img, with_flag=True)
        ans, how = recognize(isaac, vec, truncated=flat)
        if "|" in ans or ans == "1":
            genus_or_right += 1
        elif how == "confident":
            wrong_conf += 1
    print(f"\n3. stem-occluded apples: right-or-honest-tie "
          f"{genus_or_right}/{n_occ}, confidently-wrong {wrong_conf}/{n_occ}")

    verdict = acc >= 0.85 and ok_size and wrong_conf <= n_occ * 0.2
    print("-" * 72)
    print(f"VERDICT: {'WORKS' if verdict else 'BROKEN'}")
    return verdict


if __name__ == "__main__":
    main()
