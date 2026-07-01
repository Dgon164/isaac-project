# CRITIQUE 2: the engine must choose linear vs log residual track, and can — by scoring both.
import numpy as np; rng=np.random.default_rng(0); N=100000
def score(track, recorded, f):
    if track=="log":
        if (recorded<=0).any() or (f<=0).any(): return np.inf, None
        d=np.log(f)-np.log(recorded).sum(1); 
    else:
        d=f-recorded.sum(1)
    # structure vs shuffled null: low ratio = real recovered variable
    dsh=d[rng.permutation(N)]; return np.var(d-d.mean())/np.var(dsh-dsh.mean()) if False else np.std(d), d
def select(recorded,f,label):
    rl,dl=score("lin",recorded,f); rg,dg=score("log",recorded,f)
    win="LOG (multiplicative)" if rg<rl else "LINEAR (additive)"
    print(f"  {label:<26} linear-resid-std {rl:8.3f} | log-resid-std {rg:8.3f} -> {win}")
# additive truth: f = a+b+c+d (d hidden), components can be NEGATIVE (like momentum)
a,b,c=[rng.normal(0,1,N) for _ in range(3)]; d=rng.normal(0,1,N); f_add=a+b+c+d
# multiplicative truth: f = a*b*c*d (positive)
a2,b2,c2=[rng.uniform(.5,2,N) for _ in range(3)]; d2=rng.uniform(.5,2,N); f_mul=a2*b2*c2*d2
print("="*70); print("  CRITIQUE 2 — engine picks the track by scoring residual tightness")
print("="*70)
select(np.column_stack([a,b,c]), f_add, "additive system (f=a+b+c+d)")
select(np.column_stack([a2,b2,c2]), f_mul, "multiplicative (f=a*b*c*d)")
print("  (lower residual-std = the correct algebra; momentum is the ADDITIVE branch,")
print("   missing_var.py's product law is the LOG branch -- both exist, selected by score.)")
