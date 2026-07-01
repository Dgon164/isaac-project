# Twist: stronger signal -> FEWER sensors (direct measurement); weaker -> MANY (indirect).
# Which kind does the engine recover -- the direct probes or the diffuse hidden causes?
import numpy as np, warnings; warnings.filterwarnings("ignore")
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import NMF
rng=np.random.default_rng(0)
K,D,N = 20, 60, 6000

directness=rng.uniform(0,1,K)                       # 1 = direct (strong,few), 0 = indirect (weak,many)
strength = 0.4 + 1.9*directness                     # weak 0.4  <->  strong 2.3
nsens    = np.clip((34-30*directness),3,D).astype(int)  # diffuse 34  <->  concentrated 4
W=np.zeros((K,D))
for k in range(K):
    s=rng.choice(D,nsens[k],replace=False); W[k,s]=strength[k]*rng.uniform(0.7,1.3,nsens[k])
freq=rng.uniform(0.1,0.6,K); Z=(rng.random((N,K))<freq).astype(float); mag=rng.uniform(0.5,1.5,(N,K))
X=np.clip((Z*mag)@W + rng.normal(0,1.0,(N,D)),0,None)

H=NMF(n_components=min(K+6,D-1),init='nndsvda',max_iter=800,random_state=0).fit(X).components_
res=[]
for k in range(K):
    best=max(abs(np.corrcoef(W[k],H[j])[0,1]) for j in range(H.shape[0]))
    res.append((best>0.6, directness[k], strength[k], int(nsens[k]), strength[k]**2*nsens[k], best))
det=sum(r[0] for r in res)
direct=[r for r in res if r[1]>0.5]; indirect=[r for r in res if r[1]<=0.5]
fr=lambda L:(100*sum(r[0] for r in L)/len(L)) if L else float('nan')
av=lambda L,i:(np.mean([r[i] for r in L]) if L else float('nan'))
print(f"DETECTED {det} of {K} total")
print(f"  DIRECT   (strong, few sensors): found {fr(direct):>3.0f}% of {len(direct)}   "
      f"[avg strength {av(direct,2):.2f}, {av(direct,3):.0f} sensors]")
print(f"  INDIRECT (weak, many sensors):  found {fr(indirect):>3.0f}% of {len(indirect)}   "
      f"[avg strength {av(indirect,2):.2f}, {av(indirect,3):.0f} sensors]")
f=[r for r in res if r[0]]; m=[r for r in res if not r[0]]
print(f"\n  total coherent signal (strength^2 x #sensors):  found {av(f,4):.1f}  vs  missed {av(m,4):.1f}")
print("  (if total-signal splits found/missed better than per-sensor strength, the")
print("   coherence-across-sensors lever is doing the work for the indirect ones.)")
