"""Compare the dataset to itself, at scale, to ISOLATE the conserved interactions.

Each event = the same physics from a random angle. A conserved law is a combination
of the raw momentum components that stays ~constant across ALL events (tiny variance).
To prove a low-variance combo is REAL physics and not an accident of the marginals,
compare against a SHUFFLED copy of the same data (each column permuted independently
-> identical noise/marginals, but every cross-object relationship destroyed).

  real small variance + shuffled LARGE variance  =>  an isolated, real interaction.
The gap is the interaction; the shuffled level is the noise floor. Read the
eigenvector's coefficients -> the equation.
"""
import numpy as np, pandas as pd, warnings; warnings.filterwarnings("ignore")
F = "HIGGS.csv.gz"
N = 1_500_000
print(f"loading {N:,} rows of the full HIGGS ...")
df = pd.read_csv(F, header=None, nrows=N, compression="gzip").values.astype(np.float32)
y = df[:,0]; X = df[:,1:]                     # col0 label (UNUSED here), 28 features
# low-level column layout (0-based within X): lepton pt,eta,phi (0,1,2);
# missing mag,phi (3,4); jet k pt,eta,phi,btag at 5+4k..
S = 1.80                                       # discovered phi scale
def comp(pt, phi):
    ph = phi*S; return pt*np.cos(ph), pt*np.sin(ph)
cols, names = [], []
lpx,lpy = comp(X[:,0], X[:,2]); cols += [lpx,lpy]; names += ["lep_px","lep_py"]
for k in range(4):
    pt,phi = X[:,5+4*k], X[:,7+4*k]; px,py = comp(pt,phi)
    cols += [px,py]; names += [f"j{k+1}_px",f"j{k+1}_py"]
mpx,mpy = comp(X[:,3], X[:,4]); cols += [mpx,mpy]; names += ["met_px","met_py"]
M = np.column_stack(cols)                      # (N, 12) momentum components

def smallest_dirs(A, k=4):
    Ac = A - A.mean(0); C = np.cov(Ac.T)
    val,vec = np.linalg.eigh(C); return val, vec

val, vec = smallest_dirs(M)
# shuffled copy: permute each column independently (kills joint structure, keeps marginals)
rng = np.random.default_rng(0)
Msh = np.column_stack([M[rng.permutation(len(M)), j] for j in range(M.shape[1])])
val_sh, _ = smallest_dirs(Msh)

print("\n"+"="*70)
print("  SELF-COMPARISON: variance of each direction, REAL vs SHUFFLED")
print("="*70)
print(f"  {'rank':<6}{'real var':>12}{'shuffled var':>14}{'real/shuf':>11}   law?")
for i in range(4):
    w = vec[:,i]
    # variance of this same direction in shuffled data
    vsh = np.var((Msh-Msh.mean(0)) @ w)
    ratio = val[i]/vsh
    flag = "REAL LAW" if ratio < 0.5 else ""
    print(f"  {i:<6}{val[i]:>12.3f}{vsh:>14.3f}{ratio:>11.3f}   {flag}")

print("\n  the two most-conserved directions, as equations (coeff per component):")
for i in range(2):
    w = vec[:,i]/np.abs(vec[:,i]).max()
    terms = "  ".join(f"{w[j]:+.2f}*{names[j]}" for j in range(len(names)) if abs(w[j])>0.25)
    print(f"    dir {i}:  {terms}")
print("\n  READ: a direction with tiny REAL variance but large SHUFFLED variance is a")
print("  genuine conservation law isolated from noise. If its coefficients pick out")
print("  all the px (or all the py) components equally, the engine just rediscovered")
print("  transverse-momentum conservation -- Sum(px)=0, Sum(py)=0 -- by self-comparison.")
