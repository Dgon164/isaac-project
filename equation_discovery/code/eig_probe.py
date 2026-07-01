"""Step 1 of the buddy's pipeline, on real HIGGS: eig(corr(X)) -> how many latents?
Plus the critical test: can a LINEAR latent connect low-level kinematics to the
high-level invariant masses they generate? (Prediction: no -- the link is nonlinear.)
"""
import numpy as np, warnings; warnings.filterwarnings("ignore")
from sklearn.datasets import fetch_openml
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split

d = fetch_openml(data_id=23512, as_frame=False)
X = np.asarray(d.data, np.float32); names = list(d.feature_names)
ok = ~np.isnan(X).any(1); X = X[ok][:30000]
n = X.shape[1]
low  = list(range(21)); high = list(range(21, 28))

# --- step 1: eig(corr) on all features ---
C = np.corrcoef(X.T)
ev = np.sort(np.linalg.eigvalsh(C))[::-1]
print("="*64); print("  STEP 1  eig(corr(X)) — how many real hidden variables?"); print("="*64)
print("  eigenvalue spectrum (all 28 features):")
print("   ", " ".join(f"{v:.2f}" for v in ev))
print(f"  eigenvalues > 1 (Kaiser): {(ev>1).sum()}   "
      f"> 1.5: {(ev>1.5).sum()}   variance in top-5: {ev[:5].sum()/ev.sum()*100:.0f}%")

# --- where do the high-level masses sit in linear correlation? ---
print("\n  each high-level mass: best LINEAR partner & |corr|, and what it is:")
for j in high:
    c = np.array([abs(C[j,k]) if k!=j else 0 for k in range(n)])
    k = int(c.argmax())
    kind = "HIGH-level" if k in high else "low-level"
    print(f"    {names[j]:<8} best={names[k]:<10} |corr|={c[k]:.2f}  ({kind})")

# --- the decisive test: predict each mass from LOW-level only ---
print("\n  predict each high-level mass from the 21 LOW-level kinematics:")
print(f"    {'mass':<8}{'linear R2':>11}{'+products R2':>14}")
Xl = X[:, low]
# pairwise products of low-level (the nonlinear lift)
prods = [Xl[:,a]*Xl[:,b] for a in range(21) for b in range(a,21)]
Xlift = np.column_stack([Xl] + prods)
for j in high:
    yj = X[:, j]
    Atr,Ate,ytr,yte = train_test_split(Xl, yj, test_size=.3, random_state=0)
    r2l = Ridge(1).fit(Atr,ytr).score(Ate,yte)
    Btr,Bte,_,_ = train_test_split(Xlift, yj, test_size=.3, random_state=0)
    r2p = Ridge(1).fit(Btr,ytr).score(Bte,yte)
    print(f"    {names[j]:<8}{r2l:>11.3f}{r2p:>14.3f}")
print("\n  READ: linear R2 = what eig(corr)/PCA can see. +products R2 = what one")
print("  nonlinear lift adds. The gap is the invariant-mass nonlinearity that a")
print("  LINEAR latent cannot represent.")
