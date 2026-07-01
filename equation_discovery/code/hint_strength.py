"""Information never directly recorded is HINTED at in what was. The answer sheet
tells us how far the hints reach.

Recorded = 21 low-level kinematics. 'Unrecorded' (derived, not directly measured) =
the 7 invariant masses + the signal/background label = the ANSWER SHEET. Measure how
well each is reconstructable from the recorded hints alone (R2 on held-out). High =
strongly hinted, recoverable; low = genuinely gone. The answer sheet is the validator.
"""
import numpy as np, pandas as pd, warnings; warnings.filterwarnings("ignore")
from sklearn.ensemble import HistGradientBoostingRegressor as HGBR, HistGradientBoostingClassifier as HGBC
from sklearn.linear_model import Ridge
F="HIGGS.csv.gz"; N=300_000
D=pd.read_csv(F,header=None,nrows=N,compression="gzip").values.astype(np.float32)
y=D[:,0]; X=D[:,1:]; low=X[:,:21]; masses=X[:,21:28]
names=["m_jj","m_jjj","m_lv","m_jlv","m_bb","m_wbb","m_wwbb"]
tr=slice(0,N*3//4); te=slice(N*3//4,N)

print("="*66); print("  HINT STRENGTH — how well does recorded data hint the unrecorded?")
print("  (validated by the answer sheet)"); print("="*66)
print(f"  {'unrecorded quantity':<22}{'linear hint':>12}{'full hint':>11}")
for j,nm in enumerate(names):
    t=masses[:,j]
    rl=Ridge(1).fit(low[tr],t[tr]).score(low[te],t[te])
    rf=HGBR(max_iter=250,random_state=0).fit(low[tr],t[tr]).score(low[te],t[te])
    bar="#"*int(max(rf,0)*30)
    print(f"  {nm:<22}{rl:>12.3f}{rf:>11.3f}  {bar}")
# the ultimate unrecorded thing: the Higgs itself (the label), hinted by kinematics
acc=(HGBC(max_iter=250,random_state=0).fit(low[tr],y[tr]).predict(low[te])==y[te]).mean()
print(f"\n  the Higgs itself (label) from recorded kinematics: {acc:.3f}  (chance 0.53)")
print("\n  READ: every 'missing' mass is hinted at to a measurable degree (full hint R2),")
print("  and the Higgs decision itself is hinted above chance. The answer sheet turned")
print("  'unrecoverable' into a NUMBER: how far the hints reach for each quantity. That")
print("  number is what calibrates trust when there is NO answer sheet.")
