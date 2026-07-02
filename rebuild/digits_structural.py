"""
DIGITS, STRUCTURALLY — teach Isaac feature extraction, don't do it for him.

Generic percepts only (retina-class ops, no digit knowledge):
  - canonical pixels (registration front-end, proven)
  - pose (h, w) — the factored transformation, kept as evidence
  - HOLES: count of enclosed background regions (connected components of
    background not reachable from the border — generic topology)
  - CROSSINGS: ink transitions per row and per column (generic scanline op)

Which percepts matter for which confusion is NOT coded — the differentia
machinery discovers it per sibling pair, exactly as it discovered size for
cherry-vs-apple. Prediction from the structure of digits: 8-vs-3 and 4-vs-9
should pick the HOLE door; 1-vs-7 the crossing doors.
"""
import sys
import numpy as np

sys.path.insert(0, r"C:\Users\jtwee\Documents\isaac_project\code")
from isaac import Isaac
from registration_perception import canonical, resample, shift_pad, shrink_place
from ideals_differentia import scores_of, differentia
from sklearn.datasets import load_digits          # data loading only

rng = np.random.default_rng(3)
CANON = 10


def holes(binary):
    """Enclosed background regions: flood the border background, count the
    connected components of what remains. Generic topology, no digit lore."""
    H, W = binary.shape
    bg = ~binary
    seen = np.zeros_like(bg, dtype=bool)
    stack = [(y, x) for y in range(H) for x in (0, W - 1) if bg[y, x]]
    stack += [(y, x) for x in range(W) for y in (0, H - 1) if bg[y, x]]
    for p in stack:
        seen[p] = True
    while stack:
        y, x = stack.pop()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W and bg[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                stack.append((ny, nx))
        # count remaining background components
    rest = bg & ~seen
    count = 0
    for y in range(H):
        for x in range(W):
            if rest[y, x]:
                count += 1
                q = [(y, x)]
                rest[y, x] = False
                while q:
                    cy, cx = q.pop()
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and rest[ny, nx]:
                            rest[ny, nx] = False
                            q.append((ny, nx))
    return count


def crossings(binary):
    """Ink transitions per row and per column — generic scanline op."""
    row = [(np.diff(r.astype(int)) == 1).sum() for r in binary]
    col = [(np.diff(c.astype(int)) == 1).sum() for c in binary.T]
    return row + col


def featurize(img):
    can, pose = canonical(img)
    can = resample(can, CANON) if can.shape != (CANON, CANON) else can
    b = can > 0.25 * max(can.max(), 1e-9)
    # topology counted on the RAW image at a permissive threshold —
    # resampling blurs thin loops shut/open (measured: 8 read 0.40 holes on
    # the canonical grid, 0.96 on raw). The percept stays generic; only its
    # vantage point moved.
    braw = img > 0.12 * max(img.max(), 1e-9)
    h = pose["h"] if pose else 0
    w = pose["w"] if pose else 0
    return np.concatenate([can.ravel(), [h, w, holes(braw)],
                           crossings(b)]).astype(float)


NAMES = (["px"] * 100 + ["pose_h", "pose_w", "HOLES"]
         + [f"row_cross{i}" for i in range(CANON)]
         + [f"col_cross{i}" for i in range(CANON)])


def main():
    print("=" * 72)
    print("DIGITS — generic percepts, differentia learned per confusion")
    print("=" * 72)
    d = load_digits()
    X, y = d.data.astype(float), d.target
    idx = rng.permutation(len(y)); k = int(0.7 * len(y))
    tr, te = idx[:k], idx[k:]
    img = X.reshape(-1, 8, 8)

    F = np.array([featurize(im) for im in img])
    isaac = Isaac()
    isaac.crystallize_features(F[tr], y[tr], lens=None)
    S, labels = scores_of(isaac, F[te])
    pred = np.array([labels[i] for i in np.argmax(S, axis=1)])
    acc = (pred == y[te]).mean()
    print(f"\n1. clean accuracy, structural doors: {acc*100:.1f}%   "
          f"(pixel-only raw baseline was 88.1%)")

    print("\n2. learned differentia for the classic confusions:")
    for a, b in ((8, 3), (4, 9), (1, 7), (0, 8)):
        keys = differentia(isaac, a, b)
        named = [NAMES[k2] for k2 in keys]
        print(f"   {a} vs {b}: {named}")

    # robustness re-check through the same front-end
    imte = img[te]
    sh = np.array([featurize(shift_pad(im, 1, 1)) for im in imte])
    Ssh, _ = scores_of(isaac, sh)
    acc_sh = (np.array([labels[i] for i in np.argmax(Ssh, 1)]) == y[te]).mean()
    sk = np.array([featurize(shrink_place(im, 6, rng.integers(0, 3),
                                          rng.integers(0, 3))) for im in imte])
    Ssk, _ = scores_of(isaac, sk)
    acc_sk = (np.array([labels[i] for i in np.argmax(Ssk, 1)]) == y[te]).mean()
    print(f"\n3. shifted 1px: {acc_sh*100:.1f}%   shrunk 6x6+moved: "
          f"{acc_sk*100:.1f}%   (raw-pixel engine: 22%/13%)")


if __name__ == "__main__":
    main()
