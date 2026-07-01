"""
LENS BENCH — the lens is the scalability lever.

Thesis (user's intuition): the aligner and scalability are the same coin.
A good lens rotates classes axis-aligned (accuracy) AND projects 512 -> C-1
dims (the box scan O(n*C*D) loses its D). So a better lens is a SMALLER, faster
scan. This bench measures BOTH per lens, on frozen-ResNet18 CIFAR-10 embeddings:

    lens | out-dims | box-acc | linear-on-lens | fit ms | infer ms/1k | concepts

It also answers the open research fork: how much of the lens can be found
WITHOUT labels (the "auto" lens)? PCA/ICA/whitening/bolted-random = unsupervised
candidates; LDA = the supervised reference. The gap between them = how much
supervision the alignment actually needs.

Run:  PYTHONUTF8=1 python -u lens_bench.py
Embeddings are cached to emb_cache.npz after the first (GPU) run.
"""
import os, time, numpy as np

CACHE = "emb_cache.npz"
NTR, NTE = 12000, 4000


# ---------- embeddings (cache once) ----------
def get_embeddings():
    if os.path.exists(CACHE):
        d = np.load(CACHE)
        print(f"loaded cached embeddings {d['Etr'].shape} from {CACHE}")
        return d["Etr"], d["ytr"], d["Ete"], d["yte"]
    import torch, torchvision as tv
    from torchvision import transforms as T
    DEV = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"embedding CIFAR-10 through frozen ResNet18 on {DEV} (one-time)...")
    net = tv.models.resnet18(weights=tv.models.ResNet18_Weights.IMAGENET1K_V1)
    feat = torch.nn.Sequential(*list(net.children())[:-1]).to(DEV).eval()
    tf = T.Compose([T.Resize(224), T.ToTensor(),
                    T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
    tr = tv.datasets.CIFAR10("data", train=True, download=False, transform=tf)
    te = tv.datasets.CIFAR10("data", train=False, download=False, transform=tf)

    def emb(ds, n):
        idx = np.random.default_rng(0).choice(len(ds), n, replace=False)
        xs, ys = [], []
        loader = torch.utils.data.DataLoader([ds[i] for i in idx], batch_size=256)
        with torch.no_grad():
            for xb, yb in loader:
                h = feat(xb.to(DEV)).squeeze(-1).squeeze(-1)
                xs.append(h.cpu().numpy()); ys.append(yb.numpy())
        return np.concatenate(xs), np.concatenate(ys)

    t = time.time()
    Etr, ytr = emb(tr, NTR); Ete, yte = emb(te, NTE)
    print(f"  embedded in {time.time()-t:.0f}s; caching -> {CACHE}")
    np.savez(CACHE, Etr=Etr, ytr=ytr, Ete=Ete, yte=yte)
    return Etr, ytr, Ete, yte


# ---------- the box crystal (axis-aligned reader) ----------
LOW, HIGH = -7, 8

def quantize(X, lo=None, hi=None):
    if lo is None: lo, hi = X.min(0), X.max(0)
    rng = np.where(hi - lo == 0, 1, hi - lo)
    return np.clip(np.round((X - lo) / rng * (HIGH - LOW) + LOW), LOW, HIGH), lo, hi

def mkbox(o, m=1.5):
    return np.percentile(o, 1, 0) - m, np.percentile(o, 95, 0) + m, np.median(o, 0)

def score(Xq, LO, HI, MED, chunk=2000):
    n, D = Xq.shape; den = D * (HIGH - LOW) + 1.0; out = np.empty((n, LO.shape[0]))
    for i in range(0, n, chunk):
        a = Xq[i:i+chunk][:, None, :]; inr = (a >= LO[None]) & (a <= HI[None])
        out[i:i+chunk] = inr.sum(2) - (np.abs(a - MED[None]) * inr).sum(2) / den
    return out

def per_label(S, LAB, labels):
    o = np.full((S.shape[0], len(labels)), -1e18)
    for j, l in enumerate(labels):
        m = LAB == l
        if m.any(): o[:, j] = S[:, m].max(1)
    return np.array(labels)[o.argmax(1)]

def crystal(Xtr, ytr, Xte, yte, splits=0):
    """Returns (test_acc, n_concepts, fit_seconds, infer_ms_per_1k)."""
    t0 = time.time()
    Qtr, lo, hi = quantize(Xtr); Qte, _, _ = quantize(Xte, lo, hi)
    labels = sorted(np.unique(ytr).tolist())
    LO, HI, MED, LAB = [], [], [], []
    for c in labels:
        l, h, m = mkbox(Qtr[ytr == c]); LO.append(l); HI.append(h); MED.append(m); LAB.append(c)
    LO, HI, MED, LAB = map(np.array, (LO, HI, MED, LAB))
    for _ in range(splits):
        pred = per_label(score(Qtr, LO, HI, MED), LAB, labels)
        al, ah, am, alab = [], [], [], []
        for tl in labels:
            for cl in labels:
                if tl != cl and ((ytr == tl) & (pred == cl)).sum() >= 10:
                    o = Qtr[(ytr == tl) & (pred == cl)]; l, h, m = mkbox(o)
                    al.append(l); ah.append(h); am.append(m); alab.append(tl)
        if not al: break
        LO = np.vstack([LO, al]); HI = np.vstack([HI, ah]); MED = np.vstack([MED, am]); LAB = np.concatenate([LAB, alab])
    fit_s = time.time() - t0
    t1 = time.time()
    pred = per_label(score(Qte, LO, HI, MED), LAB, labels)
    infer_ms = (time.time() - t1) * 1000.0 / (len(yte) / 1000.0)
    return (pred == yte).mean(), len(LAB), fit_s, infer_ms


# ---------- the lenses ----------
def make_lenses(Etr, ytr, Ete):
    """Each lens -> (name, supervised?, Ltr, Lte). Closed-form / no gradient training."""
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
    from sklearn.decomposition import PCA, FastICA
    C = len(np.unique(ytr)); k = C - 1
    out = []

    # 0) no lens — raw 512-d (the axis-misaligned baseline)
    out.append(("none (raw 512)", False, Etr, Ete))

    # 1) PCA to C-1 dims — unsupervised, VARIANCE directions
    p = PCA(n_components=k, random_state=0).fit(Etr)
    out.append((f"PCA-{k} (unsup)", False, p.transform(Etr), p.transform(Ete)))

    # 2) PCA to 50 dims — unsupervised, more headroom
    p50 = PCA(n_components=50, random_state=0).fit(Etr)
    out.append(("PCA-50 (unsup)", False, p50.transform(Etr), p50.transform(Ete)))

    # 3) Whitened PCA-50 then ICA to C-1 — unsupervised, INDEPENDENT directions
    try:
        ica = FastICA(n_components=k, random_state=0, max_iter=400).fit(p50.transform(Etr))
        out.append((f"ICA-{k} (unsup)", False, ica.transform(p50.transform(Etr)), ica.transform(p50.transform(Ete))))
    except Exception as e:
        print(f"  (ICA skipped: {e})")

    # 4) Bolted random reservoirs — unsupervised ensemble (your "bolting nets")
    rng = np.random.default_rng(0)
    R = rng.standard_normal((Etr.shape[1], 64)) / np.sqrt(Etr.shape[1])
    Rtr = np.maximum(Etr @ R, 0); Rte = np.maximum(Ete @ R, 0)   # one relu reservoir, 64-d
    out.append(("reservoir-64 (unsup)", False, Rtr, Rte))

    # 5) LDA to C-1 dims — SUPERVISED reference (the validated win)
    lda = LDA().fit(Etr, ytr)
    out.append((f"LDA-{k} (SUP)", True, lda.transform(Etr), lda.transform(Ete)))

    # 6) PCA-50 -> LDA — denoise first, then discriminate (cheap supervised)
    lda2 = LDA().fit(p50.transform(Etr), ytr)
    out.append(("PCA50->LDA (SUP)", True, lda2.transform(p50.transform(Etr)), lda2.transform(p50.transform(Ete))))
    return out


def linear_on(Ltr, ytr, Lte, yte):
    from sklearn.linear_model import LogisticRegression
    return LogisticRegression(max_iter=500).fit(Ltr, ytr).score(Lte, yte)


def main():
    Etr, ytr, Ete, yte = get_embeddings()
    print("=" * 78)
    print("  LENS BENCH — accuracy AND scan cost per lens (CIFAR-10 / ResNet18)")
    print("=" * 78)
    print(f"  {'lens':<22}{'dims':>5}{'box':>7}{'+var':>7}{'linear':>8}{'fit_s':>7}{'inf/1k':>8}{'conc':>6}")
    print("  " + "-" * 74)
    for name, sup, Ltr, Lte in make_lenses(Etr, ytr, Ete):
        acc0, n0, fit0, inf0 = crystal(Ltr, ytr, Lte, yte, splits=0)
        accv, nv, _, _ = crystal(Ltr, ytr, Lte, yte, splits=5)
        lin = linear_on(Ltr, ytr, Lte, yte)
        tag = "*" if sup else " "
        print(f"{tag} {name:<22}{Ltr.shape[1]:>5}{acc0:>7.3f}{accv:>7.3f}{lin:>8.3f}{fit0:>7.2f}{inf0:>8.2f}{n0:>6}")
    print("  " + "-" * 74)
    print("  * = supervised (uses labels).  box = crystal splits=0; +var = splits=5.")
    print("  READ: a good lens collapses dims (smaller/faster scan) AND lifts box acc.")
    print("  The unsup<->SUP box-acc gap = how much supervision the alignment needs.")


if __name__ == "__main__":
    main()
