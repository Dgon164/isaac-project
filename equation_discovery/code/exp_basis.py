# CRITIQUE 1: polynomial Stage-1 cannot see a transcendental invariant; enriched basis can.
import numpy as np; rng=np.random.default_rng(0)
N=40000; M=1.0
th=rng.uniform(0,2*np.pi,N); h=M/2
# two massless products in (pt,eta,phi) after a random boost -> constant invariant mass M
eta=rng.normal(0,0.8,N); phi=rng.uniform(-2,2,N); dphi=rng.uniform(1.5,2.5,N); deta=rng.uniform(0.5,1.5,N)
pt1=np.abs(rng.normal(1,0.3,N))+0.3; pt2=np.abs(rng.normal(1,0.3,N))+0.3
eta1=eta; eta2=eta-deta; phi1=phi; phi2=phi-dphi
# enforce constant invariant mass by setting pt2 from the mass relation (+noise)
m2=M**2
denom=2*pt1*(np.cosh(eta1-eta2)-np.cos(phi1-phi2))
pt2=m2/np.maximum(denom,0.2)*np.exp(rng.normal(0,0.03,N))
feat=np.column_stack([pt1,eta1,phi1,pt2,eta2,phi2])
def spectrum(P):
    Ps=(P-P.mean(0))/(P.std(0)+1e-9); C=Ps.T@Ps/len(P)
    return np.sort(np.linalg.eigvalsh(C))[:3]
# polynomial lift (squares + pairwise products)
n=6; poly=[feat,feat**2]+[ (feat[:,i]*feat[:,j])[:,None] for i in range(n) for j in range(i+1,n)]
Ppoly=np.column_stack(poly)
# enriched: add the transcendental atoms
trans=np.column_stack([pt1*pt2*np.cosh(eta1-eta2), pt1*pt2*np.cos(phi1-phi2)])
Penr=np.column_stack([Ppoly,trans])
print("  smallest 3 eigenvalues (0 => an exact relationship exists in this basis):")
print(f"    polynomial basis : {spectrum(Ppoly).round(4)}")
print(f"    + cosh/cos atoms : {spectrum(Penr).round(4)}")
print("  (a near-zero eigenvalue only with the transcendental atoms == the invariant)")
