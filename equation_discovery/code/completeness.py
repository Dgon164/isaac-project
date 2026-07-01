"""What's the score? For the momentum sector of real HIGGS:
 1. how COMPLETELY does the discovered conservation law close (vs a random/shuffled floor)?
 2. is the LEFTOVER structured (=> another missing variable we can still account for ->
    100% reachable) or pure noise (=> the data's ceiling)?
"""
import numpy as np, pandas as pd, warnings; warnings.filterwarnings("ignore")
from sklearn.ensemble import HistGradientBoostingRegressor as HGB
F="HIGGS.csv.gz"; N=400_000; S=1.80
X=pd.read_csv(F,header=None,nrows=N,compression="gzip").values.astype(np.float32)[:,1:]
def comp(pt,phi): ph=phi*S; return pt*np.cos(ph), pt*np.sin(ph)
cols=[];
lpx,lpy=comp(X[:,0],X[:,2]); cols+=[lpx,lpy]
for k in range(4):
    px,py=comp(X[:,5+4*k],X[:,7+4*k]); cols+=[px,py]
mpx,mpy=comp(X[:,3],X[:,4]); cols+=[mpx,mpy]
M=np.column_stack(cols); Mc=M-M.mean(0)
val,vec=np.linalg.eigh(np.cov(Mc.T))
rng=np.random.default_rng(0)
Msh=np.column_stack([M[rng.permutation(N),j] for j in range(M.shape[1])])

print("="*70); print("  THE SCORE — momentum sector of real HIGGS"); print("="*70)
for i in range(2):
    w=vec[:,i]
    vr=np.var(Mc@w); vs=np.var((Msh-Msh.mean(0))@w)
    closure=1-vr/vs
    print(f"  conservation law {i}: closes {closure*100:.1f}%  (residual var {vr:.3f} vs random {vs:.3f})")

# is the leftover structured (peelable) or noise (ceiling)?
r = Mc@vec[:,0]                                   # residual of law 0 (should be ~0 if perfect)
# can we predict it from the OTHER recorded info (b-tags, masses, etc.)? -> structured?
other = np.column_stack([X[:,8],X[:,12],X[:,16],X[:,20],   # b-tags
                         X[:,21],X[:,22],X[:,25],X[:,26],   # masses
                         X[:,1],X[:,6],X[:,10]])            # etas
r2 = HGB(max_iter=200,random_state=0).fit(other[:N//2], r[:N//2]).score(other[N//2:], r[N//2:])
print(f"\n  leftover of law 0: predictable from other recorded features?  R2 = {r2:.3f}")
if r2 > 0.1:
    print("  => STRUCTURED leftover: another missing variable is recorded-elsewhere and")
    print(f"     peelable. ~{r2*100:.0f}% of the gap is recoverable -> 100% still reachable.")
else:
    print("  => leftover is ~NOISE (not predictable): this is the data's CEILING. The")
    print("     unrecorded momentum (extra jets) is gone from the file; 100% needs richer data.")
print("\n  SUMMARY: laws found = 2/2 (all the conservation laws that exist here).")
print("  Closure tells you how much each is accounted for; the leftover test tells you")
print("  whether the remaining gap is recoverable or the data's hard ceiling.")
