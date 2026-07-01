"""
GRID + RESERVOIR — no encoder at all. Isaac's bet, stripped to the bone.

The idea (user's): skip the learned encoder entirely. Take the raw image,
average-pool it into a coarse GxG grid (spatial, no edge detection, no training),
spray it through a RANDOM reservoir so it's spread out, and read boxes off that.
No gradient descent anywhere. What's the accuracy?

We run it on TWO datasets on purpose:
  - digits  (8x8 handwritten, simple) — grid SHOULD work; shape ~ raw layout
  - CIFAR-10 (natural images)        — grid SHOULD struggle; needs real folds
The boundary between them IS the answer: it shows exactly when you can skip the
encoder and when you can't.

Baselines per setting: raw-grid box, raw-grid linear (the grid's ceiling),
grid->reservoir box (+variants), grid->reservoir linear (reservoir ceiling).

Run:  PYTHONUTF8=1 python -u grid_reservoir.py
"""
import numpy as np
from lens_bench import crystal, linear_on


def grid_pool(imgs, G, gray):
    """imgs: (N,H,W,C) uint8 -> (N, G*G*[1 or C]) average-pooled grid features."""
    N, H, W, C = imgs.shape
    x = imgs.astype(np.float32)
    if gray:
        x = x.mean(3, keepdims=True); C = 1
    bh, bw = H // G, W // G
    x = x[:, :G*bh, :G*bw].reshape(N, G, bh, G, bw, C).mean((2, 4))  # (N,G,G,C)
    return x.reshape(N, -1) / 255.0


def zscore(Xtr, Xte):
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-6
    return (Xtr - mu) / sd, (Xte - mu) / sd


def reservoir(Xtr, Xte, d=1024, n_res=1, seed=0):
    """Random projection + ReLU. n_res>1 = several bolted (concatenated) reservoirs."""
    rng = np.random.default_rng(seed); din = Xtr.shape[1]; tr, te = [], []
    for _ in range(n_res):
        R = rng.standard_normal((din, d)) / np.sqrt(din); b = rng.standard_normal(d) * 0.1
        tr.append(np.maximum(Xtr @ R + b, 0)); te.append(np.maximum(Xte @ R + b, 0))
    return np.hstack(tr), np.hstack(te)


def run(name, Xtr_img, ytr, Xte_img, yte, grids=(4, 8), grays=(True, False)):
    print("=" * 74)
    print(f"  {name}   (chance = {1/len(np.unique(ytr)):.3f},  train {len(ytr)} test {len(yte)})")
    print("=" * 74)
    print(f"  {'grid':>5}{'col':>5}{'feat':>6}  | {'box_raw':>8}{'lin_raw':>8} | "
          f"{'box_res':>8}{'+var':>7}{'lin_res':>8}")
    print("  " + "-" * 68)
    for G in grids:
        for gray in grays:
            gtr = grid_pool(Xtr_img, G, gray); gte = grid_pool(Xte_img, G, gray)
            gtr, gte = zscore(gtr, gte)
            box_raw, _, _, _ = crystal(gtr, ytr, gte, yte, splits=3)
            lin_raw = linear_on(gtr, ytr, gte, yte)
            rtr, rte = reservoir(gtr, gte, d=1024, n_res=1)
            box_res, _, _, _ = crystal(rtr, ytr, rte, yte, splits=0)
            box_resv, _, _, _ = crystal(rtr, ytr, rte, yte, splits=5)
            lin_res = linear_on(rtr, ytr, rte, yte)
            col = "gray" if gray else "rgb"
            print(f"  {G}x{G:<3}{col:>5}{gtr.shape[1]:>6}  | {box_raw:>8.3f}{lin_raw:>8.3f} | "
                  f"{box_res:>8.3f}{box_resv:>7.3f}{lin_res:>8.3f}")
    print("  " + "-" * 68)


def load_digits_imgs():
    from sklearn.datasets import load_digits
    d = load_digits(); X = d.images.astype(np.uint8)        # (1797,8,8), 0..16
    X = (X / 16 * 255).astype(np.uint8)[..., None].repeat(3, 3)  # -> (N,8,8,3) uint8
    y = d.target
    rng = np.random.default_rng(0); idx = rng.permutation(len(y)); cut = int(0.7 * len(y))
    tr, te = idx[:cut], idx[cut:]
    return X[tr], y[tr], X[te], y[te]


def load_cifar_imgs(ntr=12000, nte=4000):
    import torchvision as tv
    tr = tv.datasets.CIFAR10("data", train=True, download=False)
    te = tv.datasets.CIFAR10("data", train=False, download=False)
    rng = np.random.default_rng(0)
    itr = rng.choice(len(tr), ntr, replace=False); ite = rng.choice(len(te), nte, replace=False)
    Xtr = tr.data[itr]; ytr = np.array(tr.targets)[itr]
    Xte = te.data[ite]; yte = np.array(te.targets)[ite]
    return Xtr, ytr, Xte, yte


def main():
    Xtr, ytr, Xte, yte = load_digits_imgs()
    run("DIGITS 8x8 (simple shapes — grid should WORK)", Xtr, ytr, Xte, yte, grids=(4, 8))
    Xtr, ytr, Xte, yte = load_cifar_imgs()
    run("CIFAR-10 (natural images — grid should STRUGGLE)", Xtr, ytr, Xte, yte, grids=(4, 8, 16))
    print("  REFERENCE on CIFAR: frozen ResNet18 encoder box=0.71, +lens=0.83;")
    print("  reservoir-on-encoder=0.55; chance=0.10. The grid has NO encoder at all.")
    print("  READ: digits high (raw layout separates) vs CIFAR low (needs real folds)")
    print("  = exactly when you can skip the encoder and when you cannot.")


if __name__ == "__main__":
    main()
