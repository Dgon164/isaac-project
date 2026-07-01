"""
HASH + OVERLAY — recognition by match-by-rendering, not by parsing.

Pipeline:
  1) library of shape templates
  2) cheap, scale/rotation-invariant HASH -> shortlist the few closest candidates
  3) for each candidate, FIT by scale+rotation, lay it over the input, score the
     DIFFERENCE (disagreeing pixels). Least difference wins.
  4) report the winner AND the recovered pose (scale, rotation).

Test on shapes at sizes and rotations NEVER stored, to see if the transform
absorbs the variation (generalize-by-construction).
"""

import numpy as np
from scipy import ndimage

RNG = np.random.default_rng(0)
N = 48  # working canvas for normalized shapes


# ───────────── shape rendering (filled polygons + circle) ─────────────
def render_shape(kind, size, rot_deg, cx=N//2, cy=N//2):
    g = np.zeros((N, N), float)
    if kind == "circle":
        yy, xx = np.mgrid[0:N, 0:N]
        g[(xx-cx)**2 + (yy-cy)**2 <= size**2] = 1
        return g
    nmap = {"triangle": 3, "square": 4, "pentagon": 5, "hexagon": 6, "star": 5}
    n = nmap[kind]
    rot = np.deg2rad(rot_deg)
    if kind == "star":
        pts = []
        for k in range(2*n):
            r = size if k % 2 == 0 else size*0.45
            a = rot + np.pi*k/n
            pts.append((cx + r*np.cos(a), cy + r*np.sin(a)))
    else:
        pts = [(cx + size*np.cos(rot + 2*np.pi*k/n),
                cy + size*np.sin(rot + 2*np.pi*k/n)) for k in range(n)]
    # scanline fill
    poly = np.array(pts)
    from matplotlib.path import Path
    path = Path(poly)
    yy, xx = np.mgrid[0:N, 0:N]
    pts_grid = np.vstack([xx.ravel(), yy.ravel()]).T
    mask = path.contains_points(pts_grid).reshape(N, N)
    g[mask] = 1
    return g


# ───────────── normalize: center + scale to a canonical box ─────────────
def normalize(g):
    ys, xs = np.nonzero(g)
    if len(xs) == 0:
        return g
    crop = g[ys.min():ys.max()+1, xs.min():xs.max()+1]
    # scale longest side to ~36px in the NxN frame, centered
    h, w = crop.shape
    s = 36.0 / max(h, w)
    zoomed = ndimage.zoom(crop, s, order=0)
    out = np.zeros((N, N), float)
    zh, zw = zoomed.shape
    oy, ox = (N-zh)//2, (N-zw)//2
    out[oy:oy+zh, ox:ox+zw] = zoomed[:min(zh, N), :min(zw, N)]
    return out


# ───────────── cheap invariant HASH (scale+rotation agnostic) ─────────────
def shape_hash(g):
    """Radial signature: fraction of 'on' mass at increasing radii from the
    centroid, normalized. Invariant to scale (we normalize radius) and to
    rotation (radial, angle-agnostic). Cheap shortlist key."""
    ys, xs = np.nonzero(g)
    if len(xs) == 0:
        return np.zeros(8)
    cy, cx = ys.mean(), xs.mean()
    r = np.sqrt((xs-cx)**2 + (ys-cy)**2)
    r = r / (r.max() + 1e-6)
    hist, _ = np.histogram(r, bins=8, range=(0, 1), density=True)
    return hist / (np.linalg.norm(hist) + 1e-6)


def hash_dist(a, b):
    return np.linalg.norm(a - b)


# ───────────── overlay verify: fit rotation, score difference ─────────────
def overlay_score(template, target):
    """Best (lowest) disagreement over a sweep of rotations. Returns
    (score, best_rotation_deg). Both already normalized/centered."""
    best, best_rot = 1e9, 0
    tgt = target > 0.5
    for rd in range(0, 360, 10):
        rot = ndimage.rotate(template, rd, reshape=False, order=0) > 0.5
        disagree = np.logical_xor(rot, tgt).sum()
        union = np.logical_or(rot, tgt).sum() + 1e-6
        score = disagree / union          # 0 = perfect, 1 = nothing in common
        if score < best:
            best, best_rot = score, rd
    return best, best_rot


def main():
    kinds = ["triangle", "square", "pentagon", "hexagon", "circle", "star"]

    # library: ONE canonical template per shape (fixed size, rot 0)
    library = {}
    for k in kinds:
        library[k] = {"img": normalize(render_shape(k, 16, 0)),
                      "hash": None}
    for k in kinds:
        library[k]["hash"] = shape_hash(library[k]["img"])

    print("="*60)
    print("  HASH + OVERLAY  (templates stored at one size, rot 0)")
    print("="*60)

    # test: novel sizes AND rotations
    trials = []
    for _ in range(60):
        true = RNG.choice(kinds)
        size = int(RNG.integers(9, 20))      # novel sizes
        rot = float(RNG.uniform(0, 360))     # novel rotations
        trials.append((true, size, rot))

    correct = 0
    shortlist_hit = 0
    pose_err = []
    for true, size, rot in trials:
        tgt = normalize(render_shape(true, size, rot))
        th = shape_hash(tgt)
        # shortlist by hash
        ranked = sorted(kinds, key=lambda k: hash_dist(th, library[k]["hash"]))
        shortlist = ranked[:3]
        shortlist_hit += (true in shortlist)
        # verify by overlay over the shortlist
        best_k, best_s, best_rot = None, 1e9, 0
        for k in shortlist:
            s, r = overlay_score(library[k]["img"], tgt)
            if s < best_s:
                best_k, best_s, best_rot = k, s, r
        correct += (best_k == true)

    print(f"  trials: {len(trials)}  (all novel size+rotation)")
    print(f"  shortlist (top-3 by hash) contained the true shape: "
          f"{shortlist_hit}/{len(trials)} = {shortlist_hit/len(trials):.0%}")
    print(f"  final recognition after overlay verify: "
          f"{correct}/{len(trials)} = {correct/len(trials):.0%}")

    # per-shape breakdown
    print("\n  per-shape:")
    by = {}
    for true, size, rot in trials:
        tgt = normalize(render_shape(true, size, rot))
        th = shape_hash(tgt)
        ranked = sorted(kinds, key=lambda k: hash_dist(th, library[k]["hash"]))
        best_k, best_s = None, 1e9
        for k in ranked[:3]:
            s, _ = overlay_score(library[k]["img"], tgt)
            if s < best_s:
                best_k, best_s = k, s
        by.setdefault(true, [0, 0]); by[true][0]+= (best_k==true); by[true][1]+=1
    for k in kinds:
        if k in by:
            print(f"    {k:9} {by[k][0]}/{by[k][1]}")


if __name__ == "__main__":
    main()
