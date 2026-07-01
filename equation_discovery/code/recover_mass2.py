"""The data is per-feature SCALED (phi range +-1.74 = pi/sqrt(3) => standardized).
Standardization of a symmetric var is ~ x/std: invertible with ONE constant.
Recover the eta & phi scale constants that make the invariant-mass equation CLOSE.
If correlation jumps to ~1, the equation was intact all along -- only mis-calibrated.
"""
import numpy as np, warnings; warnings.filterwarnings("ignore")
from sklearn.datasets import fetch_openml
d = fetch_openml(data_id=23512, as_frame=False)
X = np.asarray(d.data, np.float32); names = list(d.feature_names)
ok = ~np.isnan(X).any(1); X = X[ok]
def col(nm): return names.index(nm)
jets = [(col(f"jet{k}pt"),col(f"jet{k}eta"),col(f"jet{k}phi")) for k in (1,2,3,4)]

def recon(a,b,se,sp):
    pta,ea,pa = X[:,a[0]], X[:,a[1]]*se, X[:,a[2]]*sp
    ptb,eb,pb = X[:,b[0]], X[:,b[1]]*se, X[:,b[2]]*sp
    m2 = 2*pta*ptb*(np.cosh(ea-eb) - np.cos(pa-pb))
    return np.sqrt(np.clip(m2,0,None))

mjj = X[:,col("m_jj")]
print("="*68); print("  SCALE SEARCH — undo eta/phi standardization so the equation closes")
print("="*68)
print("  (phi std of uniform[-pi,pi] = pi/sqrt(3) = %.3f ; eta unknown)" % (np.pi/np.sqrt(3)))
best=(-1,None)
for se in np.linspace(0.6,2.4,19):
    for sp in np.linspace(1.0,2.4,15):
        r = abs(np.corrcoef(recon(jets[0],jets[1],se,sp), mjj)[0,1])
        if r>best[0]: best=(r,(se,sp))
r,(se,sp)=best
print(f"  best |corr(m_jj, reconstructed)| = {r:.3f}  at eta_scale={se:.2f} phi_scale={sp:.2f}")
print(f"  (phi_scale vs predicted 1.814:  {sp:.2f})")

# with those constants, reconstruct ALL masses from their natural object sets
print("\n  reconstruct each provided mass at the recovered scales (best object set):")
def best_pair(target, sets):
    tv=X[:,col(target)]; b=(-1,None)
    for s in sets:
        c=recon(s[0],s[1],se,sp); rr=abs(np.corrcoef(c,tv)[0,1])
        if rr>b[0]: b=(rr,s)
    return b
pairs=[(jets[i],jets[j]) for i in range(4) for j in range(i+1,4)]
for t in ["m_jj","m_bb","m_wbb","m_wwbb"]:
    rr,s=best_pair(t,pairs); print(f"    {t:<8} |corr|={rr:.3f}")

# single global scale fit for m_jj -> R2
c12=recon(jets[0],jets[1],se,sp)
k=(c12@mjj)/(c12@c12); R2=1-np.var(mjj-k*c12)/np.var(mjj)
print(f"\n  m_jj single-scale fit R2 = {R2:.3f}")
print("\n  READ: if corr ~0.9+ at phi_scale near 1.81, the invariant-mass equation is")
print("  fully present and we recovered both the FORM and its calibration constants.")
