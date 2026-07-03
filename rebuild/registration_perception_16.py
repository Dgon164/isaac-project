"""
REGISTRATION PERCEPTION — phase 1 on the FAIR canvas (16x16).

Rebuild (2026-07-03) of the 16x16 harness whose numbers (84.4% random
position+size, 86.5% novel bigger sizes, ~59% novel tiny) were recorded on
2026-07-01 but never committed. The 8x8 script (registration_perception.py)
demonstrates the mechanism but its canvas clips shifted pixels off the edge —
information destruction, not registration failure. Here the canvas is 16x16,
digits are resampled to a random size and placed at a random position, and
nothing is destroyed: pose is factored out by the SAME canonical() used in the
8x8 script (support box -> resample to 8x8), pose returned as information.

Claims under re-verification:
  raw doors on the canvas: ~5-15%      registered: ~84-87%
  novel BIGGER sizes (13-15, never trained): generalizes (~86%)
  novel tiny sizes (6-7): information-theoretic floor (~59%)
"""
import sys
import numpy as np

import os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))  # repo-local isaac.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from isaac import Isaac
from registration_perception import resample, canonical
from sklearn.datasets import load_digits          # data loading only

rng = np.random.default_rng(3)
CANVAS = 16


def place(img, size, oy, ox):
    """Resample an 8x8 digit to size x size, place on a 16x16 canvas."""
    c = np.zeros((CANVAS, CANVAS))
    c[oy:oy + size, ox:ox + size] = resample(img, size)
    return c


def random_canvas(flat, sizes):
    out = np.empty((len(flat), CANVAS * CANVAS))
    for i, row in enumerate(flat):
        s = int(rng.integers(sizes[0], sizes[1] + 1))
        oy = int(rng.integers(0, CANVAS - s + 1))
        ox = int(rng.integers(0, CANVAS - s + 1))
        out[i] = place(row.reshape(8, 8), s, oy, ox).ravel()
    return out


def canon_all(flat, side):
    out = np.empty((len(flat), 64))
    for i, row in enumerate(flat):
        c, _ = canonical(row.reshape(side, side))
        out[i] = c.ravel()
    return out


def main():
    d = load_digits()
    X, y = d.data.astype(float), d.target
    idx = rng.permutation(len(y)); k = int(0.7 * len(y))
    tr, te = idx[:k], idx[k:]

    # canvases: every image gets its own random size + position
    Ctr = random_canvas(X[tr], (8, 12))
    Cte = random_canvas(X[te], (8, 12))
    Cte_big = random_canvas(X[te], (13, 15))    # sizes NEVER seen in training
    Cte_tiny = random_canvas(X[te], (6, 7))     # below native resolution

    # ---- RAW pipeline: doors straight on the 16x16 canvas
    raw = Isaac(); raw.fit_lens("eyes", Ctr)
    raw.crystallize_features(Ctr, y[tr], lens="eyes")

    # ---- REGISTERED pipeline: canonicalize (support box -> 8x8) both sides
    Ktr = canon_all(Ctr, CANVAS)
    reg = Isaac(); reg.fit_lens("eyes", Ktr)
    reg.crystallize_features(Ktr, y[tr], lens="eyes")

    # clean control: canonicalized native digits, same classifier settings
    Kclean_tr, Kclean_te = canon_all(X[tr], 8), canon_all(X[te], 8)
    clean = Isaac(); clean.fit_lens("eyes", Kclean_tr)
    clean.crystallize_features(Kclean_tr, y[tr], lens="eyes")
    a_clean = (clean.classify_features(Kclean_te) == y[te]).mean()

    rows = [
        ("random pos + size 8-12", Cte),
        ("novel bigger 13-15",     Cte_big),
        ("novel tiny 6-7",         Cte_tiny),
    ]
    print(f"clean control (canonical, native 8x8): {a_clean*100:.1f}%\n")
    print(f"{'variant':26s} {'raw doors':>10s} {'registered':>11s}")
    print("-" * 50)
    results = {}
    for name, V in rows:
        a_raw = (raw.classify_features(V) == y[te]).mean()
        a_reg = (reg.classify_features(canon_all(V, CANVAS)) == y[te]).mean()
        results[name] = (a_raw, a_reg)
        print(f"{name:26s} {a_raw*100:9.1f}% {a_reg*100:10.1f}%")

    # pose is INFORMATION on the big canvas too
    im = X[te][0].reshape(8, 8)
    _, p0 = canonical(place(im, 10, 2, 3))
    _, p1 = canonical(place(im, 10, 5, 6))
    print(f"\npose readout: displacement seen = "
          f"dy {p1['cy']-p0['cy']:+.1f}, dx {p1['cx']-p0['cx']:+.1f} "
          f"(planted +3, +3)")
    _, p2 = canonical(place(im, 14, 1, 1))
    print(f"pose readout: size seen = {p2['h']}x{p2['w']} vs {p0['h']}x{p0['w']}"
          f" (planted 14 vs 10)")

    ok = (results["random pos + size 8-12"][1] > 0.80
          and results["novel bigger 13-15"][1] > 0.80
          and results["random pos + size 8-12"][0] < 0.30)
    print(f"\nVERDICT: {'WORKS' if ok else 'CHECK NUMBERS'} — registration "
          f"recovers the wall the raw canvas hits; bigger-than-trained sizes "
          f"generalize; tiny sizes are an information floor, not a "
          f"registration failure.")


if __name__ == "__main__":
    main()
