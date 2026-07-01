"""ONE equation, evaluated once per event, that says 'this is the Higgs'.
Not short, not readable -- fully determined. All 28 sensors allowed. Every constant
pinned by the data. H(x) is a single deterministic function: plug in 28 numbers, out
comes a Higgs score; threshold it once -> Higgs / background.
"""
import numpy as np, pandas as pd, warnings; warnings.filterwarnings("ignore")
import torch, torch.nn as nn
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
dev="cuda" if torch.cuda.is_available() else "cpu"; torch.manual_seed(0)
F="HIGGS.csv.gz"; N=2_000_000
print(f"loading {N:,} rows ...")
D=pd.read_csv(F,header=None,nrows=N,compression="gzip").values.astype(np.float32)
y=D[:,0]; X=D[:,1:]
ntr=int(N*0.9); s=StandardScaler().fit(X[:ntr])
Xtr=s.transform(X[:ntr]).astype(np.float32); Xte=s.transform(X[ntr:]).astype(np.float32)
ytr,yte=y[:ntr],y[ntr:]

class H(nn.Module):
    def __init__(s):
        super().__init__()
        s.f=nn.Sequential(nn.Linear(28,256),nn.ReLU(),nn.Linear(256,256),nn.ReLU(),
                          nn.Linear(256,128),nn.ReLU(),nn.Linear(128,1))
    def forward(s,x): return s.f(x).squeeze(1)
net=H().to(dev); opt=torch.optim.Adam(net.parameters(),1e-3,weight_decay=1e-5)
lf=nn.BCEWithLogitsLoss()
Xt=torch.tensor(Xtr,device=dev); yt=torch.tensor(ytr,device=dev)
Xv=torch.tensor(Xte,device=dev)
bs=4096
for ep in range(40):
    net.train(); p=torch.randperm(len(Xt),device=dev)
    for i in range(0,len(Xt),bs):
        idx=p[i:i+bs]; opt.zero_grad(); loss=lf(net(Xt[idx]),yt[idx]); loss.backward(); opt.step()
net.eval()
with torch.no_grad(): logit=net(Xv).cpu().numpy()
prob=1/(1+np.exp(-logit)); pred=(prob>0.5).astype(int)
acc=(pred==yte).mean(); auc=roc_auc_score(yte,prob)

print("\n"+"="*68); print("  THE DETECTOR EQUATION  H(x): 28 sensors -> Higgs score"); print("="*68)
W=[p.detach().cpu().numpy() for p in net.f.parameters()]
print("  H(x) = sigmoid( W4 . relu( W3 . relu( W2 . relu( W1 . x_std + b1 )")
print("                              + b2 ) + b3 ) + b4 )")
print(f"  where x_std = (x - mu)/sigma  (28 sensors), and the constants are fixed:")
print(f"     W1:{W[0].shape}  W2:{W[2].shape}  W3:{W[4].shape}  W4:{W[6].shape}")
print(f"     total pinned constants = {sum(w.size for w in W) + 56}  (all determined by data)")
print(f"\n  RULE:  H(x) > 0.5  =>  'this is the Higgs'")
print("  " + "-"*64)
print(f"  held-out accuracy = {acc:.3f}   AUC = {auc:.3f}   (chance 0.53)")

print("\n  run it ONCE on individual events (28 numbers in -> verdict out):")
for i in [0,1,2,3,4]:
    verdict="HIGGS " if pred[ntr*0+i]>0 else "backgr"
    truth ="HIGGS " if yte[i]>0 else "backgr"
    print(f"     event {i}:  H = {prob[i]:.3f}  ->  {verdict}   (truth: {truth})")
print("\n  READ: a single deterministic equation, evaluated once per event, returns the")
print("  Higgs verdict. Not short, not readable -- but fully pinned and runnable. The")
print("  number (acc/AUC) is the data+model ceiling here; full deep training pushes ~0.88.")
