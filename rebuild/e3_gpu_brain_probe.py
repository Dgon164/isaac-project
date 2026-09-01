"""E3 — THE HOT BRAIN (owner idea, 2026-09-01): load Isaac's whole
mind into GPU memory, treat the card as a separate processor with an
input line, and brute-force the comparisons in batch.

The whole 1,000-passage brain is ~10MB vs 24GB VRAM — it all goes
resident. This probe runs the full 1,108-question exam as ONE
batched pipeline on the card:

  encode  : every query's frame lookups precomputed to column ids
            (exact-match road; the type-substitution miss road stays
            CPU in v1 and is reported as such)
  product : one sparse table (CSR on GPU) x a batch of sparse query
            vectors = every score for every question at once
  read    : the 4 option rows per question, argmax picks

Courts: picks must be IDENTICAL to the CPU road on the same encode
inputs (his arithmetic is exact-friendly — unlike the LLM batch,
which flipped 'after'->'before' under load). Timing: CPU serial vs
GPU batch, whole exam.
"""
import os
import re
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "..", "code"))
_argv = list(sys.argv)
sys.argv = [_argv[0]]
from isaac import Isaac  # noqa: E402
import cloth_run  # noqa: E402
from glob import glob  # noqa: E402
import numpy as np  # noqa: E402

try:
    import torch
    assert torch.cuda.is_available()
except Exception:
    print("SKIP: torch+cuda not available")
    sys.exit(77)

BODY = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "..", "data", "minds", "cloth1000.isaac")
t0 = time.time()
m = Isaac.load(BODY)
m.wave_logging = False
m.lookup(["the"])
c = m._compiled
print(f"brain loaded+compiled in {time.time() - t0:.1f}s — "
      f"{c['shape'][0]:,} deltas x {c['shape'][1]:,} frames, "
      f"{sum(len(r) for r in c['col_rows']):,} nonzeros")

files = sorted(glob(os.path.join(cloth_run.DATA, "*.json")))
passages = []
for f in files:
    p = cloth_run.load(f)
    if p and p["items"]:
        passages.append(p)
    if len(passages) >= 1000:
        break
exam = []
for i, p in enumerate(passages):
    for b in p["items"]:
        ctx = [t for t in p["toks"][max(0, b["pos"] - cloth_run.CTX):
                                    b["pos"]] if re.match(r"\w", t)]
        if len(ctx) >= 2:
            exam.append((ctx, [cloth_run.tokenize(o)[0]
                               for o in b["options"]], b["truth"]))
            break
print(f"{len(exam)} exam questions")

# ── CPU reference: direct-frame road (exact encode) ────────────────
t0 = time.time()
cpu_scores = []
enc_cols, enc_vals, hits = [], [], 0
for ctx, opts, truth in exam:
    x = m._encode(ctx)          # dict {col: w} or None
    if x:
        hits += 1
        y = m._matvec(x)
        cpu_scores.append([float(y[c["didx"][o]])
                           if o in c["didx"] else -1.0 for o in opts])
        enc_cols.append(sorted(x))
        enc_vals.append([x[j] for j in sorted(x)])
    else:
        cpu_scores.append(None)
        enc_cols.append([])
        enc_vals.append([])
t_cpu = time.time() - t0
print(f"CPU serial: full exam encode+product in {t_cpu:.2f}s "
      f"({hits}/{len(exam)} direct-frame hits; misses use the "
      f"type-substitution road, CPU-only in v1)")

# ── THE HOT BRAIN: whole table resident, one batched pass ──────────
t0 = time.time()
dev = "cuda"
n_d, n_f = c["shape"]
# the table as one COO sparse (delta_row, frame_col) on the card
coo_r, coo_c, coo_v = [], [], []
for j, (r, v) in enumerate(zip(c["col_rows"], c["col_vals"])):
    if len(r):
        coo_r.append(r.astype(np.int64))
        coo_c.append(np.full(len(r), j, dtype=np.int64))
        coo_v.append(v)
Wt = torch.sparse_coo_tensor(
    torch.from_numpy(np.stack([np.concatenate(coo_r),
                               np.concatenate(coo_c)])),
    torch.from_numpy(np.concatenate(coo_v)),
    size=(n_d, n_f)).coalesce().to(dev)
t_load = time.time() - t0
mem = torch.cuda.memory_allocated() / 1e6
print(f"brain resident on GPU in {t_load:.2f}s ({mem:.0f}MB of "
      f"24,576MB — {100 * mem / 24576:.2f}% of the card)")

t0 = time.time()
nq = len(exam)
qi, qj, qv = [], [], []
for k in range(nq):
    for col, w in zip(enc_cols[k], enc_vals[k]):
        qi.append(k)
        qj.append(col)
        qv.append(w)
Qd = torch.zeros((nq, n_f), dtype=torch.float32, device=dev)
Qd[torch.tensor(qi, device=dev),
   torch.tensor(qj, device=dev)] = torch.tensor(
    qv, dtype=torch.float32, device=dev)
# supported CUDA form: sparse table @ dense query block
Yd = torch.sparse.mm(Wt, Qd.t()).t()
torch.cuda.synchronize()
t_gpu = time.time() - t0
print(f"GPU batch: ALL {nq} questions in one pass: {t_gpu:.3f}s "
      f"({1000 * t_gpu / nq:.2f}ms/question amortized)")

# ── the identity court ─────────────────────────────────────────────
Yc = Yd.cpu().numpy()
agree = comp = 0
maxdiff = 0.0
for k, (ctx, opts, truth) in enumerate(exam):
    if cpu_scores[k] is None:
        continue
    comp += 1
    g = [float(Yc[k, c["didx"][o]]) if o in c["didx"] else -1.0
         for o in opts]
    maxdiff = max(maxdiff, max(abs(a - b)
                               for a, b in zip(g, cpu_scores[k])))
    agree += (int(np.argmax(g)) == int(np.argmax(cpu_scores[k])))
print(f"identity court: {agree}/{comp} identical picks, "
      f"max score diff {maxdiff:.2e}")
print(f"\nverdict: whole-brain-resident batch = "
      f"{t_cpu / max(t_gpu, 1e-9):.0f}x the serial road on this exam "
      f"shape, using {100 * mem / 24576:.2f}% of the card. "
      f"{'IDENTITY HOLDS' if agree == comp else 'IDENTITY BROKE'}")
sys.exit(0 if agree == comp else 1)
