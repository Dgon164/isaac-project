"""
Does a ROTATION LENS close the box gap on vision embeddings?
Raw embedding: boxes get 0.71 vs linear 0.84 — the oblique-vs-axis gap.
LDA finds the discriminative directions; rotating into them should make the
classes axis-aligned -> boxes should jump. This is the registration/lens lever
on real data: align first, then the cheap box reader nearly matches the linear.
"""
import numpy as np, torch, torchvision as tv
from torchvision import transforms as T
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
from sklearn.linear_model import LogisticRegression
from vision_crystal import crystal, embed, DEV

net = tv.models.resnet18(weights=tv.models.ResNet18_Weights.IMAGENET1K_V1)
feat = torch.nn.Sequential(*list(net.children())[:-1]).to(DEV)
tf = T.Compose([T.Resize(224), T.ToTensor(),
                T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
tr = tv.datasets.CIFAR10("data", train=True, download=False, transform=tf)
te = tv.datasets.CIFAR10("data", train=False, download=False, transform=tf)
Etr, ytr, _ = embed(feat, tr, 12000)
Ete, yte, _ = embed(feat, te, 4000)
torch.cuda.empty_cache()

print("=" * 56)
print("  ROTATION LENS on vision embeddings (CIFAR/ResNet18)")
print("=" * 56)
lin = LogisticRegression(max_iter=1000).fit(Etr, ytr).score(Ete, yte)
raw, _ = crystal(Etr, ytr, Ete, yte, splits=0)

lda = LDA().fit(Etr, ytr)                       # the learned aligner (rotation)
Ltr, Lte = lda.transform(Etr), lda.transform(Ete)
lens, _ = crystal(Ltr, ytr, Lte, yte, splits=0)
lensv, _ = crystal(Ltr, ytr, Lte, yte, splits=5)

print(f"  linear probe (oblique, the target) : {lin:.3f}")
print(f"  crystal on RAW embedding           : {raw:.3f}   <- axis-aligned, trails")
print(f"  crystal AFTER rotation lens (LDA)  : {lens:.3f}   <- aligned then boxed")
print(f"  crystal after lens + variants      : {lensv:.3f}")
print("=" * 56)
print("  If lens >> raw and ~ linear: alignment was the whole gap. The cheap")
print("  box reader matches the linear head once you rotate first. Registration.")
