"""
"Just map the outputs, direct search, no precompute, just direct lookup."
Bench: can a lookup table of (hidden state -> model's answer) replace the head?

Datastore: run GPT-2 over real text (Pride & Prejudice), store the final
hidden state at each position + the model's own argmax token there.
Query: on HELD-OUT text from the same book, take each hidden state, find the
nearest stored state (euclidean), output its stored token. No matmul over V.

Measure: top-1 agreement with the full model, as a function of datastore size,
and the lookup's op cost vs the head matmul (V=50,257 rows is the breakeven).
Two key variants: raw states vs carrier-zeroed states (his filtering point).
"""
import numpy as np, torch, re
from transformers import GPT2LMHeadModel, GPT2Tokenizer

torch.set_grad_enabled(False)
tok = GPT2Tokenizer.from_pretrained("gpt2")
model = GPT2LMHeadModel.from_pretrained("gpt2").eval()
W = model.transformer.wte.weight.numpy().astype(np.float32)
V, D = W.shape

text = open("pride.txt", encoding="utf-8").read()
text = re.sub(r"\s+", " ", text[1000:])           # strip header noise
ids = tok(text, return_tensors="pt").input_ids[0]
print(f"corpus tokens: {len(ids)}")

CTX = 256
def states_for(span):
    """Final hidden states + model argmax for each position in span (with context)."""
    H, A = [], []
    for start in range(span.start, span.stop, CTX):
        chunk = ids[max(0, start - CTX):start + CTX]
        off = min(start, CTX)
        out = model.transformer(chunk.unsqueeze(0)).last_hidden_state[0]
        hs = out[off:off + CTX].numpy().astype(np.float32)
        lg = hs @ W.T
        H.append(hs); A.append(lg.argmax(axis=1))
    H = np.concatenate(H)[: span.stop - span.start]
    A = np.concatenate(A)[: span.stop - span.start]
    return H, A

N_STORE, N_TEST = 40000, 1500
H_store, A_store = states_for(range(0, N_STORE))
H_test,  A_test  = states_for(range(N_STORE + 500, N_STORE + 500 + N_TEST))
print(f"datastore {len(H_store)}, test {len(H_test)}")

CARRIERS = np.array([496, 430, 36, 314, 374])
def zero_car(X):
    Y = X.copy(); Y[:, CARRIERS] = 0; return Y

def knn_agree(Hs, As, Hq, Aq):
    # exact 1-NN by euclidean, chunked
    agree = 0
    Hs_n2 = (Hs ** 2).sum(1)
    for i in range(0, len(Hq), 256):
        q = Hq[i:i+256]
        d = Hs_n2[None, :] - 2 * (q @ Hs.T)        # + ||q||^2 constant per row
        nn = d.argmin(axis=1)
        agree += int((As[nn] == Aq[i:i+256]).sum())
    return agree / len(Hq)

print(f"\n{'datastore S':>12} {'raw agree':>10} {'no-carrier':>11} {'lookup ops / head ops':>22}")
rng = np.random.default_rng(0)
for S in (1000, 5000, 10000, 20000, 40000):
    idx = rng.choice(len(H_store), S, replace=False)
    a_raw = knn_agree(H_store[idx], A_store[idx], H_test, A_test)
    a_zc  = knn_agree(zero_car(H_store[idx]), A_store[idx], zero_car(H_test), A_test)
    ratio = S / V
    print(f"{S:>12} {a_raw:>9.1%} {a_zc:>10.1%} {ratio:>21.2f}x")

# upper-bound check: if we copy the TRUE next token of the stored position
# instead of the model's argmax, does lookup approximate the corpus instead?
print(f"\nfor reference, model argmax = actual next corpus token at "
      f"{(A_test == np.array(ids[N_STORE+501:N_STORE+501+N_TEST])).mean():.1%} of test positions")
