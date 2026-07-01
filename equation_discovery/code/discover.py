"""THE PRODUCT TEST (not the answer key):
Give the engine ONLY the 21 raw detector channels. Hide the 7 known masses.
Does it DISCOVER hidden quantities on its own -- and are they the masses?
We grade against the withheld masses, but the engine never sees them.

On a NEW system there is no answer key; this proves the engine earns trust where
there IS one, so its output ('look for these N hidden quantities, computed thus')
can be believed where there isn't.
"""
import numpy as np, warnings; warnings.filterwarnings("ignore")
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.linear_model import LogisticRegression, Ridge

d = fetch_openml(data_id=23512, as_frame=False)
X = np.asarray(d.data, np.float32); names = list(d.feature_names)
y = np.asarray(d.target); y=(y=="1").astype(int) if y.dtype==object else (y.astype(float)>.5).astype(int)
ok=~np.isnan(X).any(1); X,y=X[ok],y[ok]
low=list(range(21)); high=list(range(21,28))
Xtr,Xte,ytr,yte = train_test_split(X,y,test_size=.15,random_state=0,stratify=y)
Xtr,ytr=Xtr[:150000],ytr[:150000]; Xte,yte=Xte[:20000],yte[:20000]
s=StandardScaler().fit(Xtr); XtrS,XteS=s.transform(Xtr),s.transform(Xte)

# engine sees ONLY raw channels (low-level). masses are WITHHELD.
Ltr,Lte = XtrS[:,low], XteS[:,low]
Mtr,Mte = XtrS[:,high], XteS[:,high]          # answer key, never shown to the engine

print("="*68); print("  ENGINE INPUT = 21 raw channels only. 7 masses HIDDEN."); print("="*68)
logi_low=(LogisticRegression(max_iter=500).fit(Ltr,ytr).predict(Lte)==yte).mean()
net=MLPClassifier(hidden_layer_sizes=(256,128,64),alpha=1e-4,max_iter=200,
                  early_stopping=True,n_iter_no_change=12,random_state=0).fit(Ltr,ytr)
acc=(net.predict(Lte)==yte).mean()
print(f"  logistic on raw {logi_low:.3f}  |  net on raw {acc:.3f}  |  chance .53")

def hidden(A):
    for W,b in zip(net.coefs_[:-1],net.intercepts_[:-1]): A=np.maximum(A@W+b,0)
    return A
Htr,Hte=hidden(Ltr),hidden(Lte)
ev=np.sort(np.linalg.eigvalsh(np.cov((Hte-Hte.mean(0)).T)))[::-1]; ev=ev[ev>1e-9]
pr=(ev.sum()**2)/(ev**2).sum()
print(f"\n  ENGINE OUTPUT 1 -- this system is organized by ~{pr:.1f} hidden quantities")
print(f"  (participation ratio of the net's internal representation)")

print(f"\n  ENGINE OUTPUT 2 -- did those hidden quantities reconstruct the (withheld)")
print(f"  physical masses?  R2 from raw-channels-only net latent vs a linear baseline:")
print(f"    {'mass (withheld)':<16}{'linear(raw)':>13}{'net latent':>13}{'discovered?':>13}")
for j,nm in zip(high,[names[k] for k in high]):
    yj_tr,yj_te = Mtr[:,high.index(j)], Mte[:,high.index(j)]
    r2_lin=Ridge(1).fit(Ltr,yj_tr).score(Lte,yj_te)
    r2_net=Ridge(1).fit(Htr,yj_tr).score(Hte,yj_te)
    flag = "YES" if r2_net>0.6 and r2_net-r2_lin>0.15 else ("partial" if r2_net>0.4 else "no")
    print(f"    {nm:<16}{r2_lin:>13.3f}{r2_net:>13.3f}{flag:>13}")
print("\n  READ: linear(raw) = what plain correlation sees in the channels. net latent =")
print("  what the engine BUILT to do its job, never having seen the masses. Where net")
print("  >> linear, the engine DISCOVERED a hidden quantity that is a real physical mass.")
