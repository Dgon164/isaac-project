"""Can we recover the invariant-mass EQUATION from raw kinematics with the RIGHT
primitive (cosh(d_eta) - cos(d_phi)), on the data we already have?

If eta/phi are physical (not z-scored), the form m^2 = 2*pt_a*pt_b*(cosh(eta_a-eta_b)
- cos(phi_a-phi_b)) should reconstruct the provided m_jj up to a global scale.
We test EVERY jet pair and see which reproduces each provided high-level mass.
This is the equation, applied -- no fitting of the FORM, only a global scale check.
"""
import numpy as np, warnings; warnings.filterwarnings("ignore")
from sklearn.datasets import fetch_openml

d = fetch_openml(data_id=23512, as_frame=False)
X = np.asarray(d.data, np.float32); names = list(d.feature_names)
ok = ~np.isnan(X).any(1); X = X[ok]

# column map
def col(nm): return names.index(nm)
jets = []
for k in (1,2,3,4):
    jets.append((col(f"jet{k}pt"), col(f"jet{k}eta"), col(f"jet{k}phi"), col(f"jet{k}b-tag")))
lep = (col("lepton_pT"), col("lepton_eta"), col("lepton_phi"))

print("="*68)
print("  RANGES (is eta/phi physical, or z-scored?)")
print("="*68)
for nm in ["jet1pt","jet1eta","jet1phi","lepton_eta","lepton_phi","missing_energy_phi"]:
    c = X[:,col(nm)]
    print(f"    {nm:<20} min {c.min():+.2f}  max {c.max():+.2f}  mean {c.mean():+.2f}  std {c.std():.2f}")

def inv_mass(a, b):
    pta,eta_a,phia = X[:,a[0]], X[:,a[1]], X[:,a[2]]
    ptb,eta_b,phib = X[:,b[0]], X[:,b[1]], X[:,b[2]]
    m2 = 2*pta*ptb*(np.cosh(eta_a-eta_b) - np.cos(phia-phib))
    return np.sqrt(np.clip(m2, 0, None))

print("\n" + "="*68)
print("  RECONSTRUCT each provided mass from a jet pair via the physics formula")
print("  (report best-matching pair by |correlation|; high = the equation holds)")
print("="*68)
for target in ["m_jj","m_bb","m_wbb","m_wwbb","m_jjj","m_jlv"]:
    tv = X[:, col(target)]
    best = (-1, None)
    for i in range(4):
        for j in range(i+1,4):
            cand = inv_mass(jets[i], jets[j])
            r = abs(np.corrcoef(cand, tv)[0,1])
            if r > best[0]: best = (r, (i+1,j+1))
    # also lepton+jet pairs for m_jlv-ish
    print(f"    {target:<8} best jet-pair {str(best[1]):<8} |corr|={best[0]:.3f}")

# focus: m_jj reconstructed by jets (1,2) -- show scale relationship
cand12 = inv_mass(jets[0], jets[1]); mjj = X[:,col("m_jj")]
r = np.corrcoef(cand12, mjj)[0,1]
# fit single global scale (one constant, not a model)
scale = (cand12 @ mjj) / (cand12 @ cand12)
resid_r2 = 1 - np.var(mjj - scale*cand12)/np.var(mjj)
print("\n  m_jj via jets(1,2):  |corr|=%.3f   single-scale R2=%.3f   (scale=%.3f)" % (r, resid_r2, scale))
print("\n  READ: if |corr| is high, the invariant-mass EQUATION is intact in this data")
print("  and recoverable with the right primitive (cosh-cos). Earlier polynomial")
print("  'products' failed because they cannot represent cosh/cos -- the basis was")
print("  wrong, not the data. Then the full download is for STATISTICS, not un-warping.")
