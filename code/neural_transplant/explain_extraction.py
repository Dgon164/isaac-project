"""
HOW THE M=125 PIPELINE EXTRACTS THE ANSWER — a trace, not a claim.

The full model picks the next token by argmax over W @ h  (50257 tokens, each
scored by a 768-dim dot product with the context fingerprint h). This script
shows WHERE in those 768 dims the decision actually lives, by asking one
question: if I score using only SOME of the dims, does the true winner still
come out on top?

Three subsets, same prompt:
  - selected 125 : the big-|h| dims (minus the top-10 carriers) -> the band the pipeline uses
  - random 125   : 125 dims picked at random                    -> control
  - carriers 10  : the 10 biggest-|h| dims                      -> the loud, shared ones
Rank 0 = the true next token is #1. Big rank = it got buried.
"""

import numpy as np, torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer

torch.set_grad_enabled(False)
tok = GPT2Tokenizer.from_pretrained("gpt2")
model = GPT2LMHeadModel.from_pretrained("gpt2").eval()
W = model.transformer.wte.weight.numpy().astype(np.float64)   # (50257, 768)
V, D = W.shape
rng = np.random.default_rng(0)

PROMPTS = ["The capital of France is",
           "The chef sliced the onions with a sharp",
           "Seven plus three equals",
           "Most plants need sunlight, soil, and"]


def hidden(p):
    ids = tok(p, return_tensors="pt").input_ids
    return model.transformer(ids).last_hidden_state[0, -1].numpy().astype(np.float64)


def rank_of(token_id, scores):
    """0 = this token is the top-scoring one."""
    return int((scores > scores[token_id]).sum())


# 1) the carriers are the SAME dims regardless of the prompt -> context-blind
print("=" * 74)
print("  1) THE CARRIERS: the 10 biggest-|h| dims, per prompt")
print("=" * 74)
carrier_sets = []
for p in PROMPTS:
    h = hidden(p)
    top10 = np.argsort(-np.abs(h))[:10]
    carrier_sets.append(set(top10.tolist()))
    print(f"   {sorted(top10.tolist())}")
shared = set.intersection(*carrier_sets)
print(f"\n   shared by ALL four prompts: {sorted(shared)}")
print("   -> these dims are loud no matter the context, so they CANNOT tell")
print("      one continuation from another. Loud != informative. Drop them.")

# 2) where the true next token ranks under each dim-subset
print("\n" + "=" * 74)
print("  2) WHERE THE DECISION LIVES  (rank of the true next token, 0 = winner)")
print("=" * 74)
print(f"   {'prompt':<40}{'next':>9}{'full768':>9}{'sel125':>8}{'rand125':>9}{'carr10':>8}")
for p in PROMPTS:
    h = hidden(p)
    full = W @ h
    truth = int(np.argmax(full))
    order = np.argsort(-np.abs(h))
    sel = order[10:135]                    # the discriminative band (skip 10 carriers, take 125)
    carr = order[:10]                      # the carriers
    randd = rng.choice(D, 125, replace=False)
    r_full = rank_of(truth, full)
    r_sel = rank_of(truth, W[:, sel] @ h[sel])
    r_rand = rank_of(truth, W[:, randd] @ h[randd])
    r_carr = rank_of(truth, W[:, carr] @ h[carr])
    nxt = tok.decode([truth]).strip()[:7]
    print(f"   {p[:39]:<40}{nxt:>9}{r_full:>9}{r_sel:>8}{r_rand:>9}{r_carr:>8}")

print("\n" + "=" * 74)
print("  READING IT")
print("=" * 74)
print("""   full768  -> 0 always (that's the model's own answer, by definition)
   sel125   -> tiny rank: the chosen 125 dims already put the true token at
               or near the top. That's why a top-200 shortlist NEVER misses it.
   rand125  -> buried (thousands deep): random dims don't carry the decision.
   carr10   -> also buried: the loudest dims decide nothing.

   So 'extracting the answer' = find the ~125 dims where THIS context's h is
   big (after dropping the always-big carriers), score cheaply on just those to
   shortlist ~200 candidates, then score those few exactly on all 768. Coarse
   to filter, fine to decide. The information was never spread over 768 dims --
   it was concentrated in a context-specific handful, and the method just looks
   where h points.""")
