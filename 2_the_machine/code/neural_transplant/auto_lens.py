"""
AUTO LENS — can the registration be found WITHOUT labels?

lens_bench located the wall: unsupervised lenses (PCA/ICA) PRESERVE the signal
(linear-on-PCA50 = 0.834) but don't REGISTER it to the axes, so the box reader
can't eat it (box-on-PCA50 = 0.659). LDA registers because it uses labels.

Two ways to get registration without (full) labels:
  A) PSEUDO-LABELS: k-means clusters the embedding (no labels) -> treat clusters
     as pseudo-classes -> LDA on pseudo-labels = a rotation that axis-separates
     the CLUSTERS. If the encoder already clusters by class, this ~= real LDA.
     This is the "crystallizer finds the alignment itself" test.
  B) SEMI-SUPERVISED: fit LDA on a FRACTION of the true labels. Maps exactly how
     much supervision the registration needs to fire.

The box classifier downstream always uses the true training labels (it's a
classifier; you have training labels). The question is only whether the LENS can
be found cheaply/without them.

Run:  PYTHONUTF8=1 python -u auto_lens.py   (needs emb_cache.npz from lens_bench)
"""
import numpy as np
from lens_bench import get_embeddings, crystal, linear_on
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from scipy.optimize import linear_sum_assignment


def cluster_purity(ytrue, clusters):
    """Best label<->cluster matching accuracy (how well clusters = classes)."""
    labs = np.unique(ytrue); cl = np.unique(clusters)
    M = np.zeros((len(labs), len(cl)))
    for i, l in enumerate(labs):
        for j, c in enumerate(cl):
            M[i, j] = ((ytrue == l) & (clusters == c)).sum()
    r, c = linear_sum_assignment(-M)
    return M[r, c].sum() / len(ytrue)


def main():
    Etr, ytr, Ete, yte = get_embeddings()
    C = len(np.unique(ytr))
    print("=" * 72)
    print("  AUTO LENS — registration without (full) labels (CIFAR-10/ResNet18)")
    print("=" * 72)

    # reference: full supervised LDA
    lda = LDA().fit(Etr, ytr)
    acc, n, _, inf = crystal(lda.transform(Etr), ytr, lda.transform(Ete), yte)
    print(f"  reference  LDA-{C-1} (full labels)        box {acc:.3f}   inf {inf:.2f}ms/1k")
    print("  " + "-" * 68)

    # --- A) pseudo-label lens: k-means -> LDA on cluster ids ---
    print("  A) PSEUDO-LABEL lens  (k-means clusters -> LDA, NO class labels):")
    P = PCA(n_components=50, random_state=0).fit(Etr)        # denoise before clustering
    Ptr, Pte = P.transform(Etr), P.transform(Ete)
    for K in (C, 2 * C, 5 * C):
        km = KMeans(n_clusters=K, n_init=4, random_state=0).fit(Ptr)
        pur = cluster_purity(ytr, km.labels_)
        plda = LDA().fit(Ptr, km.labels_)                   # rotate to separate CLUSTERS
        Ltr, Lte = plda.transform(Ptr), plda.transform(Pte)
        acc, n, _, inf = crystal(Ltr, ytr, Lte, yte)        # boxes still on TRUE labels
        lin = linear_on(Ltr, ytr, Lte, yte)
        print(f"     K={K:<3} dims={Ltr.shape[1]:<3} purity={pur:.3f}  box {acc:.3f}  linear {lin:.3f}")

    # --- B) semi-supervised: LDA on a fraction of true labels ---
    print("  B) SEMI-SUPERVISED lens  (LDA on a FRACTION of true labels):")
    rng = np.random.default_rng(0)
    for frac in (0.01, 0.02, 0.05, 0.1, 0.25, 1.0):
        m = rng.random(len(ytr)) < frac
        if len(np.unique(ytr[m])) < C:   # ensure all classes present
            m[:] = False
            for c in np.unique(ytr):
                idx = np.where(ytr == c)[0]
                m[rng.choice(idx, max(2, int(frac * len(idx))), replace=False)] = True
        sld = LDA().fit(Etr[m], ytr[m])
        acc, n, _, _ = crystal(sld.transform(Etr), ytr, sld.transform(Ete), yte)
        print(f"     frac={frac:<5} (~{m.sum():>5} labeled)   box {acc:.3f}")

    print("  " + "-" * 68)
    print("  READ: pseudo-label box ~ full-LDA box  => registration is FREE (encoder")
    print("  already clusters by class).  Semi-sup curve => min labels to register.")


if __name__ == "__main__":
    main()
