"""
CODEBOOK NET — the user's "compression net": one intermediate layer of local
patch-meanings, built by CLUSTERING (no gradient descent), then composed.

The grid failed because it had ZERO intermediate meanings (raw pixels -> box).
The encoder works because it has ~18 learned ones. This builds exactly ONE,
without backprop, the user's way:
  1. chop every image into small w x w patches (the "mini grids")
  2. k-means the patches into a VOCABULARY of K local patterns (visual "glyphs")
     -- this is the intermediate layer, learned WITHOUT labels or gradient descent
  3. describe each image by which vocabulary patterns fire, where (spatial pool)
  4. read the final answer with the box crystal (and a linear probe for ceiling)

This is the Coates & Ng (2011) single-layer unsupervised pipeline: ~79% on
CIFAR-10 with NO gradient descent. Recipe matters -- contrast-normalize patches,
ZCA-whiten, triangle (soft) encoding, 2x2 spatial pooling.

Run:  PYTHONUTF8=1 python -u codebook_net.py
"""
import time, numpy as np, torch
from sklearn.cluster import MiniBatchKMeans
from lens_bench import crystal, linear_on

DEV = "cuda" if torch.cuda.is_available() else "cpu"
W = 6           # patch size
K = 256         # vocabulary size (intermediate meanings)
NTR, NTE = 10000, 4000
DICT_PATCHES = 200000


def load_cifar():
    import torchvision as tv
    tr = tv.datasets.CIFAR10("data", train=True, download=False)
    te = tv.datasets.CIFAR10("data", train=False, download=False)
    rng = np.random.default_rng(0)
    itr = rng.choice(len(tr), NTR, replace=False); ite = rng.choice(len(te), NTE, replace=False)
    Xtr = tr.data[itr].astype(np.float32); ytr = np.array(tr.targets)[itr]
    Xte = te.data[ite].astype(np.float32); yte = np.array(te.targets)[ite]
    return Xtr, ytr, Xte, yte           # images 0..255, (N,32,32,3)


def patches_of(imgs_t):
    """imgs_t: (B,32,32,3) float on DEV -> (B, P, P, w*w*3) raw patches, stride 1."""
    x = imgs_t.permute(0, 3, 1, 2)                              # (B,3,32,32)
    x = x.unfold(2, W, 1).unfold(3, W, 1)                       # (B,3,P,P,w,w)
    B, C, P, _, _, _ = x.shape
    x = x.permute(0, 2, 3, 1, 4, 5).reshape(B, P, P, C * W * W)  # (B,P,P,108)
    return x


def contrast_norm(p):
    """per-patch brightness/contrast normalization (over the 108 dims)."""
    m = p.mean(-1, keepdim=True); v = p.var(-1, keepdim=True)
    return (p - m) / torch.sqrt(v + 10.0)


def fit_zca(P):
    """P: (n,108) normalized patches -> mean, ZCA whitening matrix."""
    M = P.mean(0)
    Pc = P - M
    cov = (Pc.T @ Pc) / Pc.shape[0]
    d, V = torch.linalg.eigh(cov)
    Wz = V @ torch.diag(1.0 / torch.sqrt(d + 0.1)) @ V.T
    return M, Wz


def extract(imgs, M, Wz, C, bs=400):
    """imgs: (N,32,32,3) numpy -> (N, 4*K) triangle-coded, 2x2 spatially pooled."""
    cn = (C * C).sum(1)                                          # (K,)
    feats = []
    for i in range(0, len(imgs), bs):
        bt = torch.from_numpy(imgs[i:i+bs]).to(DEV)
        p = contrast_norm(patches_of(bt))                       # (b,P,P,108)
        b, P, _, D = p.shape
        pw = (p.reshape(-1, D) - M) @ Wz                        # whiten -> (b*P*P,108)
        z2 = (pw * pw).sum(1, keepdim=True) - 2 * pw @ C.T + cn[None]
        z = torch.sqrt(torch.clamp(z2, min=0.0))                # dist to each word
        f = torch.clamp(z.mean(1, keepdim=True) - z, min=0.0)   # triangle (soft) code
        f = f.reshape(b, P, P, -1)
        h = P // 2
        quads = [f[:, :h, :h], f[:, :h, h:], f[:, h:, :h], f[:, h:, h:]]
        pooled = torch.cat([q.sum((1, 2)) for q in quads], 1)   # (b, 4K)
        feats.append(pooled.cpu().numpy())
    return np.concatenate(feats)


def main():
    print("loading CIFAR-10 (raw)..."); Xtr, ytr, Xte, yte = load_cifar()

    # --- learn the vocabulary: cluster patches (no labels, no gradient descent) ---
    t = time.time()
    rng = np.random.default_rng(0)
    samp = Xtr[rng.choice(len(Xtr), 4000, replace=False)]
    with torch.no_grad():
        pp = contrast_norm(patches_of(torch.from_numpy(samp).to(DEV))).reshape(-1, W*W*3)
        sel = rng.choice(pp.shape[0], DICT_PATCHES, replace=False)
        pp = pp[torch.from_numpy(sel).to(DEV)]
        M, Wz = fit_zca(pp)
        ppw = ((pp - M) @ Wz).cpu().numpy()
    km = MiniBatchKMeans(K, batch_size=4096, n_init=3, max_iter=120, random_state=0).fit(ppw)
    C = torch.from_numpy(km.cluster_centers_.astype(np.float32)).to(DEV)
    print(f"  vocabulary of {K} patch-meanings learned (k-means) in {time.time()-t:.0f}s")

    # --- describe every image by its patch-meanings ---
    t = time.time()
    with torch.no_grad():
        Ftr = extract(Xtr, M, Wz, C); Fte = extract(Xte, M, Wz, C)
    mu, sd = Ftr.mean(0), Ftr.std(0) + 1e-6
    Ftr, Fte = (Ftr - mu) / sd, (Fte - mu) / sd
    print(f"  features {Ftr.shape} extracted in {time.time()-t:.0f}s\n")

    # --- read the answer ---
    print("=" * 64)
    print("  CODEBOOK NET on CIFAR-10  (ONE clustered patch layer, NO backprop)")
    print("=" * 64)
    lin = linear_on(Ftr, ytr, Fte, yte)
    box0, n0, _, inf0 = crystal(Ftr, ytr, Fte, yte, splits=0)
    box5, n5, _, _ = crystal(Ftr, ytr, Fte, yte, splits=5)
    # box on the LDA-aligned codebook features (the lens, also no backprop)
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
    lda = LDA().fit(Ftr, ytr)
    boxL, nL, _, infL = crystal(lda.transform(Ftr), ytr, lda.transform(Fte), yte, splits=0)
    print(f"  linear probe on codebook        : {lin:.3f}")
    print(f"  CRYSTAL box (codebook)          : {box0:.3f}   ({n0} concepts, {inf0:.2f}ms/1k)")
    print(f"  CRYSTAL box + variants          : {box5:.3f}   ({n5} concepts)")
    print(f"  CRYSTAL box + LDA lens          : {boxL:.3f}   ({infL:.2f}ms/1k)")
    print("  " + "-" * 60)
    print("  reference: flat grid box=0.28  |  frozen ResNet18 encoder box=0.71,")
    print("  +lens=0.83  |  chance=0.10.  This has ONE unsupervised layer, no backprop.")
    print("  READ: if codebook >> 0.28, the intermediate patch-meaning layer is the")
    print("  bridge from raw grid to encoder -- bought by clustering, not gradient descent.")


if __name__ == "__main__":
    main()
