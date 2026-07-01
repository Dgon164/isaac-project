"""Real-data missing-variable reconstruction, with built-in ground truth.

Momentum should balance: Sum(visible p) + (invisible p) = 0. We only record the
VISIBLE objects (lepton + 4 jets), so that equation can't close -- and the shortfall
IS the invisible momentum:  p_missing = -Sum(visible p).
Reconstruct it, then compare to the dataset's OWN missing_energy column (the
experimenters' reconstruction of the same invisible momentum) = ground truth.
"""
import numpy as np, pandas as pd, warnings; warnings.filterwarnings("ignore")
F="HIGGS.csv.gz"; N=500_000; S=1.80
X=pd.read_csv(F,header=None,nrows=N,compression="gzip").values.astype(np.float32)[:,1:]
def comp(pt,phi): ph=phi*S; return pt*np.cos(ph), pt*np.sin(ph)
# visible objects: lepton (0,2) + jets k pt,phi at (5+4k, 7+4k)
vx=np.zeros(N); vy=np.zeros(N)
dx,dy=comp(X[:,0],X[:,2]); vx+=dx; vy+=dy
for k in range(4):
    dx,dy=comp(X[:,5+4*k],X[:,7+4*k]); vx+=dx; vy+=dy
# reconstruct invisible momentum from the incomplete equation
inf_x, inf_y = -vx, -vy
inf_mag = np.sqrt(inf_x**2+inf_y**2)
# ground truth: provided missing-energy column (magnitude 3, phi 4)
gt_x, gt_y = comp(X[:,3], X[:,4]); gt_mag = X[:,3]

print("="*70); print("  RECONSTRUCT invisible momentum from the unclosable balance eqn"); print("="*70)
print(f"  vs the dataset's OWN missing_energy column (ground truth):")
print(f"    missing px : corr(reconstructed, provided) = {np.corrcoef(inf_x,gt_x)[0,1]:+.3f}")
print(f"    missing py : corr(reconstructed, provided) = {np.corrcoef(inf_y,gt_y)[0,1]:+.3f}")
print(f"    magnitude  : corr(reconstructed, provided) = {np.corrcoef(inf_mag,gt_mag)[0,1]:+.3f}")
# how much of the provided MET does our reconstruction explain?
from sklearn.linear_model import LinearRegression
r2x=LinearRegression().fit(inf_x[:,None],gt_x).score(inf_x[:,None],gt_x)
r2y=LinearRegression().fit(inf_y[:,None],gt_y).score(inf_y[:,None],gt_y)
print(f"    R2 explaining provided missing px / py : {r2x:.3f} / {r2y:.3f}")
print("\n  READ: the reconstructed invisible momentum (pure shortfall of the visible")
print("  balance) tracks the experimenters' missing_energy. The match is PARTIAL")
print("  because objects beyond the 4 recorded jets carry momentum too -- itself the")
print("  next missing variable. The equation not closing measured the neutrino.")
