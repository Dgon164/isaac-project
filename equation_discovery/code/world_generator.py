"""
world_generator.py  —  the dataset "encoding" used across the discovery benchmarks.

THE GENERATIVE MODEL (how every synthetic world is built):
  - There are K hidden "things" (causes / sources / particles).
  - Each thing k is ENCODED as a FINGERPRINT: a row W[k] over the D sensors saying
    WHICH sensors it touches (a random subset) and HOW STRONGLY (per-sensor gains).
  - Each event (row of data) draws a RANDOM SUBSET of things to be present (Z), each
    at a RANDOM activation MAGNITUDE (mag).
  - The sensors observe the SUM of whatever is present, plus per-sensor noise:

        X = (Z * mag) @ W  +  noise          # events x sensors

  Ground truth (W, Z, mag, and the per-thing properties) is returned so any method can
  be GRADED: "did it recover thing k's fingerprint W[k]?"

Everything is deterministic given `seed`, so datasets are exactly reproducible.

Functions:
  make_world(...)      basic world: random strengths, random sensor counts.
  make_direct_indirect(...)  strength inversely tied to sensor count
                       (strong+few = direct measurement; weak+many = indirect/diffuse).
  add_conservation_laws(...)  overlay low-variance constraints (a sensor = sum of others)
                       — the "quiet" structure type the min-variance specialist reads.
"""
import numpy as np


def make_world(K=20, D=50, N=6000, noise=1.0,
               strength_range=(0.3, 2.0), nsens_range=(3, 16),
               freq_range=(0.10, 0.60), mag_range=(0.5, 1.5), seed=0):
    """Basic world. Returns dict with X (observed) and the ground truth.

    K, D, N        : #things, #sensors, #events
    noise          : per-sensor gaussian noise std
    strength_range : each thing's overall loudness is drawn uniformly here
    nsens_range    : each thing touches this many sensors (random subset)
    freq_range     : each thing is present in an event with this probability
    mag_range      : activation magnitude when a thing is present
    """
    rng = np.random.default_rng(seed)
    strength = rng.uniform(*strength_range, K)              # how loud each thing is
    nsens    = rng.integers(nsens_range[0], nsens_range[1], K)   # how many sensors it touches
    freq     = rng.uniform(*freq_range, K)                  # how often it shows up

    # ENCODE each thing as a sparse fingerprint over the sensors
    W = np.zeros((K, D))
    for k in range(K):
        sensors = rng.choice(D, nsens[k], replace=False)
        W[k, sensors] = strength[k] * rng.uniform(0.5, 1.5, nsens[k])

    # build events: random presence x random magnitude, summed onto sensors, + noise
    Z   = (rng.random((N, K)) < freq).astype(float)         # which things are present
    mag = rng.uniform(*mag_range, (N, K))                   # activation magnitude when present
    X   = np.clip((Z * mag) @ W + rng.normal(0, noise, (N, D)), 0, None)

    return dict(X=X, W=W, Z=Z, mag=mag, strength=strength, nsens=nsens, freq=freq,
                total_signal=strength**2 * nsens)           # detectability ~ total coherent signal


def make_direct_indirect(K=20, D=60, N=6000, noise=1.0, seed=0):
    """Stronger signal -> FEWER sensors (direct measurement); weaker -> MANY (indirect/
    diffuse hidden cause). Tests per-sensor strength vs coherence-across-sensors."""
    rng = np.random.default_rng(seed)
    directness = rng.uniform(0, 1, K)                       # 1 = direct (strong,few), 0 = indirect (weak,many)
    strength = 0.4 + 1.9 * directness                      # weak 0.4  <->  strong 2.3
    nsens    = np.clip((34 - 30 * directness), 3, D).astype(int)   # diffuse 34 <-> concentrated 4
    W = np.zeros((K, D))
    for k in range(K):
        sensors = rng.choice(D, nsens[k], replace=False)
        W[k, sensors] = strength[k] * rng.uniform(0.7, 1.3, nsens[k])
    freq = rng.uniform(0.10, 0.60, K)
    Z   = (rng.random((N, K)) < freq).astype(float)
    mag = rng.uniform(0.5, 1.5, (N, K))
    X   = np.clip((Z * mag) @ W + rng.normal(0, noise, (N, D)), 0, None)
    return dict(X=X, W=W, Z=Z, mag=mag, strength=strength, nsens=nsens, freq=freq,
                directness=directness, total_signal=strength**2 * nsens)


def add_conservation_laws(world, n_laws=4, noise=0.05, seed=1):
    """Overlay low-variance CONSTRAINTS: force a sensor = sum of two others, so the
    direction (s_a - s_b - s_c) is ~constant. This is the 'quiet' structure type that
    the min-variance specialist reads (sources are loud; laws are quiet). Returns the
    modified world plus the true law vectors for grading."""
    rng = np.random.default_rng(seed)
    X = world["X"]; D = X.shape[1]; laws = []
    for _ in range(n_laws):
        a, b, c = rng.choice(D, 3, replace=False)
        X[:, a] = X[:, b] + X[:, c] + rng.normal(0, noise, X.shape[0])
        v = np.zeros(D); v[a] = 1; v[b] = -1; v[c] = -1
        laws.append(v / np.linalg.norm(v))
    world["X"] = np.clip(X, 1e-6, None)                    # keep non-negative for NMF
    world["laws"] = np.array(laws)
    return world


if __name__ == "__main__":
    w = make_world(seed=0)
    print("basic world:", w["X"].shape, "X = (presence*mag) @ fingerprints + noise")
    print("  ground truth available:", [k for k in w if k != "X"])
    print("  detectability is governed by total_signal = strength^2 * #sensors")
    d = make_direct_indirect(seed=0)
    print("\ndirect/indirect world:", d["X"].shape,
          "| direct things:", int((d["directness"] > .5).sum()),
          "indirect:", int((d["directness"] <= .5).sum()))
    wl = add_conservation_laws(make_world(D=30, seed=0), n_laws=4)
    print("\nworld + conservation laws:", wl["X"].shape, "| laws planted:", len(wl["laws"]))
