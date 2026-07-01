"""
Two experiments, June 10 2026 session.

EXP 1 — "We know the slopes" (the weights-only claim).
Steel-man: the sorted-cosine/logit curve is ~97% shared across prompts, so
precompute the shared part from W alone; runtime adds a correction.
Killer test: split each prompt's logits into
    shared part   = the mean logit profile over OTHER prompts (best possible
                    weights-only predictor: it contains every input-independent
                    regularity — norms, centroid, strata, carrier baseline)
    residual      = this prompt's logits - shared part
Measure: (a) correlation of full logits with shared part (his 97% claim),
         (b) top-1 accuracy of shared part alone,
         (c) top-1 accuracy of residual alone,
         (d) what fraction of the winner's margin lives in the residual.

EXP 2 — What QKV actually does (his stated gap).
"The capital of France is" vs "...Japan is":
  (a) verify last-token INPUT vectors are bit-identical (the killer premise);
  (b) show final hidden states differ -> something context-dependent intervened;
  (c) find which attention heads at the last position attend to 'France'/'Japan';
  (d) ablate: replace the France prompt's attention pattern at the last position
      with uniform attention in one layer at a time -> where does ' Paris' die?
"""
import numpy as np, torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer

torch.set_grad_enabled(False)
tok = GPT2Tokenizer.from_pretrained("gpt2")
model = GPT2LMHeadModel.from_pretrained("gpt2").eval()
W = model.transformer.wte.weight.numpy().astype(np.float64)
V, D = W.shape

PROMPTS = [
    "The chef sliced the onions with a sharp",
    "After the storm, the streets were covered in",
    "She opened the envelope and found a",
    "The opposite of expensive is",
    "Water freezes at a temperature of",
    "He plugged the charger into the",
    "The museum's most famous painting was stolen last",
    "To bake bread you first need to mix flour and",
    "The dog barked loudly at the",
    "Seven plus three equals",
    "The judge sentenced the defendant to ten years in",
    "Her favorite season of the year is",
    "The astronauts landed safely on the",
    "I forgot my umbrella, so I got soaked in the",
    "The teacher wrote the equation on the",
    "Most plants need sunlight, soil, and",
    "The orchestra was led by a famous",
    "He locked the door and put the key in his",
    "The library was quiet except for the sound of",
    "Before surgery, the patient was given a general",
]

def hidden(prompt):
    ids = tok(prompt, return_tensors="pt").input_ids
    return model.transformer(ids).last_hidden_state[0, -1].numpy().astype(np.float64)

print("=" * 70)
print("EXP 1: how much of the answer is in the weights-only (shared) part?")
print("=" * 70)
L = np.stack([W @ hidden(p) for p in PROMPTS])          # (P, V) logits
corr_full_shared, top1_shared, top1_resid, margin_frac = [], 0, 0, []
for i in range(len(PROMPTS)):
    shared = L[np.arange(len(PROMPTS)) != i].mean(axis=0)   # leave-one-out
    full = L[i]; resid = full - shared
    truth = int(np.argmax(full))
    corr_full_shared.append(np.corrcoef(full, shared)[0, 1])
    top1_shared += (int(np.argmax(shared)) == truth)
    top1_resid  += (int(np.argmax(resid))  == truth)
    # margin decomposition: winner vs runner-up of the FULL logits
    ru = np.argsort(-full)[1]
    m_full = full[truth] - full[ru]
    m_resid = resid[truth] - resid[ru]
    margin_frac.append(m_resid / m_full)
print(f"corr(full logits, shared part): mean {np.mean(corr_full_shared):.3f}  <- 'we know the slopes' is TRUE")
print(f"top-1 from shared part alone : {top1_shared}/{len(PROMPTS)}")
print(f"top-1 from residual alone    : {top1_resid}/{len(PROMPTS)}")
print(f"fraction of winning margin in residual: mean {np.mean(margin_frac):.2f}")
shared_all = L.mean(axis=0)
print(f"shared part's own top-5 (what weights-only predicts for EVERY prompt): "
      f"{[tok.decode([t]) for t in np.argsort(-shared_all)[:5]]}")

print()
print("=" * 70)
print("EXP 2: what QKV does — France vs Japan, measured")
print("=" * 70)
pf, pj = "The capital of France is", "The capital of Japan is"
idf = tok(pf, return_tensors="pt").input_ids
idj = tok(pj, return_tensors="pt").input_ids
toks_f = [tok.decode([t]) for t in idf[0]]
print(f"tokens: {toks_f}")

# (a) last-token INPUT vector = wte[' is'] + pos_emb[last]; identical?
wte, wpe = model.transformer.wte.weight, model.transformer.wpe.weight
in_f = wte[idf[0, -1]] + wpe[idf.shape[1] - 1]
in_j = wte[idj[0, -1]] + wpe[idj.shape[1] - 1]
print(f"(a) last-token input vectors identical: {bool(torch.equal(in_f, in_j))}")

# (b) final hidden states
hf, hj = hidden(pf), hidden(pj)
print(f"(b) final hidden states equal: {np.allclose(hf, hj)} "
      f"(top-1: '{tok.decode([int(np.argmax(W@hf))])}' vs '{tok.decode([int(np.argmax(W@hj))])}')")

# (c) attention from last position to the country token, per layer (max over heads)
of = model(idf, output_attentions=True)
country_pos = 4  # 'The'(0) ' capital'(1) ' of'(2) ' France'(3)? verify:
country_pos = toks_f.index(" France")
print(f"(c) attention weight last-pos -> ' France' (max head per layer):")
row = []
for l, A in enumerate(of.attentions):
    a = A[0, :, -1, country_pos]           # (heads,)
    row.append(f"L{l}:{a.max():.2f}")
print("    " + "  ".join(row))

# (d) causal test: knock out attention's input-dependence at the last position,
# one layer at a time, by forcing uniform attention there. Where does Paris die?
import torch.nn.functional as F
pid = tok.encode(" Paris")[0]
base_logit = float(model(idf).logits[0, -1, pid])
base_rank = int((model(idf).logits[0, -1] > base_logit).sum()) + 1
print(f"(d) baseline ' Paris': logit {base_logit:.2f}, rank {base_rank}")

def uniform_attn_hook(module, args, kwargs, layer_store):
    pass  # placeholder; we patch differently below

# simpler causal test: zero the country token's VALUE contribution by masking
# attention to that position at the last query, layer by layer.
def run_with_mask(layer_idx):
    handles = []
    def hook(mod, inputs, output):
        return output
    # patch attention forward via monkey-typed mask on attn weights is invasive;
    # instead: ablate by replacing the ' France' token with ' the' at one layer's
    # input is not equivalent. Use attention masking through head_mask per layer:
    hm = torch.ones(12, 12)
    # head_mask zeroes entire heads, not positions — measure instead which LAYER's
    # attention output matters by zeroing attn output at last position:
    blk = model.transformer.h[layer_idx].attn
    def zero_last(mod, inp, out):
        a = out[0].clone()
        a[0, -1, :] = 0.0
        return (a,) + out[1:]
    h = blk.register_forward_hook(zero_last)
    logits = model(idf).logits[0, -1]
    h.remove()
    r = int((logits > logits[pid]).sum()) + 1
    return float(logits[pid]), r, tok.decode([int(logits.argmax())])

print("    zero attention OUTPUT at last position, one layer at a time:")
for l in range(12):
    lg, r, top = run_with_mask(l)
    flag = " <-- Paris dies" if r > 20 else ""
    print(f"    L{l:>2}: Paris logit {lg:7.2f} rank {r:>5}, top-1 '{top}'{flag}")
