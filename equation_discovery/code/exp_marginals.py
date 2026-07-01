# CRITIQUE 4: is the Higgs signal in the 1D MARGINALS, not the joint structure?
# additive model (no interactions) = marginal-only ceiling; vs full model (interactions).
import numpy as np, pandas as pd, warnings; warnings.filterwarnings("ignore")
from sklearn.ensemble import HistGradientBoostingClassifier as HGB
from sklearn.metrics import roc_auc_score
F="HIGGS.csv.gz"; N=400_000
D=pd.read_csv(F,header=None,nrows=N,compression="gzip").values.astype(np.float32)
y=D[:,0]; X=D[:,1:]; tr=slice(0,N*3//4); te=slice(N*3//4,N)
nm=["lep_pt","lep_eta","lep_phi","met_mag","met_phi"]+[f"jet{k}{p}" for k in(1,2,3,4) for p in("pt","eta","phi","btag")]+["m_jj","m_jjj","m_lv","m_jlv","m_bb","m_wbb","m_wwbb"]
def auc(model,cols=None):
    Xt=X[tr] if cols is None else X[tr][:,cols]; Xv=X[te] if cols is None else X[te][:,cols]
    return roc_auc_score(y[te], model.fit(Xt,y[tr]).predict_proba(Xv)[:,1])
full=auc(HGB(max_iter=300,random_state=0))                                  # interactions allowed
add =auc(HGB(max_iter=300,interaction_cst="no_interactions",random_state=0)) # ADDITIVE = marginals only
print("="*62); print("  CRITIQUE 4 — is the signal in the 1D marginals?"); print("="*62)
print(f"  full model (interactions allowed) AUC = {full:.3f}")
print(f"  ADDITIVE model (no interactions, 1D marginals only) AUC = {add:.3f}")
print(f"  interaction gain = {full-add:+.3f}  ({(full-add)/(full-0.5)*100:.0f}% of the signal needs interactions)")
print("\n  best single-feature AUC (pure 1D marginal):")
sing=sorted(((roc_auc_score(y[te],HGB(max_iter=120,random_state=0).fit(X[tr][:,[j]],y[tr]).predict_proba(X[te][:,[j]])[:,1]),nm[j]) for j in range(28)),reverse=True)
for a,n in sing[:8]: print(f"    {n:<9} {a:.3f}")
