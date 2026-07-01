"""
Compare PARTIAL DOOR OVERLAP recognition against a CONFIRMED his-way result,
on the SAME real data and split: sklearn digits (his box-crystal ~0.90 this
session, crystal_in_isaac.py). Both run here, side by side, his engine only.

door-overlap classifier (the new mechanism):
  - binarize each 8x8 digit -> a SET of active-pixel tokens (its 'doors present')
  - per class, wire concept:c -> the pixels that recur (active in >= THETA of its
    train examples) — crystallize the class as a node with part-doors
  - recognize a test digit by isaac.recognize_doors: the class whose part-doors
    overlap the digit's active pixels the most (partial, his net)

Run:  python door_digits.py
"""
import numpy as np
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
from isaac import Isaac

THETA = 0.5          # a pixel is a class door if active in >= 50% of its examples
ON = 4               # pixel "active" if intensity > ON (digits are 0..16)


def main():
    dig = load_digits()
    Xtr, Xte, ytr, yte = train_test_split(dig.data, dig.target, test_size=0.3,
                                          random_state=1, stratify=dig.target)
    classes = sorted(np.unique(ytr).tolist())

    # ---- CONFIRMED baseline: his box crystal on the same split ----
    isaac = Isaac()
    isaac.fit_lens("digits", Xtr, ytr, select=40)
    isaac.crystallize_features(Xtr, ytr, lens="digits")
    box_acc = (isaac.classify_features(Xte) == yte).mean()

    # ---- NEW: partial door overlap classifier, his net ----
    iz = Isaac()
    Btr = Xtr > ON                                  # binarize -> active pixels
    Bte = Xte > ON
    door_counts = {}
    for c in classes:
        frac = Btr[ytr == c].mean(0)                # how often each pixel is on for class c
        doors = [f"p{j}" for j in range(Btr.shape[1]) if frac[j] >= THETA]
        for d in doors:
            iz.net.add_door(f"concept:{c}", d, tag="part")
        door_counts[c] = len(doors)

    correct = 0
    for row, true in zip(Bte, yte):
        active = {f"p{j}" for j in range(len(row)) if row[j]}
        fired = iz.recognize_doors(active, tag="part", threshold=0.0)
        best = max(classes, key=lambda c: fired.get(f"concept:{c}", 0.0))
        correct += (best == true)
    door_acc = correct / len(yte)

    print("=" * 60)
    print("  DIGITS — same split, his engine only")
    print("=" * 60)
    print(f"  box crystal (confirmed this session) : {box_acc:.3f}")
    print(f"  partial door overlap (NEW)           : {door_acc:.3f}")
    print(f"  (avg doors per class concept: "
          f"{np.mean(list(door_counts.values())):.0f} of 64 pixels)")
    print("=" * 60)
    print("  READ: how does partial door overlap stack up against the confirmed")
    print("  box reader, on the same real digits? Reported as-is.")


if __name__ == "__main__":
    main()
