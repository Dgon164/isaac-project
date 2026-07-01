# CRITIQUE 3: does naive column-shuffle inflate the noise floor vs a phase-space-aware null?
import numpy as np, pandas as pd, warnings; warnings.filterwarnings("ignore")
F="HIGGS.csv.gz"; N=600_000; S=1.80
X=pd.read_csv(F,header=None,nrows=N,compression="gzip").values.astype(np.float32)[:,1:]
def comp(pt,phi): ph=phi*S; return pt*np.cos(ph), pt*np.sin(ph)
cols=[]; 
lpx,lpy=comp(X[:,0],X[:,2]); cols+=[lpx,lpy]
for k in range(4):
    px,py=comp(X[:,5+4*k],X[:,7+4*k]); cols+=[px,py]
mpx,mpy=comp(X[:,3],X[:,4]); cols+=[mpx,mpy]
M=np.column_stack(cols); Mc=M-M.mean(0)
val,vec=np.linalg.eigh(np.cov(Mc.T)); w=vec[:,0]
rng=np.random.default_rng(0)
# null A: naive independent column shuffle
Ma=np.column_stack([M[rng.permutation(N),j] for j in range(M.shape[1])])
# null B: phase-space-aware -- shuffle WITHIN bins of total visible scalar pt (preserves energy scale)
scale=np.abs(M).sum(1); b=np.digitize(scale,np.quantile(scale,np.linspace(0,1,21)[1:-1]))
Mb=M.copy()
for bi in np.unique(b):
    idx=np.where(b==bi)[0]
    for j in range(M.shape[1]): Mb[idx,j]=M[idx[rng.permutation(len(idx))],j]
def closure(Mn):
    vr=np.var(Mc@w); vs=np.var((Mn-Mn.mean(0))@w); return 1-vr/vs, vs
print("="*64); print("  CRITIQUE 3 — naive vs phase-space-aware (stratified) null"); print("="*64)
cA,vA=closure(Ma); cB,vB=closure(Mb)
print(f"  law-direction variance in REAL data: {np.var(Mc@w):.4f}")
print(f"  naive column-shuffle:      null var {vA:.4f}   closure {cA*100:.1f}%")
print(f"  energy-stratified shuffle: null var {vB:.4f}   closure {cB*100:.1f}%")
print(f"  difference in reported closure: {(cA-cB)*100:+.1f} points")
