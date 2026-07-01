# Two structure TYPES, two specialists. SOURCES (NMF, loud end) vs LAWS (min-variance,
# quiet end). Each blind to the other; the portfolio sees both.
import numpy as np, warnings; warnings.filterwarnings("ignore")
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import NMF
rng=np.random.default_rng(0); D,N=30,5000
# TYPE 1: 6 identifiable sources (non-negative sparse latents -> NMF can separate them)
A=np.zeros((D,6))
for k in range(6): A[rng.choice(D,6,replace=False),k]=rng.uniform(0.8,1.6,6)
Zl=(rng.random((N,6))<0.4)*rng.uniform(0.5,2.0,(N,6))
X=Zl@A.T + rng.normal(0,0.4,(N,D)); X=np.clip(X,0,None)
# TYPE 2: 4 conservation laws (a sensor = sum of two others -> a near-constant direction)
laws=[]
for j in range(4):
    g=rng.choice(D,3,replace=False); X[:,g[0]]=X[:,g[1]]+X[:,g[2]]+rng.normal(0,0.05,N)
    v=np.zeros(D); v[g[0]]=1; v[g[1]]=-1; v[g[2]]=-1; laws.append(v/np.linalg.norm(v))
X=np.clip(X,1e-6,None)

# SOURCE specialist: NMF
H=NMF(10,init='nndsvda',max_iter=800,random_state=0).fit(X).components_
Hn=[h/np.linalg.norm(h) for h in H]
# LAW specialist: smallest-variance eigenvectors of the correlation matrix
Xs=StandardScaler().fit_transform(X); vec=np.linalg.eigh(np.cov(Xs.T))[1]
bot=[vec[:,i] for i in range(6)]
src_true=[A[:,k]/np.linalg.norm(A[:,k]) for k in range(6)]
mt=lambda C,T,th=0.7: sum(max(abs(c@t) for c in C)>th for t in T)
print("  specialist                 sources (of 6)   laws (of 4)")
print(f"  SOURCE  (NMF, loud end)          {mt(Hn,src_true)}              {mt(Hn,laws)}")
print(f"  LAW     (min-var, quiet end)     {mt(bot,src_true)}              {mt(bot,laws)}")
print(f"  PORTFOLIO (route to both)        {max(mt(Hn,src_true),mt(bot,src_true))}              {max(mt(Hn,laws),mt(bot,laws))}")
print("\n  one specialist alone misses half the system; the bank of specialists sees it all.")
