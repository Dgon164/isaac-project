"""
CONDENSATION SCALING — the user's remembered claim, measured.

  "we just accepted the O(n2) because as it grew, it also condensed...
   the more it compresses and generalizes, the less things it needs to
   compare against absolutely."

Prediction: a new item is compared against IDEALS (concepts), not against
every prior instance. Concept count saturates at the domain's true structure
(here: 12 planted prototypes), so per-item cost goes ~CONSTANT while naive
all-pairs grows linearly per item (quadratically in total). Absorption also
SHARPENS the ideals (distributions tighten as they absorb), so recognition
improves while cost flattens — growth causes condensation causes cheapness.

Discipline kept: a new concept is declared only when the best ideal fails to
beat a permuted-input null (no fixed similarity threshold).
Instances are still stored raw (everything enters, nothing leaves) —
condensation is about COMPARISON, not about forgetting.
"""
import numpy as np

rng = np.random.default_rng(17)
G, D, BINS = 12, 40, 8
protos = rng.random((G, D))


def item(g):
    return np.clip(protos[g] + rng.normal(0, 0.12, D), 0, 1)


class Ideal:
    """A concept = per-dim observed histogram (mini proximity doors)."""

    def __init__(self, x):
        self.counts = np.ones((D, BINS))
        self.labels = []
        self.add(x, None)

    def add(self, x, g):
        idx = np.minimum((x * BINS).astype(int), BINS - 1)
        self.counts[np.arange(D), idx] += 1
        if g is not None:
            self.labels.append(g)

    def loglik(self, x):
        idx = np.minimum((x * BINS).astype(int), BINS - 1)
        p = self.counts / self.counts.sum(axis=1, keepdims=True)
        return float(np.log(p[np.arange(D), idx]).mean())


def condensing(n, checkpoints):
    ideals, comps, out = [], 0, []
    for t in range(n):
        g = int(rng.integers(G))
        x = item(g)
        if ideals:
            scores = [I.loglik(x) for I in ideals]
            nulls = [I.loglik(rng.permutation(x)) for I in ideals]
            comps += 2 * len(ideals)
            best = int(np.argmax(scores))
            if scores[best] > max(nulls):        # beats the permuted null
                ideals[best].add(x, g)
            else:
                ideals.append(Ideal(x)); ideals[-1].labels = [g]
        else:
            ideals.append(Ideal(x)); ideals[-1].labels = [g]
        if t + 1 in checkpoints:
            purity = np.mean([np.bincount(I.labels).max() / len(I.labels)
                              for I in ideals if I.labels])
            out.append((t + 1, comps, len(ideals),
                        2 * len(ideals), purity))
    return out


def main():
    print("=" * 76)
    print("CONDENSATION — naive all-pairs vs compare-against-ideals")
    print("=" * 76)
    n = 8000
    cps = [250, 500, 1000, 2000, 4000, 8000]
    rows = condensing(n, cps)
    print(f"\n{'n':>6} {'naive total':>13} {'condensed':>10} {'saving':>8} "
          f"{'concepts':>9} {'per-item':>9} {'purity':>7}")
    for (m, comps, k, per, pur) in rows:
        naive = m * (m - 1) // 2
        print(f"{m:>6} {naive:>13,} {comps:>10,} {naive/max(comps,1):>7.0f}x "
              f"{k:>9} {per:>9} {pur*100:>6.1f}%")
    print("\nper-item = comparisons a NEW item needs right now (2 x concepts:"
          "\nreal + its null). Naive per-item at n=8000 would be 7,999.")


if __name__ == "__main__":
    main()
