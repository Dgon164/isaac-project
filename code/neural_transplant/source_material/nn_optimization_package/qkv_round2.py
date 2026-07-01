"""
QKV mechanics, round 2 (eager attention so weights are visible).
(c) attention from last position to ' France', per layer/head
(e) block attention TO the France position at ALL layers -> does Paris die?
(f) activation patching: copy the Japan prompt's residual at the country
    position into the France run, one layer at a time -> when does the
    answer flip to Tokyo? (= where the country info has migrated)
"""
import numpy as np, torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer

torch.set_grad_enabled(False)
tok = GPT2Tokenizer.from_pretrained("gpt2")
model = GPT2LMHeadModel.from_pretrained("gpt2", attn_implementation="eager").eval()
W = model.transformer.wte.weight.numpy().astype(np.float64)

pf, pj = "The capital of France is", "The capital of Japan is"
idf = tok(pf, return_tensors="pt").input_ids
idj = tok(pj, return_tensors="pt").input_ids
CPOS = [tok.decode([t]) for t in idf[0]].index(" France")
pid_paris = tok.encode(" Paris")[0]
pid_tokyo = tok.encode(" Tokyo")[0]

out = model(idf, output_attentions=True)
print("(c) attention last-pos -> ' France', max over heads (and which head):")
for l, A in enumerate(out.attentions):
    a = A[0, :, -1, CPOS]
    print(f"    L{l:>2}: max {a.max():.3f} (head {int(a.argmax())})   "
          f"mean over heads {a.mean():.3f}")

logits = out.logits[0, -1]
r0 = int((logits > logits[pid_paris]).sum()) + 1
print(f"\nbaseline: ' Paris' rank {r0}, ' Tokyo' rank "
      f"{int((logits > logits[pid_tokyo]).sum()) + 1}")

# (e) forbid every layer from attending to the France position
def make_blocker():
    hooks = []
    for blk in model.transformer.h:
        def hook(mod, args, kwargs):
            am = torch.zeros(1, 1, idf.shape[1], idf.shape[1])
            am[:, :, :, CPOS] = torch.finfo(torch.float32).min
            kwargs = dict(kwargs); kwargs["attention_mask"] = am
            return args, kwargs
        hooks.append(blk.attn.register_forward_pre_hook(hook, with_kwargs=True))
    return hooks
hooks = make_blocker()
lg = model(idf).logits[0, -1]
for h in hooks: h.remove()
rp = int((lg > lg[pid_paris]).sum()) + 1
print(f"(e) attention to ' France' blocked at ALL layers: ' Paris' rank {r0} -> {rp}, "
      f"top-5 now: {[tok.decode([t]) for t in torch.argsort(-lg)[:5]]}")

# (f) activation patching: residual stream at country position, Japan -> France run
states_j = model(idj, output_hidden_states=True).hidden_states  # 13 tensors
print("\n(f) patch Japan's residual at the country position into the France run:")
print("    (after this layer, the France run carries Japan's info at that slot)")
for L in range(13):
    patched = {}
    def hook_factory(layer_idx):
        def hook(mod, inputs):
            x = inputs[0].clone()
            x[0, CPOS] = states_j[layer_idx][0, CPOS]
            return (x,) + inputs[1:]
        return hook
    if L < 12:
        h = model.transformer.h[L].register_forward_pre_hook(hook_factory(L))
        lg = model(idf).logits[0, -1]
        h.remove()
    else:
        continue
    rP = int((lg > lg[pid_paris]).sum()) + 1
    rT = int((lg > lg[pid_tokyo]).sum()) + 1
    top = tok.decode([int(lg.argmax())])
    print(f"    patch before L{L:>2}: Paris rank {rP:>4}  Tokyo rank {rT:>4}  top-1 '{top}'")
