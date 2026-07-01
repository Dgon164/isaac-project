"""
WHAT YOU CAN DECODE FROM THE BOXES — on digits (8x8 pixels = 64 readable dims).
Tiny, CPU, instant, no reservoirs. The boxes ARE Isaac concepts; this reads them.
"""
import numpy as np
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
from range_classifier import RangeClassifier

dig = load_digits()
Xtr, Xte, ytr, yte = train_test_split(dig.data, dig.target, test_size=0.3, random_state=1, stratify=dig.target)
clf = RangeClassifier(max_splits=5).fit(Xtr, ytr)
print(f"accuracy: {clf.score_accuracy(Xte, yte):.3f}   concepts: {len(clf.concepts)}\n")

generals = [c for c in clf.concepts if c["type"] == "general"]
RAMP = " .:-=+*#%@"


def render(vec):
    g = vec.reshape(8, 8)
    g = (g - g.min()) / (np.ptp(g) + 1e-9)
    return "\n".join("   " + "".join(RAMP[int(v * 9)] for v in row) for row in g)


# 1) PROTOTYPE: the box's median IS a readable picture of the class
print("=" * 64)
print("  1) PROTOTYPES — each box's median, drawn (it knows what a digit is)")
print("=" * 64)
for d in (0, 1, 8):
    c = next(c for c in generals if c["label"] == d)
    print(f"\n  digit {d}:")
    print(render(c["med"]))

# 2) FEATURE RELEVANCE: narrow range = defining pixel; wide = don't-care
print("\n" + "=" * 64)
print("  2) WHAT DEFINES EACH DIGIT — count of TIGHT (defining) dims per class")
print("=" * 64)
for c in generals:
    width = c["hi"] - c["lo"]
    tight = int((width <= np.percentile(width, 25)).sum())
    print(f"  digit {c['label']}: {tight}/64 pixels are tightly constrained (its signature)")

# 3) RELATIONAL MEANING: which dims SEPARATE which class-pairs
print("\n" + "=" * 64)
print("  3) RELATIONAL MAP — which pixels separate two confusable digits")
print("=" * 64)
def sep_dims(a, b):
    ca = next(c for c in generals if c["label"] == a)
    cb = next(c for c in generals if c["label"] == b)
    overlap = np.minimum(ca["hi"], cb["hi"]) - np.maximum(ca["lo"], cb["lo"])
    return np.where(overlap < 0)[0]  # non-overlapping = separating dims
for a, b in [(1, 7), (3, 8), (5, 6)]:
    s = sep_dims(a, b)
    print(f"  {a} vs {b}: {len(s)} separating pixels, at grid positions "
          f"{[(int(i//8), int(i%8)) for i in s[:6]]}{'...' if len(s)>6 else ''}")

# 4) CONFUSION STRUCTURE: the variant concepts name who-confuses-with-who
print("\n" + "=" * 64)
print("  4) CONFUSION STRUCTURE — the variant boxes record real confusions")
print("=" * 64)
from collections import Counter
conf = Counter(c["type"] for c in clf.concepts if c["type"] != "general")
for t, n in conf.most_common(8):
    print(f"  {n}x  {t}")

# 5) GEOMETRY DIAGNOSIS: how box-friendly is this representation?
print("\n" + "=" * 64)
print("  5) GEOMETRY — fraction of dims that separate at least one class-pair")
print("=" * 64)
discrim = 0
for d in range(64):
    los = np.array([c["lo"][d] for c in generals]); his = np.array([c["hi"][d] for c in generals])
    pairwise = [his[i] < los[j] or his[j] < los[i] for i in range(len(generals)) for j in range(i+1, len(generals))]
    if any(pairwise):
        discrim += 1
print(f"  {discrim}/64 pixels cleanly separate >=1 digit pair (box-friendly signal).")
print("  High = axis-aligned/decodable. Low = diagonally entangled (box-hostile).")
