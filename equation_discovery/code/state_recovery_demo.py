"""
state_recovery_demo.py  —  self-contained, deterministic, no external data.

Generates a synthetic "particle in multiple states" dataset observed through fully
variable kinematics (random Lorentz boosts), then RECOVERS, using no ground truth:
  (1) the INVARIANT signature  — the conserved form that identifies the particle,
  (2) the STATE SPECTRUM        — base state + other states + edge cases, by frequency,
  (3) a per-event assignment    — which state each collision is in.

Exports:
  ../data/state_recovery_dataset.csv   (per-event: raw observables, recovered + truth)
  ../data/state_recovery_summary.txt   (recovered signature + state table vs planted)

Reproduce:  python state_recovery_demo.py     (SEED fixed -> identical output every run)
"""
import numpy as np, os, csv

SEED = 0
N    = 60000
rng  = np.random.default_rng(SEED)

# ───────────────────────── ground truth (used ONLY to grade/export) ─────────────────────────
# one particle whose invariant mass occupies discrete STATES with given frequencies:
r = rng.random(N)
mass = np.empty(N); true_state = np.empty(N, dtype=object)
m_base = (r < 0.70);                 mass[m_base]  = 1.00; true_state[m_base]  = "base(1.00)"
m_s1   = (r >= 0.70) & (r < 0.90);   mass[m_s1]    = 1.30; true_state[m_s1]    = "state(1.30)"
m_s2   = (r >= 0.90) & (r < 0.98);   mass[m_s2]    = 1.55; true_state[m_s2]    = "state(1.55)"
m_edge = (r >= 0.98);                mass[m_edge]  = rng.uniform(0.5, 2.5, m_edge.sum()); true_state[m_edge] = "edge"

# ───────────────────────── observe through random boosts (only the invariant is fixed) ─────────────────────────
th = rng.uniform(0, 2*np.pi, N); half = mass/2
E1 = half.copy(); px1 = half*np.cos(th); py1 = half*np.sin(th)
E2 = half.copy(); px2 = -px1;            py2 = -py1
phi = rng.uniform(0, 2*np.pi, N); eta = rng.normal(0, 0.9, N)
beta = np.tanh(eta); gam = np.cosh(eta); nx = np.cos(phi); ny = np.sin(phi)
def boost(E, px, py):
    ppar = px*nx + py*ny; perpx = px - ppar*nx; perpy = py - ppar*ny
    return gam*(E + beta*ppar), (gam*(ppar + beta*E))*nx + perpx, (gam*(ppar + beta*E))*ny + perpy
E1, px1, py1 = boost(E1, px1, py1)
E2, px2, py2 = boost(E2, px2, py2)   # these 6 columns are the "raw detector observables"

# ═════════════════════════════ RECOVERY (no ground truth touched) ═════════════════════════════
Et, Px, Py = E1+E2, px1+px2, py1+py2
Z  = np.column_stack([Et**2, Px**2, Py**2, Et*Px, Et*Py, Px*Py])
Zc = Z - Z.mean(0)
w  = np.linalg.eigh(np.cov(Zc.T))[1][:, 0]                 # (1) signature = min-variance form
sig = w / np.abs(w[0])
q  = (Z @ w); q *= np.sign(q.mean())
m_rec = np.sqrt(np.clip(q, 1e-9, None)); m_rec /= np.median(m_rec)   # recovered mass, anchored

# (2) state spectrum: smoothed-histogram peaks = recurring levels
hist, edges = np.histogram(m_rec, bins=200, range=(0.4, 2.6)); centers = (edges[:-1]+edges[1:])/2
sm = np.convolve(hist, np.ones(5)/5, mode="same")
peaks = sorted(float(centers[i]) for i in range(2, len(sm)-2)
               if sm[i] >= sm[i-1] and sm[i] > sm[i+1] and sm[i] > N*0.01)
nearest = np.array([min(peaks, key=lambda p: abs(p-mi)) for mi in m_rec])
off = np.abs(m_rec - nearest) > 0.06                       # (3) per-event: off all levels = edge
freq = {p: float(((np.abs(m_rec-p) < 0.06) & ~off).mean()) for p in peaks}
base = max(peaks, key=lambda p: freq[p])
rec_state = np.array(["edge" if off[i] else ("base" if nearest[i]==base else f"state({nearest[i]:.2f})")
                      for i in range(N)], dtype=object)

# ───────────────────────── export ─────────────────────────
HERE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(HERE, "..", "data"); os.makedirs(OUT, exist_ok=True)
csv_path = os.path.join(OUT, "state_recovery_dataset.csv")
with open(csv_path, "w", newline="") as f:
    wr = csv.writer(f)
    wr.writerow(["event_id","E1","px1","py1","E2","px2","py2",
                 "recovered_mass","recovered_state","true_mass","true_state"])
    for i in range(N):
        wr.writerow([i, f"{E1[i]:.5f}",f"{px1[i]:.5f}",f"{py1[i]:.5f}",
                     f"{E2[i]:.5f}",f"{px2[i]:.5f}",f"{py2[i]:.5f}",
                     f"{m_rec[i]:.5f}", rec_state[i], f"{mass[i]:.5f}", true_state[i]])

sum_path = os.path.join(OUT, "state_recovery_summary.txt")
lines = []
lines.append("RECOVERED SIGNATURE (the invariable / particle identity):")
labels = ["E^2","px^2","py^2","E*px","E*py","px*py"]
lines.append("   q = " + "  ".join(f"{sig[k]:+.2f}*{labels[k]}" for k in range(6) if abs(sig[k])>0.05))
lines.append("   (= the Minkowski invariant E^2-px^2-py^2; conserved across all boosts)")
lines.append("")
lines.append("RECOVERED STATE SPECTRUM (the variable / states the particle occupies):")
lines.append(f"   {'level':>8}{'frequency':>12}   role")
for p in sorted(peaks, key=lambda p: -freq[p]):
    role = "BASE STATE" if p == base else "other state"
    lines.append(f"   {p:>8.2f}{freq[p]*100:>11.1f}%   {role}")
lines.append(f"   {'edge':>8}{off.mean()*100:>11.1f}%   off-level (edge cases)")
lines.append("")
lines.append("PLANTED TRUTH (for grading): base 1.00 (70%), 1.30 (20%), 1.55 (8%), edges 2%")
# per-state recovery accuracy vs truth
def acc(true_mask, lvl):
    if lvl is None: return (rec_state[true_mask]=="edge").mean()
    return (np.abs(m_rec[true_mask]-lvl)<0.06).mean()
lines.append("")
lines.append("RECOVERY ACCURACY (recovered value lands on the right level):")
lines.append(f"   base 1.00: {acc(m_base,1.00)*100:5.1f}%   state 1.30: {acc(m_s1,1.30)*100:5.1f}%   "
             f"state 1.55: {acc(m_s2,1.55)*100:5.1f}%")
open(sum_path, "w").write("\n".join(lines))

print("\n".join(lines))
print(f"\nWROTE:\n  {csv_path}\n  {sum_path}")
print(f"\nrows: {N}   (deterministic: SEED={SEED} -> identical every run)")
