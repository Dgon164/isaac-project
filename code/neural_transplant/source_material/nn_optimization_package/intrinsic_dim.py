"""
INTRINSIC DIMENSIONALITY OF GPT-2 REPRESENTATIONS — measured, June 10 2026.
Question (researcher): "even the most complicated things can be represented
and processed from 10-50 dims. i don't know why yet."

Four measurements on real corpus states (Pride & Prejudice, 20k positions):

 1. PCA spectrum + participation ratio  — linear effective dimensionality
 2. TwoNN intrinsic dimension (Facco 2017) — nonlinear manifold dimension
 3. DECISION sufficiency: project h onto top-k PCA dims, reconstruct, and
    measure top-1 agreement with the full model. How many dims does the
    DECISION need (vs the representation)?
 4. Random-projection control (Johnson-Lindenstrauss): same test with
    random k-dim subspaces — how much do the LEARNED directions matter?

Plus: do the top PCA directions align with the known carrier dims?
"""
import numpy as np, torch, re
from transformers import GPT2LMHeadModel, GPT2Tokenizer

torch.set_grad_enabled(False)
np.random.seed(0)
tok = GPT2Tokenizer.from_pretrained("gpt2")
model = GPT2LMHeadModel.from_pretrained("gpt2").eval()
W = model.transformer.wte.weight.numpy().astype(np.float32)
V, D = W.shape

text = re.sub(r"\s+", " ", open("pride.txt", encoding="utf-8").read()[1000:])
ids = tok(text, return_tensors="pt").input_ids[0][:24000]  # >1024 tokenizer warning is benign: we chunk at 256 below

H = []
CTX = 256
for s in range(0, 20000, CTX):
    out = model.transformer(ids[s:s+CTX].unsqueeze(0)).last_hidden_state[0]
    H.append(out.numpy().astype(np.float32))
H = np.concatenate(H)            # (~20000, 768)
print(f"states: {H.shape}")

# ---------- 1. PCA spectrum ----------
mu = H.mean(0)
Hc = H - mu
U, S, Vt = np.linalg.svd(Hc[:8000], full_matrices=False)
lam = S**2 / len(Hc[:8000])
pr = lam.sum()**2 / (lam**2).sum()                  # participation ratio
var = np.cumsum(lam) / lam.sum()
k90 = int(np.searchsorted(var, 0.90)) + 1
k99 = int(np.searchsorted(var, 0.99)) + 1
print(f"\n[1] PCA: participation ratio = {pr:.1f} effective dims")
print(f"    dims for 90% variance: {k90}   for 99%: {k99}")
print(f"    top-10 eigenvalue share: {var[9]:.1%}")

# carrier alignment: loadings of known carrier dims on PC1-3
CARRIERS = [496, 430, 36, 314, 374]
for pc in range(3):
    load = np.abs(Vt[pc][CARRIERS])
    print(f"    PC{pc+1}: |loading| on carriers {CARRIERS} = {np.round(load,2)} "
          f"(max possible 1.0; mean |loading| over all dims {np.abs(Vt[pc]).mean():.3f})")

# ---------- 2. TwoNN intrinsic dimension ----------
sub = H[np.random.choice(len(H), 3000, replace=False)].astype(np.float64)
n2 = (sub**2).sum(1); d2 = n2[:,None] + n2[None,:] - 2*(sub @ sub.T)
np.fill_diagonal(d2, np.inf)
r1 = np.sqrt(np.partition(d2, 0, axis=1)[:, 0])
r2 = np.sqrt(np.partition(d2, 1, axis=1)[:, 1])
mu_ratio = r2 / np.maximum(r1, 1e-12)
mu_ratio = mu_ratio[(mu_ratio > 1.0) & np.isfinite(mu_ratio)]  # NB: >1.0 also drops exact-tie duplicate states (harmless)
id_twonn = len(mu_ratio) / np.log(mu_ratio).sum()
print(f"\n[2] TwoNN intrinsic dimension: {id_twonn:.1f}")

# also on carrier-removed states (decision-relevant subspace)
subz = sub.copy(); subz[:, CARRIERS] = 0
n2 = (subz**2).sum(1); d2 = n2[:,None] + n2[None,:] - 2*(subz @ subz.T)
np.fill_diagonal(d2, np.inf)
r1 = np.sqrt(np.partition(d2, 0, axis=1)[:, 0])
r2 = np.sqrt(np.partition(d2, 1, axis=1)[:, 1])
mu_ratio = r2 / np.maximum(r1, 1e-12)
mu_ratio = mu_ratio[(mu_ratio > 1.0) & np.isfinite(mu_ratio)]
print(f"    TwoNN with carriers zeroed: {len(mu_ratio)/np.log(mu_ratio).sum():.1f}")

# ---------- 3. decision sufficiency under PCA truncation ----------
test = H[np.random.choice(len(H), 400, replace=False)]
truth = (test @ W.T).argmax(1)
print(f"\n[3] decision sufficiency: top-1 agreement after PCA-k reconstruction")
print(f"    {'k':>4} {'PCA agree':>10} {'random-k agree':>15}")
for k in (3, 5, 10, 20, 30, 50, 75, 100, 150, 200, 300):
    Vk = Vt[:k]
    rec = (test - mu) @ Vk.T @ Vk + mu
    a_pca = ((rec @ W.T).argmax(1) == truth).mean()
    # random k-dim subspace control (JL)
    R = np.linalg.qr(np.random.randn(D, k).astype(np.float32))[0].T
    rec_r = (test - mu) @ R.T @ R + mu
    a_rnd = ((rec_r @ W.T).argmax(1) == truth).mean()
    print(f"    {k:>4} {a_pca:>9.1%} {a_rnd:>14.1%}")
