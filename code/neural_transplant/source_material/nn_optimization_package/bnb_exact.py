"""
Branch-and-bound EXACT output search (first implementation — June 10, 2026).

Idea (from handoff §2): process dims incrementally; for each vocab row keep a
running partial score s_i and running 'spent' energy e_i = sum of w_i[d]^2 over
processed dims. With precomputed full row norms R_i = ||w_i||^2, Cauchy-Schwarz
gives a provable ceiling on the unseen remainder:

    full_i <= s_i + sqrt((R_i - e_i) * ||h_tail||^2)

Maintain a confirmed lower bound L = exact full score of the current leader.
Prune every row whose ceiling < L. When one row remains (or dims exhaust),
the survivor's exact score wins. Exact at ANY depth — no accuracy knob.

Also tested: dim processing ORDER.
  order A: decreasing |h[d]|              (the original heuristic)
  order B: decreasing |h[d]| * std(W[:,d]) (discriminative power: how much a
           dim can SEPARATE rows, not how loud it is)
Prediction: B prunes faster, because carrier dims are loud but uniform —
they raise every ceiling equally and separate nothing.
"""
import numpy as np, torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer

torch.set_grad_enabled(False)
tok = GPT2Tokenizer.from_pretrained("gpt2")
model = GPT2LMHeadModel.from_pretrained("gpt2").eval()
W = model.transformer.wte.weight.numpy().astype(np.float64)
V, D = W.shape
R2 = (W ** 2).sum(axis=1)            # precomputed once, offline
COLSTD = W.std(axis=0)               # precomputed once, offline

PROMPTS = [  # same fresh set as revalidate.py
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

def bnb(h, ordering="power", chunk=8, prefilter_M=0, prefilter_K=0):
    """Exact branch-and-bound argmax of W @ h. Returns (token_id, ops)."""
    ops = 0
    if ordering == "mag":
        order = np.argsort(-np.abs(h))
    else:  # discriminative power
        order = np.argsort(-(np.abs(h) * COLSTD))

    # optional stage-0: the validated cheap filter proposes a leader to set L high early
    if prefilter_M:
        magorder = np.argsort(-np.abs(h))
        filt = magorder[10:10 + prefilter_M]
        partial = W[:, filt] @ h[filt]; ops += V * prefilter_M
        cand = np.argpartition(-partial, prefilter_K)[:prefilter_K]
        fs = W[cand] @ h; ops += prefilter_K * D
        leader = cand[int(np.argmax(fs))]; L = fs.max()
    else:
        leader, L = -1, -np.inf

    alive = np.arange(V)
    s = np.zeros(V)            # running partial scores (alive-indexed below)
    e = np.zeros(V)            # running spent energy
    h_tail2 = float((h ** 2).sum())

    pos = 0
    while pos < D and len(alive) > 1:
        dims = order[pos:pos + chunk]
        pos += len(dims)
        Wb = W[np.ix_(alive, dims)]
        s[alive] += Wb @ h[dims]
        e[alive] += (Wb ** 2).sum(axis=1)
        ops += 2 * len(alive) * len(dims)
        h_tail2 -= float((h[dims] ** 2).sum())

        # confirm the current partial leader exactly (raises L)
        top = alive[int(np.argmax(s[alive]))]
        if top != leader:
            sc = float(W[top] @ h); ops += D
            if sc > L: L, leader = sc, top

        ceil = s[alive] + np.sqrt(np.maximum(R2[alive] - e[alive], 0) * max(h_tail2, 0))
        alive = alive[ceil >= L]
        ops += len(alive)  # bound arithmetic, counted conservatively

    if len(alive) >= 1:
        fs = W[alive] @ h; ops += len(alive) * D
        i = int(np.argmax(fs))
        if fs[i] > L: leader = alive[i]
    return int(leader), ops

full_ops = V * D
for label, kw in [("B&B, |h| order",          dict(ordering="mag")),
                  ("B&B, |h|*std order",      dict(ordering="power")),
                  ("B&B power + M=40 seed",   dict(ordering="power", prefilter_M=40, prefilter_K=50)),
                  ("B&B power + M=125 seed",  dict(ordering="power", prefilter_M=125, prefilter_K=50))]:
    hits, ops_all, worst = 0, [], 0
    for p in PROMPTS:
        h = hidden(p)
        truth = int(np.argmax(W @ h))
        pred, ops = bnb(h, **kw)
        hits += (pred == truth)
        ops_all.append(ops)
    arr = np.array(ops_all)
    print(f"{label:<26} {hits}/{len(PROMPTS)} exact | mean {full_ops/arr.mean():5.1f}x | "
          f"median {full_ops/np.median(arr):5.1f}x | worst {full_ops/arr.max():5.1f}x")
