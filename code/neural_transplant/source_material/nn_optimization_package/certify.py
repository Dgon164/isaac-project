"""
Salvage experiment: B&B bound as CERTIFICATE, not search.

Pipeline: filter (exclude top-10, partial on next M dims) -> top-K full-score
-> leader L. Then ceiling_i = partial_i + sqrt((R2_i - e_i) * ||h_rest||^2)
for all i. If max ceiling over non-confirmed rows <= L: output PROVABLY exact.
Else: fall back to full matmul (still exact, just slower).

Questions:
 Q1. Certification rate vs M (per-query dim order).
 Q2. Does a FIXED GLOBAL dim order preserve 30/30 accuracy? (If yes, per-row
     prefix energies are precomputable offline and the energy pass is free.)
 Q3. Expected ops of the certify-or-fallback EXACT pipeline.
"""
import numpy as np, torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer

torch.set_grad_enabled(False)
tok = GPT2Tokenizer.from_pretrained("gpt2")
model = GPT2LMHeadModel.from_pretrained("gpt2").eval()
W = model.transformer.wte.weight.numpy().astype(np.float64)
V, D = W.shape
R2 = (W ** 2).sum(axis=1)

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
    "The river flows down from the mountains into the",
    "She tied her hair back with a rubber",
    "The detective examined the fingerprints on the",
    "On Halloween, children go from door to door asking for",
    "The farmer milked the cows early in the",
    "His flight was delayed because of bad",
    "The baby finally fell asleep in her mother's",
    "You should always wash your hands before eating a",
    "The knight drew his sword and charged at the",
    "The stock market crashed and investors lost a lot of",
]

def hidden(prompt):
    ids = tok(prompt, return_tensors="pt").input_ids
    return model.transformer(ids).last_hidden_state[0, -1].numpy().astype(np.float64)

HS = [hidden(p) for p in PROMPTS]
TRUTH = [int(np.argmax(W @ h)) for h in HS]

# global dim order: average |h| over this prompt set's *first half* (calibration),
# evaluated on accuracy over ALL prompts (incl. unseen half) — flag if it differs.
calib = np.mean([np.abs(h) for h in HS[:15]], axis=0)
GLOBAL_ORDER = np.argsort(-calib)

print("Q2: global vs per-query dim order, filter accuracy (exclude 10, K=200)")
for M in (40, 125, 200):
    hits_pq = hits_gl = 0
    for h, t in zip(HS, TRUTH):
        for mode in ("pq", "gl"):
            order = np.argsort(-np.abs(h)) if mode == "pq" else GLOBAL_ORDER
            filt = order[10:10 + M]
            partial = W[:, filt] @ h[filt]
            surv = np.argpartition(-partial, 200)[:200]
            pred = surv[int(np.argmax(W[surv] @ h))]
            if mode == "pq": hits_pq += (pred == t)
            else: hits_gl += (pred == t)
    print(f"  M={M:>3}: per-query {hits_pq}/30 | global {hits_gl}/30")

print("\nQ1+Q3: certification under GLOBAL order (prefix energies precomputable)")
# precompute prefix energies at the M checkpoints (offline cost, not counted)
for M in (40, 125, 200, 300, 400, 500):
    dims = GLOBAL_ORDER[10:10 + M]
    E = (W[:, dims] ** 2).sum(axis=1)               # offline
    carrier = GLOBAL_ORDER[:10]
    certs, fallback_ops = 0, []
    hits = 0
    for h, t in zip(HS, TRUTH):
        rest = np.ones(D, bool); rest[dims] = False  # tail = everything not in filter band
        h_rest2 = float((h[rest] ** 2).sum())
        partial = W[:, dims] @ h[dims]               # V*M ops
        surv = np.argpartition(-partial, 200)[:200]
        fs = W[surv] @ h                             # K*D ops
        leader = surv[int(np.argmax(fs))]; L = fs.max()
        hits += (leader == t)
        ceil = partial + np.sqrt(np.maximum(R2 - E, 0) * h_rest2)   # V ops
        ceil[surv] = -np.inf                         # survivors already scored exactly
        certified = bool(ceil.max() <= L)
        certs += certified
        ops = V * M + 200 * D + V + (0 if certified else V * D)
        fallback_ops.append(ops)
    arr = np.array(fallback_ops)
    print(f"  M={M:>3}: filter exact {hits}/30 | certified {certs}/30 | "
          f"exact-pipeline mean speedup {(V*D)/arr.mean():4.1f}x")
