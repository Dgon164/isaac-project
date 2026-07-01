"""Census of shadows: what is structure (accountable) vs independent input vs noise,
and is there UNACCOUNTED structure still hinting at the answer?

For each recorded feature: how much is it determined by the others (its shadow)?
  high shadow  = redundant/derived -> a relationship we can account for (an equation)
  low  shadow  = independent degree of freedom (a genuine input / a random angle)
Then: strip ALL the inter-feature shadows (use the residuals) and ask -- does what's
LEFT still differentiate signal from background? If yes, an unread shadow remains.
"""
import numpy as np, pandas as pd, warnings; warnings.filterwarnings("ignore")
from sklearn.ensemble import HistGradientBoostingRegressor as HGBR, HistGradientBoostingClassifier as HGBC
F="HIGGS.csv.gz"; N=200_000
D=pd.read_csv(F,header=None,nrows=N,compression="gzip").values.astype(np.float32)
y=D[:,0]; X=D[:,1:]; n=X.shape[1]
nm=["lep_pt","lep_eta","lep_phi","met_mag","met_phi"]+ \
   [f"jet{k}{p}" for k in (1,2,3,4) for p in ("pt","eta","phi","btag")]+ \
   ["m_jj","m_jjj","m_lv","m_jlv","m_bb","m_wbb","m_wwbb"]
tr=slice(0,N*3//4); te=slice(N*3//4,N)

print("="*64); print("  SHADOW CENSUS — how determined is each feature by the rest?"); print("="*64)
shadow=np.zeros(n); resid=np.zeros((N,n))
for j in range(n):
    o=[k for k in range(n) if k!=j]
    m=HGBR(max_iter=150,random_state=0).fit(X[tr][:,o],X[tr,j])
    shadow[j]=m.score(X[te][:,o],X[te,j])
    resid[:,j]=X[:,j]-m.predict(X[:,o])
order=np.argsort(-shadow)
for j in order:
    tag="derived/redundant (accountable)" if shadow[j]>0.5 else \
        ("partly shadowed" if shadow[j]>0.15 else "independent input / noise")
    print(f"  {nm[j]:<9} shadow {shadow[j]:>6.2f}   {tag}")

# strip all inter-feature shadows -> do the residuals still find the Higgs?
acc_full=(HGBC(max_iter=200,random_state=0).fit(X[tr],y[tr]).predict(X[te])==y[te]).mean()
acc_res =(HGBC(max_iter=200,random_state=0).fit(resid[tr],y[tr]).predict(resid[te])==y[te]).mean()
print("\n"+"="*64); print("  UNREAD SHADOW: does what's LEFT (residuals) still find the answer?"); print("="*64)
print(f"  full features -> Higgs: {acc_full:.3f}")
print(f"  residuals only -> Higgs: {acc_res:.3f}   (chance 0.53)")
print("\n  READ: high-shadow features are accountable as equations (close the gap there).")
print("  low-shadow are the independent inputs. If the RESIDUALS still beat chance, the")
print("  answer's shadow is NOT fully carried by the pairwise relationships -- there is")
print("  unaccounted structure (another shadow) living in the joint/higher-order part.")
