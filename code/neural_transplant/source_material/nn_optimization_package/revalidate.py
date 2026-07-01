"""
Re-validation of the sparse output-layer pipeline (June 10, 2026 session).
Hypothesis under test: exclude top-10 |h| dims, partial-score on next M dims,
full-score top-K survivors -> exact top-1 match with the full model.
Handoff claims: M=125/K=200 -> 24/24 exact at 6.0x; M=40/K=200 -> 19/24 at 17.8x.

Prompt set: written fresh THIS session by the assistant, before any code ran.
Never seen by any prior session. Predictions (top-1 of full model) are computed
from the model itself = ground truth; the pipeline is the thing under test.
"""
import numpy as np, torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer

torch.set_grad_enabled(False)
tok = GPT2Tokenizer.from_pretrained("gpt2")
model = GPT2LMHeadModel.from_pretrained("gpt2").eval()
W = model.transformer.wte.weight.numpy().astype(np.float64)   # (50257, 768)
V, D = W.shape

# ---- chain of custody -------------------------------------------------------
ids = tok("The capital of France is", return_tensors="pt").input_ids
out = model(ids)
h = model.transformer(ids).last_hidden_state[0, -1].numpy().astype(np.float64)
logits_model = out.logits[0, -1].numpy().astype(np.float64)
logits_matmul = W @ h
print(f"[custody] lm_head bias: {model.lm_head.bias}")
print(f"[custody] tied: {model.lm_head.weight.data_ptr() == model.transformer.wte.weight.data_ptr()}")
print(f"[custody] max |model logits - W@h|: {np.abs(logits_model - logits_matmul).max():.2e}")
assert np.abs(logits_model - logits_matmul).max() < 1e-3

# ---- fresh prompt set (30, written blind this session) ----------------------
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

def pipeline(h, n_exclude=10, M=125, K=200):
    """Returns (predicted_token_id, ops)."""
    order = np.argsort(-np.abs(h))                 # dims by |magnitude|
    filt = order[n_exclude:n_exclude + M]          # discriminative band
    partial = W[:, filt] @ h[filt]                 # V x M ops
    surv = np.argpartition(-partial, K)[:K]
    full = W[surv] @ h                             # K x D ops
    return surv[int(np.argmax(full))], V * M + K * D

results = {}
for M, K in [(40, 200), (125, 200), (125, 500), (200, 200)]:
    hits, ops_total = 0, 0
    misses = []
    for p in PROMPTS:
        h = hidden(p)
        truth = int(np.argmax(W @ h))
        pred, ops = pipeline(h, 10, M, K)
        ops_total += ops
        if pred == truth: hits += 1
        else: misses.append((p, tok.decode([truth]), tok.decode([pred])))
    speed = (V * D) / (ops_total / len(PROMPTS))
    results[(M, K)] = (hits, speed, misses)
    print(f"\nM={M:>3} K={K:>3}: {hits}/{len(PROMPTS)} exact, {speed:.1f}x fewer ops")
    for p, t, g in misses:
        print(f"   MISS: '{p}' truth='{t}' got='{g}'")
