# A fully-known hard world: 20 hidden 'things', each touches a random set of sensors at a
# random strength, present at random per event, buried in noise. How many can it recover?
import numpy as np, warnings; warnings.filterwarnings("ignore")
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import NMF
rng=np.random.default_rng(0)
K,D,N = 20, 50, 6000

# --- build the world (ground truth) ---
W=np.zeros((K,D))
nsens =rng.integers(3,16,K)                       # how many sensors each thing touches (random)
strength=rng.uniform(0.3,2.0,K)                   # how strong each thing is (random range)
freq  =rng.uniform(0.10,0.60,K)                   # how often each thing shows up (random)
for k in range(K):
    s=rng.choice(D,nsens[k],replace=False); W[k,s]=strength[k]*rng.uniform(0.5,1.5,nsens[k])
Z=(rng.random((N,K))<freq).astype(float)          # which things are present each event (random)
mag=rng.uniform(0.5,1.5,(N,K))                    # activation value when present (random)
X=np.clip((Z*mag)@W + rng.normal(0,1.0,(N,D)),0,None)   # sensors = sum of present things + noise

# --- engine: estimate the amount, then unmix, then match to ground truth ---
Xs=StandardScaler().fit_transform(X)
real=np.sort(np.linalg.eigvalsh(np.corrcoef(Xs.T)))[::-1]
sh=np.array([np.sort(np.linalg.eigvalsh(np.corrcoef(np.column_stack(
    [Xs[rng.permutation(N),j] for j in range(D)]).T)))[::-1] for _ in range(20)])
Khat=int((real>np.percentile(sh,95,axis=0)).sum())
H=NMF(n_components=min(K+6,D-1),init='nndsvda',max_iter=700,random_state=0).fit(X).components_

res=[]
for k in range(K):
    best=max(abs(np.corrcoef(W[k],H[j])[0,1]) for j in range(H.shape[0]))
    res.append((best>0.6, nsens[k], strength[k], freq[k], best))
det=sum(r[0] for r in res); clean=sum(r[4]>0.85 for r in res)

print(f"WORLD: {K} hidden things, {D} sensors, {N} events, buried in noise")
print(f"  engine's guess at HOW MANY things (floor): {Khat} of {K}")
print(f"  DETECTED (sensor-signature recovered): {det} of {K}  ({det/K*100:.0f}%)")
print(f"     of those, cleanly nailed (>85% match): {clean}")
d=[r for r in res if r[0]]; m=[r for r in res if not r[0]]
f=lambda L,i: (np.mean([r[i] for r in L]) if L else float('nan'))
print(f"\n  WHICH ones it found vs missed (this is the honest profile):")
print(f"    FOUND  ({len(d)}): avg {f(d,1):.0f} sensors,  strength {f(d,2):.2f},  present {f(d,3)*100:.0f}% of events")
print(f"    MISSED ({len(m)}): avg {f(m,1):.0f} sensors,  strength {f(m,2):.2f},  present {f(m,3)*100:.0f}% of events")
print("\n  (found = strong / touches many sensors / shows up often. missed = weak / few / rare.)")
