"""Deep net (torch, GPU) on raw channels only -- does DEPTH sharpen discovery?
Same product test: 21 raw channels in, 7 masses withheld, grade the latent.
"""
import numpy as np, warnings; warnings.filterwarnings("ignore")
import torch, torch.nn as nn
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge, LogisticRegression
dev = "cuda" if torch.cuda.is_available() else "cpu"
torch.manual_seed(0)

d=fetch_openml(data_id=23512,as_frame=False)
X=np.asarray(d.data,np.float32); names=list(d.feature_names)
y=np.asarray(d.target); y=(y=="1").astype(int) if y.dtype==object else (y.astype(float)>.5).astype(int)
ok=~np.isnan(X).any(1); X,y=X[ok],y[ok].astype(np.float32)
low=list(range(21)); high=list(range(21,28)); hin=[names[j] for j in high]
Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=.15,random_state=0,stratify=y)
s=StandardScaler().fit(Xtr[:,low])
Ltr=s.transform(Xtr[:,low]).astype(np.float32); Lte=s.transform(Xte[:,low]).astype(np.float32)
sm=StandardScaler().fit(Xtr[:,high])
Mtr=sm.transform(Xtr[:,high]).astype(np.float32); Mte=sm.transform(Xte[:,high]).astype(np.float32)  # withheld

class Net(nn.Module):
    def __init__(s,w=300,L=5):
        super().__init__()
        layers=[]; d=21
        for _ in range(L):
            layers+=[nn.Linear(d,w),nn.BatchNorm1d(w),nn.ReLU(),nn.Dropout(.1)]; d=w
        s.body=nn.Sequential(*layers); s.head=nn.Linear(w,1)
    def forward(s,x): h=s.body(x); return s.head(h).squeeze(1), h

net=Net().to(dev)
opt=torch.optim.Adam(net.parameters(),1e-3,weight_decay=1e-5)
lossf=nn.BCEWithLogitsLoss()
Xt=torch.tensor(Ltr,device=dev); yt=torch.tensor(ytr,device=dev)
Xv=torch.tensor(Lte,device=dev); yv=torch.tensor(yte,device=dev)
bs=2048; n=len(Xt)
print("="*66); print("  DEEP NET (5x300, torch/GPU) on 21 raw channels, masses HIDDEN"); print("="*66)
for ep in range(60):
    net.train(); perm=torch.randperm(n,device=dev)
    for i in range(0,n,bs):
        idx=perm[i:i+bs]; opt.zero_grad()
        out,_=net(Xt[idx]); loss=lossf(out,yt[idx]); loss.backward(); opt.step()
    if ep%15==14 or ep==0:
        net.eval()
        with torch.no_grad():
            o,_=net(Xv); acc=((o>0).float()==yv).float().mean().item()
        print(f"   epoch {ep+1:>2}  test acc {acc:.3f}")
net.eval()
with torch.no_grad():
    o,Hv=net(Xv); accf=((o>0).float()==yv).float().mean().item()
    _,Ht=net(Xt)
H_te=Hv.cpu().numpy(); H_tr=Ht.cpu().numpy()
logi=(LogisticRegression(max_iter=500).fit(Ltr,ytr).predict(Lte)==yte).mean()
ev=np.sort(np.linalg.eigvalsh(np.cov((H_te-H_te.mean(0)).T)))[::-1]; ev=ev[ev>1e-9]
pr=(ev.sum()**2)/(ev**2).sum()
print(f"\n  final: logistic {logi:.3f} | DEEP net {accf:.3f} | shallow-net(prev) 0.658")
print(f"  effective hidden quantities (participation ratio) = {pr:.1f}  (prev shallow 9.8)")
print(f"\n  DISCOVERY GRADE — withheld masses reconstructed from the deep latent:")
print(f"    {'mass (hidden)':<16}{'linear(raw)':>13}{'deep latent':>13}{'discovered?':>13}")
for k,nm in enumerate(hin):
    r2l=Ridge(1).fit(Ltr,Mtr[:,k]).score(Lte,Mte[:,k])
    r2n=Ridge(1).fit(H_tr,Mtr[:,k]).score(H_te,Mte[:,k])
    flag="YES" if r2n>0.6 and r2n-r2l>0.15 else ("partial" if r2n>0.4 else "no")
    print(f"    {nm:<16}{r2l:>13.3f}{r2n:>13.3f}{flag:>13}")
print("\n  READ: did DEPTH (vs the shallow net) recover the masses better and compress")
print("  to fewer effective quantities? if yes, the full 11M-row run is justified.")
