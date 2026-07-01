# CRITIQUE 1 (clean): can a POLYNOMIAL lift express a transcendental invariant? predict m^2.
import numpy as np; from sklearn.linear_model import Ridge; from sklearn.model_selection import train_test_split
rng=np.random.default_rng(0); N=60000
pt1=np.abs(rng.normal(1,.3,N))+.3; pt2=np.abs(rng.normal(1,.3,N))+.3   # all INDEPENDENT
e1=rng.normal(0,.8,N); e2=rng.normal(0,.8,N); p1=rng.uniform(-2,2,N); p2=rng.uniform(-2,2,N)
m2=2*pt1*pt2*(np.cosh(e1-e2)-np.cos(p1-p2))                            # the transcendental target
base=np.column_stack([pt1,e1,p1,pt2,e2,p2]); n=6
poly=[base,base**2]+[(base[:,i]*base[:,j])[:,None] for i in range(n) for j in range(i+1,n)]
Ppoly=np.column_stack(poly)
Penr=np.column_stack([Ppoly, pt1*pt2*np.cosh(e1-e2), pt1*pt2*np.cos(p1-p2)])
def r2(P):
    Xtr,Xte,ytr,yte=train_test_split(P,m2,test_size=.3,random_state=0)
    return Ridge(1e-3).fit(Xtr,ytr).score(Xte,yte)
print("="*60); print("  CRITIQUE 1 (clean) — can the basis express the invariant?")
print("="*60)
print(f"  predict m^2 from POLYNOMIAL lift (sq+pairwise): R2 = {r2(Ppoly):.3f}")
print(f"  predict m^2 from + cosh/cos ATOMS:             R2 = {r2(Penr):.3f}")
print("  => polynomial Stage-1 is blind to the transcendental invariant; the atoms fix it.")
