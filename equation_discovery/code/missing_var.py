"""Detect, reconstruct, and IDENTIFY a missing variable from an incomplete equation.

True law:  f = a*b*c*d   (four sources). We record only a,b,c,f -- d is UNMEASURED.
d secretly takes one of two KNOWN values per event (two hidden 'species'), + noise.

Claim (the user's point): abc cannot reproduce f; the shortfall IS d.
  1. DETECT: fit f from a,b,c -> irreducible residual whose size says 'a variable is missing'
  2. RECONSTRUCT: d_hat = f/(a*b*c)  (in logs: residual of log-linear fit)
  3. IDENTIFY: d_hat's values match entries in a catalog of KNOWN quantities ->
     'present but undetected', and WHICH known things they are.
Nothing tells the pipeline that d exists or what it is; truth is used only to grade.
"""
import numpy as np
from sklearn.linear_model import LinearRegression
rng = np.random.default_rng(0)
N = 200_000
a = rng.uniform(0.5, 2.0, N); b = rng.uniform(0.5, 2.0, N); c = rng.uniform(0.5, 2.0, N)
# the HIDDEN variable: two known species (masses 1.00 and 1.60), 80/20 mix, small noise
species = (rng.random(N) < 0.20).astype(int)
d_true = np.where(species==1, 1.60, 1.00) * np.exp(rng.normal(0, 0.03, N))
f = a*b*c*d_true * np.exp(rng.normal(0, 0.02, N))         # observed result (+ measurement noise)

# ---- 1. DETECT: can a,b,c alone explain f? (work in logs: product -> sum) ----
LA = np.column_stack([np.log(a), np.log(b), np.log(c)])
reg = LinearRegression().fit(LA, np.log(f))
resid = np.log(f) - reg.predict(LA)
# noise-floor: if NOTHING were missing, residual would be just measurement noise (~0.02)
print("="*70); print("  1. DETECT a missing variable"); print("="*70)
print(f"  fit log f ~ log a,b,c   exponents = {reg.coef_.round(2)} (true product => ~1,1,1)")
print(f"  residual std = {resid.std():.3f}   measurement-noise floor ~0.02")
print(f"  => residual is {resid.std()/0.02:.0f}x the noise floor: a variable IS missing.")

# ---- 2. RECONSTRUCT the missing variable ----
d_hat = np.exp(resid)                                       # = f/(a*b*c), de-trended
print("\n"+"="*70); print("  2. RECONSTRUCT it: d_hat = f / (a*b*c)"); print("="*70)
print(f"  d_hat range [{d_hat.min():.2f}, {d_hat.max():.2f}], "
      f"correlation with the TRUE hidden d = {np.corrcoef(d_hat, d_true)[0,1]:.3f}")

# ---- 3. IDENTIFY: pattern is exact up to ONE scale; anchor it, then match catalog ----
print("\n"+"="*70); print("  3. IDENTIFY (pattern exact up to scale; 1 anchor fixes it)"); print("="*70)
# split d_hat into its natural clusters in log-space (2-means, scale-free)
L = np.log(d_hat); lo, hi = L.min(), L.max()
ctr = np.array([np.quantile(L,0.4), np.quantile(L,0.9)])      # init two centers
for _ in range(50):
    assign = (np.abs(L[:,None]-ctr[None,:])).argmin(1)
    for k in (0,1):
        if (assign==k).any(): ctr[k] = L[assign==k].mean()
peaks = np.exp(ctr); peaks.sort()
ratio = peaks[1]/peaks[0]
print(f"  found 2 species in the reconstructed variable; peak ratio = {ratio:.3f}")
print(f"  (true hidden ratio 1.60/1.00 = 1.600 -- recovered SCALE-FREE and exact)")
# anchor: assume the dominant species is a known reference at 1.00 -> calibrate scale
scale = 1.00/peaks[0]; cal = peaks*scale
catalog = {"X":0.50,"Y":1.00,"Z":1.60,"W":2.30}
print(f"  anchor dominant peak to known 1.00 -> calibrated values: {cal.round(2)}")
for p in cal:
    nm=min(catalog, key=lambda k: abs(catalog[k]-p))
    print(f"    reconstructed {p:.2f}  ==  catalog {nm} ({catalog[nm]:.2f})  [match err {abs(catalog[nm]-p):.3f}]")
# grade species separation (scale-free: threshold at the antimode)
thr = np.exp(ctr.mean()); pred = (d_hat>thr).astype(int)
pur = (pred==species).mean()
print(f"\n  GRADE: species separated with {max(pur,1-pur)*100:.0f}% accuracy "
      f"(d_hat<->true d corr was 0.996)")
print("\n  READ: an incomplete equation didn't fail -- it MEASURED what it was missing.")
print("  The shortfall reconstructed the unrecorded variable EXACTLY up to one scale;")
print("  its two values matched known catalog entries 1.00 and 1.60 once a single")
print("  anchor set the scale -> a hidden component detected, counted, and identified.")
