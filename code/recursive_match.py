"""
RECURSIVE PARTIAL conceptual matching — the actual claim, tested.

Each level is the SAME partial matcher (graded W@x / fingerprint overlap) applied
to the OUTPUT of the level below, carrying confidence upward:

  L1: recognize base patterns (partial+scaled, from match_proto)  -> tokens + conf
  L2: a concept = a SET of L1 tokens; partial-match the recognized bag  -> tokens + conf
  L3: a concept = a SET of L2 tokens; partial-match again              -> top concept + conf

The point of PARTIAL all the way up: if one component is too corrupted to
recognize at L1, the L2/L3 concept is still recognized from the rest, at lower
confidence. We test that: top-concept accuracy vs noise, and a worked cascade
where a component is destroyed but the whole is still recognized.

Run:  python recursive_match.py
"""
import numpy as np
rng = np.random.default_rng(0)

ALPHABET = "abcd"; A = len(ALPHABET); AI = {c: i for i, c in enumerate(ALPHABET)}

# ---- L1: base patterns (scale-free signatures) ----
L1 = {"stripe": "abab", "ramp": "abcd", "arch": "abcba",
      "zigzag": "acac", "fall": "dcba", "bump": "abba"}
rle = lambda s: "".join(c for i, c in enumerate(s) if i == 0 or s[i-1] != c)
L1 = {k: rle(v) for k, v in L1.items()}

def featvec(sym):
    v = np.zeros(A + A*A)
    for c in sym:
        if c in AI: v[AI[c]] += 1
    for a, b in zip(sym, sym[1:]):
        if a in AI and b in AI: v[A + AI[a]*A + AI[b]] += 1
    n = np.linalg.norm(v); return v/n if n else v

L1_names = list(L1); W1 = np.array([featvec(L1[n]) for n in L1_names])

# ---- L2 / L3 concepts = sets of the level below ----
L2 = {"rainbow": ["arch", "ramp"], "flag": ["stripe", "fall"],
      "target": ["arch", "zigzag"], "wave": ["zigzag", "stripe"]}
L3 = {"poster": ["rainbow", "flag"], "banner": ["wave", "target"]}


def match_L1(pattern):
    """partial+scaled match of one base pattern -> (token, confidence)."""
    s = W1 @ featvec(rle(pattern)); j = int(s.argmax())
    return L1_names[j], float(s[j])

def match_set(bag, fingerprints):
    """partial conceptual match: concept score = mean confidence of its members
    present in the bag (a missing member contributes 0). Graded -> partial."""
    out = {}
    for name, parts in fingerprints.items():
        out[name] = np.mean([bag.get(p, 0.0) for p in parts])
    top = max(out, key=out.get)
    return top, out[top], out

def instantiate(part, max_scale, noise):
    """render an L1 concept as a scaled + noisy raw sequence."""
    seq = "".join(c * int(rng.integers(1, max_scale+1)) for c in L1[part])
    s = list(seq)
    for i in range(len(s)):
        if rng.random() < noise: s[i] = ALPHABET[int(rng.integers(0, A))]
    return "".join(s)


def recognize(instance):
    """instance = list of (L1-concept-name, raw_pattern). Recurse L1->L2->L3."""
    bag1 = {}
    for _, raw in instance:
        tok, conf = match_L1(raw)
        bag1[tok] = max(bag1.get(tok, 0.0), conf)          # carry best confidence
    # L2: match the recognized L1 bag against each L2 fingerprint
    bag2 = match_set(bag1, L2)[2]
    # L3: match the L2 scores against each L3 fingerprint
    top, conf, _ = match_set(bag2, L3)
    return top, conf, bag1, bag2


def make_top(top_name, max_scale, noise):
    inst = []
    for l2 in L3[top_name]:
        for l1 in L2[l2]:
            inst.append((l1, instantiate(l1, max_scale, noise)))
    return inst


def main():
    print("hierarchy:")
    print("  L3:", L3); print("  L2:", L2); print("  L1:", L1)
    print("=" * 56)
    print(f"  {'noise':>6} | {'top-concept accuracy':>22}")
    print("  " + "-" * 36)
    for noise in (0.0, 0.1, 0.2, 0.3):
        hit = 0; N = 3000
        for _ in range(N):
            true = list(L3)[int(rng.integers(0, len(L3)))]
            inst = make_top(true, max_scale=4, noise=noise)
            if recognize(inst)[0] == true: hit += 1
        print(f"  {noise:>6.1f} | {hit/N:>22.3f}   (chance 0.5)")
    print("  " + "-" * 36)

    print("\n  worked cascade — a 'poster', with ONE component destroyed:")
    inst = make_top("poster", max_scale=4, noise=0.0)
    inst[0] = ("arch", "zzzz")                              # obliterate the arch in 'rainbow'
    top, conf, bag1, bag2 = recognize(inst)
    print(f"    L1 recognized: { {k: round(v,2) for k,v in bag1.items()} }")
    print(f"    L2 scores    : { {k: round(v,2) for k,v in bag2.items()} }")
    print(f"    L3 -> {top}  (conf {conf:.2f})")
    print("  READ: the arch is gone, 'rainbow' is only half-supported, yet 'poster'")
    print("  still wins from the rest of the tower -- partial match carried upward.")


if __name__ == "__main__":
    main()
