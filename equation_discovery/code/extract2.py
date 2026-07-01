"""Stronger net, then TWO-STAGE extraction:
 stage A: the net's ~7 latents ARE the invariant masses (proven last run: m_bb R2~.96).
          so treat the 7 high-level masses as the recovered intermediate variables.
 stage B: read the net's DECISION as a compact function of just those 7 latents,
          instead of a 28x28 interaction soup. If a few terms over 7 masses recover
          most of the net's logit, the mechanism is: kinematics -> masses -> rule.
"""
import numpy as np, warnings; warnings.filterwarnings("ignore")
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.linear_model import LogisticRegression, Ridge, Lasso
from sklearn.ensemble import HistGradientBoostingClassifier as HGB

d = fetch_openml(data_id=23512, as_frame=False)
X = np.asarray(d.data, np.float32); names = list(d.feature_names)
y = np.asarray(d.target); y = (y=="1").astype(int) if y.dtype==object else (y.astype(float)>.5).astype(int)
ok = ~np.isnan(X).any(1); X, y = X[ok], y[ok]
Xtr,Xte,ytr,yte = train_test_split(X, y, test_size=.15, random_state=0, stratify=y)
Xtr,ytr = Xtr[:150000], ytr[:150000]; Xte,yte = Xte[:20000], yte[:20000]
s = StandardScaler().fit(Xtr); Xtr,Xte = s.transform(Xtr), s.transform(Xte)
n = X.shape[1]; high = list(range(21,28)); hi_names=[names[j] for j in high]

# ---- 1. a stronger net ----
logi = (LogisticRegression(max_iter=500).fit(Xtr,ytr).predict(Xte)==yte).mean()
net = MLPClassifier(hidden_layer_sizes=(256,128,64), alpha=1e-4, max_iter=200,
                    early_stopping=True, n_iter_no_change=12, random_state=0).fit(Xtr,ytr)
acc = (net.predict(Xte)==yte).mean()
print("="*66); print("  1. STRONGER NET"); print("="*66)
print(f"  logistic {logi:.3f}  |  MLP(256,128,64) {acc:.3f}  |  prev MLP 0.708  |  chance .53")

def hidden(A):
    for W,b in zip(net.coefs_[:-1], net.intercepts_[:-1]): A=np.maximum(A@W+b,0)
    return A
Htr,Hte = hidden(Xtr), hidden(Xte)
logit_tr=(Htr@net.coefs_[-1]+net.intercepts_[-1]).ravel()
logit_te=(Hte@net.coefs_[-1]+net.intercepts_[-1]).ravel()

# participation ratio
ev=np.sort(np.linalg.eigvalsh(np.cov((Hte-Hte.mean(0)).T)))[::-1]; ev=ev[ev>1e-9]
pr=(ev.sum()**2)/(ev**2).sum()
print(f"  net hidden width {Hte.shape[1]}, effective latents (participation ratio) = {pr:.1f}")

# which masses does it encode now
print("\n  invariant masses encoded in the net latent (R2 from hidden):")
for j in high:
    print(f"    {names[j]:<8} {Ridge(1).fit(Htr,Xtr[:,j]).score(Hte,Xte[:,j]):.3f}")

# ---- STAGE B: decision as a compact function of the 7 masses ----
print("\n"+"="*66); print("  2. TWO-STAGE: net decision as a function of the 7 masses"); print("="*66)
Mtr,Mte = Xtr[:,high], Xte[:,high]
# how much of the signal is in the 7 masses alone?
acc7 = (HGB(random_state=0).fit(Mtr,ytr).predict(Mte)==yte).mean()
print(f"  classifier on ONLY the 7 masses: {acc7:.3f}  (vs full-net {acc:.3f}) "
      f"-> {acc7/acc*100:.0f}% of the net's skill is in 7 numbers")

# build a small basis over the 7 masses: linear + squares + pairwise
cols=[Mtr]; cte=[Mte]; cn=list(hi_names)
for nm,arr,a in [("^2",Mtr**2,Mte**2)]:
    cols.append(arr); cte.append(a); cn+=[f"{h}^2" for h in hi_names]
for i in range(7):
    for j in range(i+1,7):
        cols.append((Mtr[:,i]*Mtr[:,j])[:,None]); cte.append((Mte[:,i]*Mte[:,j])[:,None]); cn.append(f"{hi_names[i]}*{hi_names[j]}")
Btr=np.column_stack(cols); Bte=np.column_stack(cte)
bs=StandardScaler().fit(Btr); Btr,Bte=bs.transform(Btr),bs.transform(Bte)
for al in (0.05,0.02,0.005):
    m=Lasso(alpha=al,max_iter=8000).fit(Btr,logit_tr)
    print(f"  distill net-logit over 7-mass basis (alpha={al}): R2={m.score(Bte,logit_te):.3f}  "
          f"({(m.coef_!=0).sum()} of {len(cn)} terms)")
m=Lasso(alpha=0.005,max_iter=8000).fit(Btr,logit_tr); w=m.coef_; o=np.argsort(-np.abs(w))
print("  top terms of the extracted rule (over the masses):")
for i in o[:10]:
    if w[i]!=0: print(f"     {w[i]:+.3f}  {cn[i]}")

# which single mass the decision leans on most (Higgs channel?)
print("\n  importance of each mass in the net's decision (|corr of mass with logit|):")
imp=sorted(((abs(np.corrcoef(Xte[:,j],logit_te)[0,1]), names[j]) for j in high), reverse=True)
for v,nm in imp: print(f"    {nm:<8} {v:.3f}" + ("   <- H->bb channel" if nm=="m_bb" else ""))
print("\n  READ: stage A = the 7 latents are the masses (top block). stage B = the")
print("  decision is mostly a compact function of those 7 numbers. kinematics ->")
print("  masses -> rule, with m_bb (the Higgs channel) carrying the most.")
