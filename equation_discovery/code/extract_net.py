"""The info IS in the net. Train one that scores high, then read out WHAT it encoded.

  1. train an MLP -> confirm it beats the linear/box baselines (info is in there)
  2. eig the NET'S hidden layer (not raw X) -> how many real latents it actually uses
  3. probe: regress each physical quantity onto the hidden layer -> WHICH info is in there
  4. distill: sparse-regress the interaction basis onto the net's LOGIT (smooth, denoised
     target) -> the named mechanism, gotten OUT
"""
import numpy as np, warnings; warnings.filterwarnings("ignore")
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.linear_model import LogisticRegression, Ridge

d = fetch_openml(data_id=23512, as_frame=False)
X = np.asarray(d.data, np.float32); names = list(d.feature_names)
y = np.asarray(d.target); y = (y=="1").astype(int) if y.dtype==object else (y.astype(float)>.5).astype(int)
ok = ~np.isnan(X).any(1); X, y = X[ok], y[ok]
Xtr,Xte,ytr,yte = train_test_split(X, y, test_size=.2, random_state=0, stratify=y)
Xtr,ytr = Xtr[:60000], ytr[:60000]; Xte,yte = Xte[:10000], yte[:10000]
s = StandardScaler().fit(Xtr); Xtr,Xte = s.transform(Xtr), s.transform(Xte)
n = X.shape[1]

# ---- 1. train a net that scores high ----
logi = (LogisticRegression(max_iter=500).fit(Xtr,ytr).predict(Xte)==yte).mean()
net = MLPClassifier(hidden_layer_sizes=(128,64), alpha=1e-4, max_iter=120,
                    early_stopping=True, random_state=0).fit(Xtr,ytr)
acc = (net.predict(Xte)==yte).mean()
print("="*66); print("  1. THE INFO IS IN THE NET"); print("="*66)
print(f"  logistic (linear) {logi:.3f}   |   MLP {acc:.3f}   |   chance 0.53")
print(f"  the MLP encodes {acc-logi:+.3f} of accuracy that the linear view cannot see.")

# ---- forward pass to penultimate activations ----
def hidden(Xin):
    a = Xin
    for W,b in zip(net.coefs_[:-1], net.intercepts_[:-1]):
        a = np.maximum(a @ W + b, 0)          # relu
    return a
Htr, Hte = hidden(Xtr), hidden(Xte)
logit_te = Hte @ net.coefs_[-1] + net.intercepts_[-1]; logit_te = logit_te.ravel()
logit_tr = (Htr @ net.coefs_[-1] + net.intercepts_[-1]).ravel()

# ---- 2. eig the NET's representation: how many latents does it really use? ----
Hc = Hte - Hte.mean(0)
ev = np.sort(np.linalg.eigvalsh(np.cov(Hc.T)))[::-1]; ev = ev[ev>1e-9]
cum = np.cumsum(ev)/ev.sum()
pr = (ev.sum()**2)/(ev**2).sum()              # participation ratio = effective # dims
print("\n"+"="*66); print("  2. eig(NET hidden layer) — how many real latents it uses"); print("="*66)
print(f"  hidden width {Hte.shape[1]}, but effective dims (participation ratio) = {pr:.1f}")
print(f"  components for 90% variance: {(cum<.9).sum()+1}   top-5 var: {cum[4]*100:.0f}%")

# ---- 3. probe: WHICH physical quantities live in the hidden layer? ----
print("\n"+"="*66); print("  3. probe — what info the net's latent carries (R2 from hidden)"); print("="*66)
print(f"  {'physical quantity':<26}{'R2 from net latent':>20}")
order = []
for j in range(n):
    r2 = Ridge(1).fit(Htr, Xtr[:,j]).score(Hte, Xte[:,j])
    order.append((r2, names[j]))
for r2,nm in sorted(order, reverse=True):
    tag = " <- high-level mass" if nm.startswith("m_") else ""
    print(f"  {nm:<26}{r2:>20.3f}{tag}")

# ---- 4. distill the net's smooth logit into named terms ----
def expand(A):
    cols=[A, A**2]; cn=list(names)+[f"{c}^2" for c in names]
    for i in range(n):
        for j in range(i+1,n):
            cols.append((A[:,i]*A[:,j])[:,None]); cn.append(f"{names[i]}*{names[j]}")
    return np.column_stack(cols), cn
Etr,cn = expand(Xtr); Ete,_ = expand(Xte)
es = StandardScaler().fit(Etr); Etr,Ete = es.transform(Etr), es.transform(Ete)
# distill against the NET'S logit (smooth) vs against raw labels (noisy)
from sklearn.linear_model import Lasso
dist = Lasso(alpha=0.02, max_iter=5000).fit(Etr, logit_tr)
r2_net = dist.score(Ete, logit_te)
w = dist.coef_; nz=(w!=0).sum(); ordr=np.argsort(-np.abs(w))
print("\n"+"="*66); print("  4. distill the net's LOGIT into a compact named form"); print("="*66)
print(f"  a sparse interaction form recovers R2={r2_net:.3f} of the net's decision "
      f"with {nz} of {len(cn)} terms")
print(f"  top terms the net's mechanism rests on:")
for i in ordr[:12]:
    if w[i]!=0: print(f"     {w[i]:+.3f}  {cn[i]}")
print("\n  READ: (2) how many latents the net truly uses; (3) which physical")
print("  quantities those latents encode; (4) the compact named form extracted")
print("  from the net's denoised decision — the mechanism, gotten OUT.")
