"""E2c — THE BREAK-FINDER (owner: "pretend this is the final
product... see how and where maximal parallelization breaks
everything").

Sweeps concurrent LLM clients W = 1,2,4,8,16,32 against an ollama
server running 8 parallel slots, while the CPU is separately loaded
(Isaac gauntlet arm + the 12-process worker pool run alongside).
Per level: throughput, p50/p95 latency, errors. Plus the check that
matters most for a "final product": DETERMINISM UNDER LOAD — the
same 24 questions, temp 0, at W=1 vs W=16; batched GPU attention is
allowed to change its arithmetic, and if answers drift, parallelism
is not free.

Everything prints plain; breaks are labeled BREAK when found.
"""
import json
import os
import re
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "..", "code"))
_argv = list(sys.argv)
sys.argv = [_argv[0]]
import cloth_run  # noqa: E402
from glob import glob  # noqa: E402

MODEL = "qwen2.5:1.5b-instruct"

files = sorted(glob(os.path.join(cloth_run.DATA, "*.json")))
passages = []
for f in files:
    p = cloth_run.load(f)
    if p and p["items"]:
        passages.append(p)
    if len(passages) >= 200:
        break
qs = []
for i, p in enumerate(passages):
    for b in p["items"]:
        ctx = [t for t in p["toks"][max(0, b["pos"] - cloth_run.CTX):
                                    b["pos"]] if re.match(r"\w", t)]
        if len(ctx) >= 2:
            qs.append((" ".join(p["toks"]), " ".join(ctx),
                       " / ".join(b["options"])))
            break


def call(q, timeout=180):
    passage, ctx, opts = q
    body = json.dumps(dict(
        model=MODEL, stream=False,
        messages=[dict(role="system", content="Answer with just the "
                       "missing word."),
                  dict(role="user", content=f"{passage}\n\nThe text "
                       f"went \"... {ctx} ___\". Options: {opts}. "
                       f"Reply with just the word.")],
        options=dict(temperature=0, num_predict=16))).encode()
    t0 = time.perf_counter()
    try:
        req = urllib.request.Request(
            "http://localhost:11434/api/chat", body,
            {"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            j = json.loads(r.read())
        return (j["message"]["content"].strip(),
                time.perf_counter() - t0, None)
    except Exception as e:
        return (None, time.perf_counter() - t0,
                type(e).__name__ + ": " + str(e)[:60])


def gpu():
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,utilization.gpu",
             "--format=csv,noheader"], capture_output=True, text=True,
            timeout=10).stdout.strip()
        return out
    except Exception:
        return "?"


# wait for the server
for _ in range(60):
    try:
        urllib.request.urlopen("http://localhost:11434/api/tags",
                               timeout=5)
        break
    except Exception:
        time.sleep(2)
print(f"server up; {len(qs)} distinct questions in the pool; "
      f"gpu at start: {gpu()}", flush=True)
call(qs[0])                                     # load the model
print(f"model loaded: {gpu()}\n", flush=True)

BREAKS = []
print(f"{'W':>3} {'calls':>6} {'ok':>4} {'err':>4} {'wall':>7} "
      f"{'q/s':>6} {'p50':>6} {'p95':>6}  gpu")
det = {}
for W in (1, 2, 4, 8, 16, 32):
    batch = [qs[(W * 37 + k) % len(qs)] for k in range(64)]
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=W) as pool:
        results = list(pool.map(call, batch))
    wall = time.perf_counter() - t0
    lats = sorted(r[1] for r in results)
    errs = [r[2] for r in results if r[2]]
    ok = len(results) - len(errs)
    print(f"{W:>3} {len(batch):>6} {ok:>4} {len(errs):>4} "
          f"{wall:>6.1f}s {ok / wall:>6.1f} {lats[31]:>5.1f}s "
          f"{lats[60]:>5.1f}s  {gpu()}", flush=True)
    for e in sorted(set(errs)):
        print(f"      BREAK at W={W}: {e}  "
              f"(x{errs.count(e)})")
        BREAKS.append(f"W={W}: {e}")
    # determinism set: identical 24 questions at W=1 and W=16
    if W in (1, 16):
        dbatch = qs[:24]
        with ThreadPoolExecutor(max_workers=W) as pool:
            det[W] = [r[0] for r in pool.map(call, dbatch)]

if 1 in det and 16 in det:
    diffs = [(a, b) for a, b in zip(det[1], det[16])
             if a is not None and b is not None and a != b]
    if diffs:
        BREAKS.append(f"determinism: {len(diffs)}/24 answers CHANGED "
                      f"under parallel load")
        print(f"\nBREAK — DETERMINISM: {len(diffs)}/24 temp-0 answers "
              f"differ between W=1 and W=16:")
        for a, b in diffs[:5]:
            print(f"    W=1: {a!r:30}  W=16: {b!r}")
    else:
        print(f"\ndeterminism held: 24/24 identical answers at W=1 "
              f"vs W=16")

print(f"\nBREAK MAP: {len(BREAKS)} break(s) found"
      + ("".join(f"\n  - {b}" for b in BREAKS) if BREAKS else
         " — nothing broke at these levels"))
