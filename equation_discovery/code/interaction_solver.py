"""STAGE 2: how EXACTLY do the detected components relate? Search a library of
ALLOWED numerical interactions for the combination that reproduces a detected
quantity, and read the constants that fall out.

Target: a detected mass (m_jj). Sources: the 4 jets' (pt,eta,phi). Allowed
interactions (the physics-permitted forms, applied to EVERY jet pair so the fit
also picks the right pairing):
    pt_a*pt_b ,  pt_a*pt_b*cosh(eta_a-eta_b) ,  pt_a*pt_b*cos(s*(phi_a-phi_b))
Sparse-select over all pairs -> surviving terms = the equation; coefficients = the
numbers. Grade: does it recover  m^2 ~ pt_a pt_b (cosh d_eta - cos d_phi)  for ONE pair?
"""
import numpy as np, pandas as pd, warnings; warnings.filterwarnings("ignore")
from sklearn.linear_model import Lasso, LinearRegression
F="HIGGS.csv.gz"; N=300_000; S=1.80
raw=pd.read_csv(F,header=None,nrows=N,compression="gzip").values.astype(np.float32)
X=raw[:,1:]
# jet k (0-based in X): pt=5+4k, eta=6+4k, phi=7+4k ; m_jj = col 21
jets=[(5+4*k,6+4*k,7+4*k) for k in range(4)]
mjj=X[:,21]; target=mjj**2

cands=[]; cnames=[]
for a in range(4):
    for b in range(a+1,4):
        pta,ea,pa=X[:,jets[a][0]],X[:,jets[a][1]],X[:,jets[a][2]]
        ptb,eb,pb=X[:,jets[b][0]],X[:,jets[b][1]],X[:,jets[b][2]]
        cands += [pta*ptb, pta*ptb*np.cosh(ea-eb), pta*ptb*np.cos(S*(pa-pb))]
        cnames += [f"pt{a+1}*pt{b+1}", f"pt{a+1}*pt{b+1}*cosh(d_eta)", f"pt{a+1}*pt{b+1}*cos(d_phi)"]
P=np.column_stack(cands)
# standardize for selection
Ps=(P-P.mean(0))/(P.std(0)+1e-9); ts=(target-target.mean())/target.std()
las=Lasso(alpha=0.01,max_iter=20000).fit(Ps,ts)
w=las.coef_; R2=las.score(Ps,ts); o=np.argsort(-np.abs(w))
print("="*70); print("  STAGE 2 — constrained interaction solver: derive m_jj's equation")
print("="*70)
print(f"  sparse fit over {len(cnames)} allowed interactions:  R2={R2:.3f}  "
      f"({int((w!=0).sum())} terms kept)")
print("  surviving interactions (standardized weights):")
for k in o[:6]:
    if abs(w[k])>1e-3: print(f"     {w[k]:+.3f}  {cnames[k]}")

# read the actual constants for the winning pair (raw OLS on its cosh & cos terms)
top_pair = cnames[o[0]].split("*")[0][2:] + cnames[o[0]].split("*")[1][2:]  # e.g. '12'
a,b = int(top_pair[0])-1, int(top_pair[1])-1
pta,ea,pa=X[:,jets[a][0]],X[:,jets[a][1]],X[:,jets[a][2]]
ptb,eb,pb=X[:,jets[b][0]],X[:,jets[b][1]],X[:,jets[b][2]]
T1=pta*ptb*np.cosh(ea-eb); T2=pta*ptb*np.cos(S*(pa-pb))
ols=LinearRegression().fit(np.column_stack([T1,T2]), target)
c1,c2=ols.coef_; r2raw=ols.score(np.column_stack([T1,T2]),target)
print(f"\n  winning pair = jets ({a+1},{b+1}).  raw fit of m_jj^2:")
print(f"     m_jj^2 = {c1:+.3f}*[pt{a+1}pt{b+1} cosh(d_eta)] {c2:+.3f}*[pt{a+1}pt{b+1} cos(d_phi)] {ols.intercept_:+.3f}")
print(f"     R2={r2raw:.3f}   |  TRUE FORM predicts c1 = -c2 (equal & opposite): ratio = {(-c1/c2 if c2 else 0):.2f}")
print("\n  READ: if one pair's cosh & cos terms dominate with EQUAL-OPPOSITE coefficients,")
print("  the solver recovered the invariant-mass law  m^2 = k*pt_a*pt_b*(cosh d_eta - cos d_phi)")
print("  AND the pairing -- the exact numerical interaction that creates the detected mass.")
