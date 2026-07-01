"""
BOX crystal + PARTIAL DOOR OVERLAP, working TOGETHER (not instead) on real data.

  box crystal  : recognizes each digit image (continuous -> token, its strength, ~0.90)
  door overlap : recognizes the higher 'scene' concept from the SET of recognized
                 digits, by partial door overlap (its strength, recursive/partial)

A 'scene' = a few real digit images drawn from a concept's member set. The box
turns each image into a digit-token; door overlap matches the token-set against
scene concepts. The point: the composition should be ROBUST to the box's errors —
if one digit is misread, the scene still recognized from partial overlap.

Compared against an ORACLE (perfect digit labels) to isolate what the box's
~10% per-digit error costs the composition. His engine only.

Run:  python scene_recognition.py
"""
import numpy as np
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
from isaac import Isaac

SCENES = {"low": {0, 1, 2, 3}, "high": {6, 7, 8, 9},
          "evens": {0, 2, 4, 6, 8}, "odds": {1, 3, 5, 7, 9}}
K = 3                       # digits per scene
rng = np.random.default_rng(0)


def main():
    dig = load_digits()
    Xtr, Xte, ytr, yte = train_test_split(dig.data, dig.target, test_size=0.3,
                                          random_state=1, stratify=dig.target)

    # box crystal front-end (the confirmed continuous recognizer)
    isaac = Isaac()
    isaac.fit_lens("digits", Xtr, ytr, select=40)
    isaac.crystallize_features(Xtr, ytr, lens="digits")
    per_digit_acc = (isaac.classify_features(Xte) == yte).mean()

    # scene concepts wired as nodes with 'part' doors to digit-tokens
    for s, members in SCENES.items():
        for d in members:
            isaac.net.add_door(f"scene:{s}", f"d{d}", tag="part")
    scenes = list(SCENES)

    # index test images by their TRUE class so we can build scenes
    by_class = {c: np.where(yte == c)[0] for c in range(10)}

    def recognize_scene(active_tokens):
        fired = isaac.recognize_doors(active_tokens, tag="part", threshold=0.0)
        return max(scenes, key=lambda s: fired.get(f"scene:{s}", 0.0))

    box_hits = oracle_hits = 0
    N = 4000
    for _ in range(N):
        true = scenes[int(rng.integers(0, len(scenes)))]
        members = list(SCENES[true])
        chosen = rng.choice(members, size=min(K, len(members)), replace=False)
        idxs = [int(rng.choice(by_class[d])) for d in chosen]
        imgs = Xte[idxs]
        # BOX reads each image -> recognized digit tokens (with ~10% errors)
        preds = isaac.classify_features(imgs)
        box_tokens = {f"d{int(p)}" for p in preds}
        # ORACLE: perfect digit labels
        oracle_tokens = {f"d{int(d)}" for d in chosen}
        box_hits += (recognize_scene(box_tokens) == true)
        oracle_hits += (recognize_scene(oracle_tokens) == true)

    print("=" * 60)
    print("  BOX + DOOR OVERLAP together — scene recognition (real digits)")
    print("=" * 60)
    print(f"  box per-digit accuracy (front-end)        : {per_digit_acc:.3f}")
    print(f"  scene concept, box-read digits (TOGETHER) : {box_hits/N:.3f}")
    print(f"  scene concept, oracle digits (ceiling)    : {oracle_hits/N:.3f}")
    print("=" * 60)
    print("  READ: box does the continuous per-digit recognition; door overlap")
    print("  composes the recognized set into the scene concept. If the TOGETHER")
    print("  number is near the oracle, the composition absorbed the box's errors")
    print("  via partial overlap -- they work WITH each other.")


if __name__ == "__main__":
    main()
