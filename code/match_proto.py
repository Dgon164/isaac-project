"""
MATCH PROTO — step 1: PARTIAL + SCALED matching, done as a matrix multiply.
Standalone (does NOT touch the engine) so the idea is TESTABLE before integrating.
Same mechanic as his _route (scores = W @ x), extended two ways:

  SCALED  : run-length encode the input first -> the symbol sequence is
            scale-invariant, so 01010 and 0011001100 are the SAME pattern.
  PARTIAL : represent a pattern as graded uni/bi-gram features and match by
            dot product (cosine), so a noisy/incomplete instance still scores
            ("82% of X, highest") instead of all-or-nothing.

Test: recognize concepts across SCALE (random run lengths) and NOISE (random
symbol corruption), comparing three levels so each mechanism's contribution is
visible:
  exact          : raw sequence must equal the canonical pattern   (no scale, no partial)
  scaled-only    : RLE + exact symbol match                        (scale, no partial)
  partial+scaled : RLE + graded matrix match                       (both)

Run:  python match_proto.py
"""
import numpy as np

ALPHABET = "abcd"
A = len(ALPHABET); AI = {c: i for i, c in enumerate(ALPHABET)}
rng = np.random.default_rng(0)

# concepts = scale-invariant symbol signatures (no run lengths, just the shape)
CONCEPTS = {
    "stripe": "abab",
    "ramp":   "abcd",
    "arch":   "abcba",
    "pair":   "aabb",      # note: as a *signature* this is a,b (RLE) -> careful below
    "zigzag": "acac",
    "fall":   "dcba",
}
# use RLE'd signatures so each concept is genuinely scale-free
CONCEPTS = {k: "".join(c for i, c in enumerate(v) if i == 0 or v[i-1] != c)
            for k, v in CONCEPTS.items()}


def rle(seq):
    return "".join(c for i, c in enumerate(seq) if i == 0 or seq[i-1] != c)


def featvec(symbols):
    """unigram + bigram counts over the alphabet, L2-normalized (graded -> partial)."""
    v = np.zeros(A + A * A)
    for c in symbols:
        if c in AI: v[AI[c]] += 1.0
    for a, b in zip(symbols, symbols[1:]):
        if a in AI and b in AI: v[A + AI[a] * A + AI[b]] += 1.0
    n = np.linalg.norm(v)
    return v / n if n > 0 else v


# the "matrix": one row per concept (his W) — built from the scale-free signatures
names = list(CONCEPTS)
W = np.array([featvec(CONCEPTS[n]) for n in names])          # (concepts, features)
EXACT = {n: CONCEPTS[n] for n in names}


def make_instance(sig, max_scale, noise):
    """expand each symbol to a random run length (SCALE), then corrupt (NOISE)."""
    seq = "".join(c * int(rng.integers(1, max_scale + 1)) for c in sig)
    s = list(seq)
    for i in range(len(s)):
        if rng.random() < noise:
            s[i] = ALPHABET[int(rng.integers(0, A))]
    return "".join(s)


def recognize(raw, mode):
    if mode == "exact":
        return next((n for n in names if EXACT[n] == raw), None)
    sym = rle(raw)                                          # SCALE removed
    if mode == "scaled":
        return next((n for n in names if EXACT[n] == sym), None)
    x = featvec(sym)                                        # PARTIAL-friendly
    scores = W @ x                                          # the matrix match
    return names[int(scores.argmax())]


def main():
    print("concepts (scale-free signatures):", CONCEPTS)
    print("=" * 64)
    print(f"  {'noise':>6} | {'exact':>8}{'scaled':>9}{'partial+scaled':>16}")
    print("  " + "-" * 48)
    for noise in (0.0, 0.1, 0.2, 0.3):
        acc = {"exact": 0, "scaled": 0, "partial": 0}
        N = 3000
        for _ in range(N):
            true = names[int(rng.integers(0, len(names)))]
            raw = make_instance(CONCEPTS[true], max_scale=4, noise=noise)
            acc["exact"]   += (recognize(raw, "exact")  == true)
            acc["scaled"]  += (recognize(raw, "scaled") == true)
            acc["partial"] += (recognize(raw, "partial")== true)
        print(f"  {noise:>6.1f} | {acc['exact']/N:>8.3f}{acc['scaled']/N:>9.3f}"
              f"{acc['partial']/N:>16.3f}")
    print("  " + "-" * 48)

    print("\n  example match-numbers (a scaled+noisy 'ramp' instance):")
    raw = make_instance(CONCEPTS["ramp"], max_scale=4, noise=0.15)
    x = featvec(rle(raw)); scores = W @ x
    order = np.argsort(-scores)
    print(f"    raw input: {raw!r}  -> RLE: {rle(raw)!r}")
    for j in order:
        print(f"      {names[j]:<8} {scores[j]*100:5.1f}%")
    print("  READ: exact dies as soon as scale>1; scaled handles scale but not")
    print("  noise; partial+scaled degrades gracefully under both. The % is the")
    print("  graded match the recursion would carry upward.")


if __name__ == "__main__":
    main()
