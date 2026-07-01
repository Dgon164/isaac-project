"""
VISION CRYSTAL — is a vision encoder's FINAL representation box-friendly?

Not feature extraction. We take a frozen pretrained ResNet18's penultimate
512-dim embedding (the fully-formed, class-discriminative representation), and
crystallize it into per-class boxes. Compare the box (crystal) head to a linear
probe and kNN on the same embeddings — and to boxes on RAW PIXELS (the box-
hostile control). Question: did the encoder hand us a box-friendly space?
"""
import time, numpy as np, torch
import torchvision as tv
from torchvision import transforms as T
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier

DEV = "cuda" if torch.cuda.is_available() else "cpu"
LOW, HIGH = -7, 8


# ---- vectorized box classifier (the crystal) ----
def quantize(X, lo=None, hi=None):
    if lo is None: lo, hi = X.min(0), X.max(0)
    rng = np.where(hi - lo == 0, 1, hi - lo)
    return np.clip(np.round((X - lo) / rng * (HIGH - LOW) + LOW), LOW, HIGH), lo, hi

def box(o, m=1.5):
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
    Qtr, lo, hi = quantize(Xtr); Qte, _, _ = quantize(Xte, lo, hi)
    labels = sorted(np.unique(ytr).tolist())
    LO, HI, MED, LAB = [], [], [], []
    for c in labels:
        l, h, m = box(Qtr[ytr == c]); LO.append(l); HI.append(h); MED.append(m); LAB.append(c)
    LO, HI, MED, LAB = map(np.array, (LO, HI, MED, LAB))
    for _ in range(splits):
        pred = per_label(score(Qtr, LO, HI, MED), LAB, labels)
        al, ah, am, alab = [], [], [], []
        for tl in labels:
            for cl in labels:
                if tl != cl and ((ytr == tl) & (pred == cl)).sum() >= 10:
                    o = Qtr[(ytr == tl) & (pred == cl)]; l, h, m = box(o)
                    al.append(l); ah.append(h); am.append(m); alab.append(tl)
        if not al: break
        LO = np.vstack([LO, al]); HI = np.vstack([HI, ah]); MED = np.vstack([MED, am]); LAB = np.concatenate([LAB, alab])
    return (per_label(score(Qte, LO, HI, MED), LAB, labels) == yte).mean(), len(LAB)


def embed(model, ds, n):
    idx = np.random.default_rng(0).choice(len(ds), n, replace=False)
    xs, ys = [], []
    loader = torch.utils.data.DataLoader([ds[i] for i in idx], batch_size=256)
    model.eval()
    with torch.no_grad():
        for xb, yb in loader:
            h = model(xb.to(DEV)).squeeze(-1).squeeze(-1)
            xs.append(h.cpu().numpy()); ys.append(yb.numpy())
    return np.concatenate(xs), np.concatenate(ys), idx


def main():
    print("loading ResNet18 (pretrained) + CIFAR-10...")
    net = tv.models.resnet18(weights=tv.models.ResNet18_Weights.IMAGENET1K_V1)
    feat = torch.nn.Sequential(*list(net.children())[:-1]).to(DEV)  # drop fc -> 512-d
    tf = T.Compose([T.Resize(224), T.ToTensor(),
                    T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
    tr = tv.datasets.CIFAR10("data", train=True, download=True, transform=tf)
    te = tv.datasets.CIFAR10("data", train=False, download=True, transform=tf)

    t = time.time()
    Etr, ytr, itr = embed(feat, tr, 12000)
    Ete, yte, ite = embed(feat, te, 4000)
    torch.cuda.empty_cache()
    print(f"  embeddings {Etr.shape} extracted in {time.time()-t:.0f}s\n")

    print("=" * 60)
    print("  HEADS on the frozen encoder's 512-d FINAL representation")
    print("=" * 60)
    lin = LogisticRegression(max_iter=300).fit(Etr, ytr).score(Ete, yte)
    knn = KNeighborsClassifier(10).fit(Etr, ytr).score(Ete, yte)
    cry0, n0 = crystal(Etr, ytr, Ete, yte, splits=0)
    cry5, n5 = crystal(Etr, ytr, Ete, yte, splits=5)
    print(f"  linear probe (the 'real' head): {lin:.3f}")
    print(f"  kNN-10                        : {knn:.3f}")
    print(f"  CRYSTAL (boxes, general)      : {cry0:.3f}   ({n0} concepts)")
    print(f"  CRYSTAL (boxes + variants)    : {cry5:.3f}   ({n5} concepts)")

    print("\n  CONTROL — boxes on RAW PIXELS (box-hostile):")
    # tiny raw-pixel boxes on a downsized gray image
    def raw(ds, idx):
        g = np.stack([np.asarray(ds.data[i]).mean(2)[::4, ::4].ravel() for i in idx])
        return g / 255.0
    rtr, rte = raw(tr, itr), raw(te, ite)
    cryp, _ = crystal(rtr, ytr, rte, yte, splits=3)
    print(f"  CRYSTAL on raw pixels         : {cryp:.3f}   <- the hostile baseline")

    print("\n" + "=" * 60)
    print("  Read: if crystal ~ linear probe, the encoder's FINAL rep is box-")
    print("  friendly -> a legible, abstaining box head matches the linear one")
    print("  at tiny cost. If crystal ~ raw-pixel, the rep didn't help.")


if __name__ == "__main__":
    main()
