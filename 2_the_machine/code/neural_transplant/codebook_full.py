"""
CODEBOOK FULL — fix the two harness bugs the K-sweep exposed:
  (1) data starvation: use ALL 50000 CIFAR train images (was 10000)
  (2) lens rank-deficiency: regularized SHRINKAGE LDA (solver='eigen') so the
      lens survives high-dim codebook features instead of cratering.
Question this settles: does the no-backprop codebook climb toward ~0.79 with
data+regularization, or is ~0.7 the real one-layer ceiling?

Run:  PYTHONUTF8=1 python -u codebook_full.py
"""
import time, numpy as np, torch
from sklearn.cluster import MiniBatchKMeans
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
from sklearn.linear_model import LogisticRegression
import torchvision as tv
from codebook_net import patches_of, contrast_norm, fit_zca, extract, W, DICT_PATCHES, DEV
from lens_bench import crystal


def load_full():
    tr = tv.datasets.CIFAR10("data", train=True, download=False)
    te = tv.datasets.CIFAR10("data", train=False, download=False)
    return (tr.data.astype(np.float32), np.array(tr.targets),
            te.data.astype(np.float32), np.array(te.targets))


def main():
    print("loading FULL CIFAR-10 (50k train)..."); Xtr, ytr, Xte, yte = load_full()
    rng = np.random.default_rng(0)
    samp = Xtr[rng.choice(len(Xtr), 8000, replace=False)]
    with torch.no_grad():
        pp = contrast_norm(patches_of(torch.from_numpy(samp).to(DEV))).reshape(-1, W*W*3)
        sel = rng.choice(pp.shape[0], DICT_PATCHES, replace=False)
        pp = pp[torch.from_numpy(sel).to(DEV)]
        M, Wz = fit_zca(pp)
        ppw = ((pp - M) @ Wz).cpu().numpy()

    print("=" * 74)
    print("  CODEBOOK FULL on CIFAR-10  (50k imgs, shrinkage lens, NO backprop)")
    print("=" * 74)
    print(f"  {'K':>5}{'feat':>7}{'km_s':>7}{'feat_s':>8}{'linear':>8}{'box+lens':>10}{'inf/1k':>9}")
    print("  " + "-" * 68)
    for K in (512, 1024, 1600):
        t = time.time()
        km = MiniBatchKMeans(K, batch_size=8192, n_init=2, max_iter=150, random_state=0).fit(ppw)
        km_s = time.time() - t
        C = torch.from_numpy(km.cluster_centers_.astype(np.float32)).to(DEV)
        t = time.time()
        with torch.no_grad():
            Ftr = extract(Xtr, M, Wz, C); Fte = extract(Xte, M, Wz, C)
        mu, sd = Ftr.mean(0), Ftr.std(0) + 1e-6
        Ftr, Fte = (Ftr - mu) / sd, (Fte - mu) / sd
        feat_s = time.time() - t
        lin = LogisticRegression(max_iter=1000, C=1.0).fit(Ftr, ytr).score(Fte, yte)
        lda = LDA(solver="eigen", shrinkage="auto").fit(Ftr, ytr)   # REGULARIZED lens
        boxL, _, _, infL = crystal(lda.transform(Ftr), ytr, lda.transform(Fte), yte, splits=0)
        print(f"  {K:>5}{Ftr.shape[1]:>7}{km_s:>7.1f}{feat_s:>8.1f}{lin:>8.3f}{boxL:>10.3f}{infL:>9.2f}")
    print("  " + "-" * 68)
    print("  ref: flat grid 0.28 | ResNet18 encoder box 0.71 +lens 0.83 | Coates-Ng ~0.79 | chance 0.10")


if __name__ == "__main__":
    main()
