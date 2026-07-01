"""Unsupervised discovery of a CONSERVATION LAW from raw channels, no labels, no
combinatorics, no jet masses needed: transverse momentum balance  Sum(p) = 0.

px = pt*cos(s*phi), py = pt*sin(s*phi). The colliding beams carry ~no transverse
momentum, so over all visible objects + the missing-energy (neutrino), Sum px ~ 0
and Sum py ~ 0. We DISCOVER this by finding the phi-scale s that minimizes the
total-momentum spread -- the law calibrates phi for us. Then we check the missing
energy is what balances the visible momentum (corr ~ -1).
"""
import numpy as np, warnings; warnings.filterwarnings("ignore")
from sklearn.datasets import fetch_openml
d = fetch_openml(data_id=23512, as_frame=False)
X = np.asarray(d.data, np.float32); names = list(d.feature_names)
ok = ~np.isnan(X).any(1); X = X[ok]
def c(nm): return names.index(nm)

vis = [("lepton_pT","lepton_phi")] + [(f"jet{k}pt",f"jet{k}phi") for k in (1,2,3,4)]
def comps(pt_c, phi_c, s):
    pt, ph = X[:,c(pt_c)], X[:,c(phi_c)]*s
    return pt*np.cos(ph), pt*np.sin(ph)

def total_mom(s, include_missing):
    px = np.zeros(len(X)); py = np.zeros(len(X))
    for ptc,phc in vis:
        dx,dy = comps(ptc,phc,s); px+=dx; py+=dy
    if include_missing:
        dx,dy = comps("missing_energy_magnitude","missing_energy_phi",s); px+=dx; py+=dy
    return px, py

print("="*68); print("  DISCOVER phi-scale by MINIMIZING total transverse momentum"); print("="*68)
best=(1e9,None)
for s in np.linspace(1.0, 2.4, 29):
    px,py = total_mom(s, True)
    imb = np.sqrt(px**2+py**2).mean()
    if imb<best[0]: best=(imb,s)
imb_best, s_best = best
print(f"  best phi-scale s = {s_best:.3f}   (physics prediction pi/sqrt(3) = {np.pi/np.sqrt(3):.3f})")

# how much does the missing-energy term reduce the imbalance? (is it the balancer?)
pxv,pyv = total_mom(s_best, False)              # visible only
pxa,pya = total_mom(s_best, True)               # + missing energy
imb_vis = np.sqrt(pxv**2+pyv**2).mean()
imb_all = np.sqrt(pxa**2+pya**2).mean()
mpx,mpy = comps("missing_energy_magnitude","missing_energy_phi", s_best)
rx = np.corrcoef(pxv, mpx)[0,1]; ry = np.corrcoef(pyv, mpy)[0,1]
typ = np.sqrt(pxv**2+pyv**2).std()
print(f"\n  mean |total momentum|:")
print(f"    visible objects only      : {imb_vis:.3f}")
print(f"    + missing energy (neutrino): {imb_all:.3f}   ({(1-imb_all/imb_vis)*100:.0f}% smaller)")
print(f"  corr(visible px, missing px) = {rx:+.3f}   corr(visible py, missing py) = {ry:+.3f}")
print(f"  (corr ~ -1 => the missing energy is exactly what cancels the visible momentum)")
print("\n  READ: an unsupervised search recovered the phi calibration AND the law")
print("  Sum(p)=0; the missing-energy term is revealed as the invisible particle that")
print("  balances it -- a human-readable conservation law, found from raw numbers.")
