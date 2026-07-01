# Full-scale HIGGS detector on the whole 11M-row file. GPU. Single deterministic equation.
import numpy as np, pandas as pd, time, warnings; warnings.filterwarnings("ignore")
import torch, torch.nn as nn
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
dev="cuda" if torch.cuda.is_available() else "cpu"; torch.manual_seed(0)
print("device:", torch.cuda.get_device_name(0) if dev=="cuda" else "cpu")
t0=time.time()
print("loading full HIGGS (11M rows)...")
D=pd.read_csv("HIGGS.csv.gz",header=None,compression="gzip").values.astype(np.float32)
print(f"  loaded {D.shape[0]:,} rows in {time.time()-t0:.0f}s")
y=D[:,0]; X=D[:,1:]
# standard split used in the literature: last 500k = test
Xtr,ytr=X[:-500_000],y[:-500_000]; Xte,yte=X[-500_000:],y[-500_000:]
s=StandardScaler().fit(Xtr); Xtr=s.transform(Xtr).astype(np.float32); Xte=s.transform(Xte).astype(np.float32)
print(f"  train {len(Xtr):,}  test {len(Xte):,}")

class H(nn.Module):
    def __init__(s):
        super().__init__()
        def blk(a,b): return [nn.Linear(a,b),nn.BatchNorm1d(b),nn.ReLU(),nn.Dropout(0.05)]
        s.body=nn.Sequential(*blk(28,512),*blk(512,512),*blk(512,256),*blk(256,128)); s.head=nn.Linear(128,1)
    def forward(s,x): return s.head(s.body(x)).squeeze(1)
net=H().to(dev); opt=torch.optim.Adam(net.parameters(),2e-3,weight_decay=1e-5)
sched=torch.optim.lr_scheduler.OneCycleLR(opt,2e-3,epochs=24,steps_per_epoch=(len(Xtr)//8192)+1)
lf=nn.BCEWithLogitsLoss()
Xt=torch.tensor(Xtr,device=dev); yt=torch.tensor(ytr,device=dev)
Xv=torch.tensor(Xte,device=dev); yv=torch.tensor(yte,device=dev)
bs=8192
for ep in range(24):
    net.train(); p=torch.randperm(len(Xt),device=dev)
    for i in range(0,len(Xt),bs):
        idx=p[i:i+bs]; opt.zero_grad(); loss=lf(net(Xt[idx]),yt[idx]); loss.backward(); opt.step(); sched.step()
    if ep%4==3 or ep==0:
        net.eval()
        with torch.no_grad():
            pr=[]
            for i in range(0,len(Xv),65536): pr.append(torch.sigmoid(net(Xv[i:i+65536])).cpu().numpy())
        pr=np.concatenate(pr); auc=roc_auc_score(yte,pr); acc=((pr>0.5)==yte).mean()
        print(f"  epoch {ep+1:>2}  test acc {acc:.4f}  AUC {auc:.4f}  ({time.time()-t0:.0f}s)")
net.eval()
with torch.no_grad():
    pr=[]
    for i in range(0,len(Xv),65536): pr.append(torch.sigmoid(net(Xv[i:i+65536])).cpu().numpy())
pr=np.concatenate(pr)
print("\n=== FULL-SCALE HIGGS DETECTOR ===")
print(f"  accuracy {((pr>0.5)==yte).mean():.4f}   AUC {roc_auc_score(yte,pr):.4f}")
print(f"  (Baldi 2014 deep-learning ceiling: AUC ~0.88)   total {time.time()-t0:.0f}s")
