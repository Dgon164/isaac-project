# Specialized detector PER source: "is source k present in this event?" -- like HIGGS,
# but one per source. Compare to unsupervised unmixing (NMF recovered 15/20).
# KEY: a per-source detector needs LABELS (you must already KNOW source k to train it).
import sys; sys.path.insert(0,".")
import numpy as np, warnings; warnings.filterwarnings("ignore")
from world_generator import make_direct_indirect
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
w=make_direct_indirect(seed=0); X=w["X"]; Z=w["Z"]; K=Z.shape[1]
n=len(X); tr=slice(0,n*3//4); te=slice(n*3//4,n)
direct=w["directness"]>0.5
print("  per-source detector (trained with labels) -- can it detect each source?")
aucs=[]
for k in range(K):
    if Z[tr,k].sum()<30: aucs.append(np.nan); continue
    clf=LogisticRegression(max_iter=500).fit(X[tr],Z[tr,k])
    aucs.append(roc_auc_score(Z[te,k], clf.predict_proba(X[te])[:,1]))
aucs=np.array(aucs)
det=lambda mask: int(np.sum(aucs[mask]>0.70))
print(f"  detectable (AUC>0.70):  {det(np.ones(K,bool))} of {K}")
print(f"     of the DIRECT (strong/few) things:   {det(direct)} of {direct.sum()}")
print(f"     of the INDIRECT (weak/many) things:  {det(~direct)} of {(~direct).sum()}")
print(f"\n  for reference, UNSUPERVISED unmixing (NMF) recovered 15 of 20.")
print(f"  per-source supervised detection: {det(np.ones(K,bool))} of {K}  (avg AUC {np.nanmean(aucs):.2f})")
print("\n  ASTERISK: this needs LABELS for each source (you must already know it exists,")
print("  like physicists labeling Higgs vs background). It's DETECTION, not DISCOVERY.")
