"""
CODEBOOK K-SWEEP — how high does the no-backprop number go as the visual
vocabulary grows? Bigger K = more patch-meanings = the performance knob.
Reports linear ceiling AND box+LDA-lens (the shippable legible head) per K,
with the k-means "training" time. All closed-form / clustering; zero backprop.

Run:  PYTHONUTF8=1 python -u codebook_sweep.py
"""
import time, numpy as np, torch
from sklearn.cluster import MiniBatchKMeans
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
from codebook_net import load_cifar, patches_of, contrast_norm, fit_zca, extract, W, DICT_PATCHES, DEV
from lens_bench import crystal, linear_on


def main():
    Xtr, ytr, Xte, yte = load_cifar()
    rng = np.random.default_rng(0)
    samp = Xtr[rng.choice(len(Xtr), 4000, replace=False)]
    with torch.no_grad():
        pp = contrast_norm(patches_of(torch.from_numpy(samp).to(DEV))).reshape(-1, W*W*3)
        sel = rng.choice(pp.shape[0], DICT_PATCHES, replace=False)
        pp = pp[torch.from_numpy(sel).to(DEV)]
        M, Wz = fit_zca(pp)
        ppw = ((pp - M) @ Wz).cpu().numpy()

    print("=" * 70)
    print("  CODEBOOK K-SWEEP on CIFAR-10  (vocabulary size = the accuracy knob)")
    print("=" * 70)
    print(f"  {'K':>5}{'feat':>7}{'kmeans_s':>10}{'linear':>9}{'box+lens':>10}{'inf/1k':>9}")
    print("  " + "-" * 64)
    for K in (256, 512, 1024, 1600):
        t = time.time()
        km = MiniBatchKMeans(K, batch_size=4096, n_init=2, max_iter=120, random_state=0).fit(ppw)
        km_s = time.time() - t
        C = torch.from_numpy(km.cluster_centers_.astype(np.float32)).to(DEV)
        with torch.no_grad():
            Ftr = extract(Xtr, M, Wz, C); Fte = extract(Xte, M, Wz, C)
        mu, sd = Ftr.mean(0), Ftr.std(0) + 1e-6
        Ftr, Fte = (Ftr - mu) / sd, (Fte - mu) / sd
        lin = linear_on(Ftr, ytr, Fte, yte)
        lda = LDA().fit(Ftr, ytr)
        boxL, _, _, infL = crystal(lda.transform(Ftr), ytr, lda.transform(Fte), yte, splits=0)
        print(f"  {K:>5}{Ftr.shape[1]:>7}{km_s:>10.1f}{lin:>9.3f}{boxL:>10.3f}{infL:>9.2f}")
    print("  " + "-" * 64)
    print("  reference: flat grid 0.28 | ResNet18 encoder box 0.71 +lens 0.83 | chance 0.10")
    print("  READ: the climb with K = the performance-vs-train-time curve, no backprop.")


if __name__ == "__main__":
    main()
