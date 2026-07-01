"""
COMPILE ISAAC -> WEIGHTS AND DIMS.

The inverse of FULL_NET_OVERVIEW: that read Venn circles OUT of a trained net.
This writes ISAAC's learned meanings INTO a net, with no training. The claim
is that his engine already IS a net in a reserved-dim basis:

  frames  -> input dimensions  (one reserved dim per pattern; localist)
  deltas  -> output dimensions (one reserved dim per world-change)
  doors   -> weights           (W[delta, frame] = signed surprise)
  surprise-> weight magnitude  (recorded, not thresholded)
  abstain -> the zero row       (no door fires -> no output -> "unknown" free)

Inference is one matrix multiply: y = W @ x. We verify the compiled net
reproduces ISAAC's symbolic belief-tracking answers exactly on a sealed test
stream — same predictions, same unknowns — because the net is the door lookup.
"""
import json, numpy as np
from pathlib import Path
from learner_v0 import (toks, find_mention, frame_of, name_inventories,
                        paired_observations, learn, load_stream,
                        track_beliefs, answer)

HERE = Path(__file__).parent
TRAIN = HERE / "production" / "train"
TEST = HERE / "production" / "test"

# 1. LEARN — get ISAAC's real doors from co-variation (his engine, untouched).
streams = [load_stream(p) for p in sorted(TRAIN.glob("stream_seed*.jsonl"))]
objs, ents, rooms = name_inventories(streams)
all_obs = []
for st in streams:
    all_obs.extend(paired_observations(st, objs, ents, rooms))
doors = learn(all_obs)

# 2. COMPILE — lay the doors into a reserved-dim, signed weight matrix.
FRAMES = sorted({d["frame"] for d in doors})              # input dims
DELTAS = sorted({d["delta"] for d in doors})              # output dims
fidx = {f: i for i, f in enumerate(FRAMES)}
didx = {d: i for i, d in enumerate(DELTAS)}
W = np.zeros((len(DELTAS), len(FRAMES)))                  # delta <- frame
for d in doors:
    W[didx[d["delta"]], fidx[d["frame"]]] = d["effective"]  # +surprise = excite
# (inhibitory doors -> negative entries; none learned here. abstain = 0.)

print("COMPILED NET")
print(f"  input dims  (frames): {len(FRAMES)}")
print(f"  output dims (deltas): {len(DELTAS)}")
print(f"  nonzero weights     : {(W != 0).sum()}  (the rest abstain at 0)")
print("\n  weight table (the net, fully legible):")
for d in DELTAS:
    for f in FRAMES:
        w = W[didx[d], fidx[f]]
        if w != 0:
            print(f"    dim{fidx[f]:>2} {str(f):<18} --[{w:+.2f}]--> dim{didx[d]} {d}")

def encode(sent):
    """Perception (the real program) -> reserved-dim input vector + binding."""
    st = toks(sent)
    om = find_mention(st, objs); em = find_mention(st, ents); rm = find_mention(st, rooms)
    spans = [m for m in (om, em, rm) if m]
    frame = frame_of(st, spans)
    x = np.zeros(len(FRAMES))
    if frame in fidx:
        x[fidx[frame]] = 1.0
    return x, (om[0] if om else None), (em[0] if em else None)

def net_forward(sent):
    """One matmul. Returns (delta, confidence, object, actor) or abstain->None."""
    x, obj, actor = encode(sent)
    y = W @ x                                             # delta activations
    if y.max() <= 0:                                      # no door fired
        return None, 0.0, obj, actor                     # abstain == unknown
    j = int(y.argmax())
    return DELTAS[j], float(y[j]), obj, actor

# 3. VERIFY — net belief-tracking vs ISAAC's symbolic engine on a sealed stream.
def net_track(stream):
    hist = {}
    for row in stream:
        for sent in row["heard"]:
            delta, conf, obj, actor = net_forward(sent)
            if delta is None or obj is None:
                continue
            hist[obj] = {"tick": row["tick"], "actor": actor,
                         "door_delta": delta, "door_effective": conf}
    return hist

seed = "9001"
stream = load_stream(TEST / f"stream_seed{seed}.jsonl")
sym_hist = track_beliefs(stream, objs, ents, rooms, doors)     # ISAAC symbolic
net_hist = net_track(stream)                                   # compiled net

queries = [l.split(". ", 1)[1] for l in
           (TEST / f"queries_seed{seed}.txt").read_text().strip().split("\n")]
agree = total = unknowns = 0
mismatches = []
for q in queries:
    sym = answer(q, sym_hist, objs)["belief"]
    qt = toks(q); om = find_mention(qt, objs)
    net = net_hist.get(om[0]) if om else None
    sym_s = (sym["actor"], sym["door_delta"]) if sym else "unknown"
    net_s = (net["actor"], net["door_delta"]) if net else "unknown"
    total += 1
    if sym_s == net_s: agree += 1
    else: mismatches.append((q, sym_s, net_s))
    if net_s == "unknown": unknowns += 1

print(f"\nVERIFY on sealed seed {seed}: {len(queries)} queries")
print(f"  net agrees with ISAAC's symbolic engine: {agree}/{total}")
print(f"  answered 'unknown' (abstain, no door fired): {unknowns}")
if mismatches:
    for q, s, n in mismatches[:5]:
        print(f"    MISMATCH {q}: symbolic={s} net={n}")
else:
    print("  -> compiled net is EXACTLY equivalent to the symbolic engine.")
