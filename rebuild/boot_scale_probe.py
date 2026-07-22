"""
BOOT SCALE PROBE — does chunking hold, does parallelism pay, where is
the knee? Feeds synthetic corpora of growing size through the boot
pipeline and times every stage honestly. Also: delta-vs-full compile
cost, interactive per-message cost at size, and config:workers 1 vs N
on the crystallize stage (real processes, spawn overhead included).

    python boot_scale_probe.py            (from rebuild/)

Writes boot_scale_probe_results.csv next to itself.
"""
import csv
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "..", "code"))
from isaac import Isaac, tokenize  # noqa: E402

TIERS = [2000, 8000, 24000]        # total tokens per tier
VOCAB = 400
STAGE_CAP = 300.0                  # seconds — past this, honest bailout
CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "boot_scale_probe_results.csv")


def corpus(n_tokens, seed=11):
    """Zipf-ish sentences, 5-12 tokens, until n_tokens total."""
    rng = np.random.default_rng(seed)
    p = 1.0 / np.arange(1, VOCAB + 1)
    p /= p.sum()
    seqs, total = [], 0
    while total < n_tokens:
        ln = int(rng.integers(5, 13))
        seqs.append([f"w{int(i)}" for i in rng.choice(VOCAB, ln, p=p)])
        total += ln
    return seqs, total


def timed(fn, *a, **kw):
    t0 = time.perf_counter()
    out = fn(*a, **kw)
    return time.perf_counter() - t0, out


def run_tier(n_tokens):
    seqs, total = corpus(n_tokens)
    print(f"\n  tier {n_tokens}: {len(seqs)} sequences...", flush=True)
    isaac = Isaac()
    isaac.wave_logging = False
    isaac.beat()                              # seed + idle beat
    isaac.ingest(seqs, kind="scale-probe")

    stages, bail = {}, None
    job = None
    for name, op in [("pull", isaac.q_next),
                     ("segment", isaac.segment_job),
                     ("crystallize", isaac.crystallize_job),
                     ("assess", isaac.assess_job),
                     ("merge", isaac.merge_job),
                     ("commit", isaac.commit_job),
                     ("sleep", isaac.sleep_pass)]:
        args = () if name in ("pull", "sleep") else (job,)
        dt, out = timed(op, *args)
        stages[name] = dt
        print(f"    [{name}] {dt:.2f}s", flush=True)
        if name == "pull":
            job = out
        if dt > STAGE_CAP:
            bail = name
            break

    segs = len(isaac._job_segments(isaac._job_id(job)))

    # compile cost: delta (one new sequence) vs full (reset accumulator)
    isaac.observe(seqs[0])
    d_delta, _ = timed(isaac._compile)
    isaac._pair_counts = None
    d_full, _ = timed(isaac._compile)

    # interactive cost at this size: ingest one line + beat + lookup
    print("    [interactive probe]...", flush=True)
    msg_times = []
    for k in range(3):
        line = " ".join(seqs[k][:6])
        t0 = time.perf_counter()
        isaac.ingest(tokenize(line), kind="probe-msg")
        isaac.beat()
        isaac.lookup(tokenize(line)[:-1])
        msg_times.append(time.perf_counter() - t0)

    st = isaac.status()
    shape = st["matrix_shape"]
    nnz = (int((isaac._compiled["W"] != 0).sum())
           if isaac._compiled else 0)

    # monolithic baseline: direct observe + one compile, no pipeline
    mono = Isaac()
    mono.wave_logging = False
    t0 = time.perf_counter()
    for s in seqs:
        mono.observe(s)
    mono._ensure_compiled()
    mono_t = time.perf_counter() - t0

    return dict(tokens=total, sequences=len(seqs), segments=segs,
                stages=stages, bail=bail, nodes=st["nodes"],
                doors=st["doors"], shape=shape, nnz=nnz,
                delta_compile_s=d_delta, full_compile_s=d_full,
                per_msg_s=sum(msg_times) / len(msg_times),
                monolithic_s=mono_t)


def run_workers(n_tokens, nworkers):
    """Crystallize stage only, config:workers = nworkers."""
    seqs, _ = corpus(n_tokens)
    isaac = Isaac()
    isaac.wave_logging = False
    isaac.beat()
    isaac.net.set_meta("config:workers", "value", nworkers)
    isaac.ingest(seqs, kind="workers-probe")
    job = isaac.q_next()
    isaac.segment_job(job)
    dt, out = timed(isaac.crystallize_job, job)
    return dt, out.get("crystallized", 0)


if __name__ == "__main__":
    print("=" * 70)
    print("  BOOT SCALE PROBE — chunking, compile, knee, workers")
    print("=" * 70)
    rows = []
    for tier in TIERS:
        r = run_tier(tier)
        rows.append(r)
        s = r["stages"]
        road = " ".join(f"{k}={v:.2f}s" for k, v in s.items())
        print(f"\n  tier {r['tokens']} tokens "
              f"({r['sequences']} seqs -> {r['segments']} segments)")
        print(f"    {road}" + (f"  [BAILED at {r['bail']} — past "
              f"{STAGE_CAP:.0f}s cap]" if r["bail"] else ""))
        print(f"    net: {r['nodes']} nodes, {r['doors']} doors; "
              f"W {r['shape']} nnz={r['nnz']}")
        print(f"    compile: delta {r['delta_compile_s']*1000:.0f}ms vs "
              f"full {r['full_compile_s']*1000:.0f}ms  "
              f"({r['full_compile_s']/max(r['delta_compile_s'],1e-9):.0f}x)")
        print(f"    interactive: {r['per_msg_s']*1000:.0f}ms per message "
              f"(ingest+beat+lookup) | monolithic baseline "
              f"{r['monolithic_s']:.2f}s")

    print(f"\n  workers on crystallize (tier {TIERS[-1]}):")
    wrows = []
    for nw in (1, 4):
        dt, nseg = run_workers(TIERS[-1], nw)
        wrows.append((nw, dt, nseg))
        print(f"    workers={nw}: {dt:.2f}s for {nseg} segments")
    if wrows[0][1] > 0:
        print(f"    speedup: {wrows[0][1]/max(wrows[1][1],1e-9):.2f}x "
              f"(spawn overhead included — honest)")

    with open(CSV_PATH, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["tokens", "sequences", "segments"]
                   + [f"{k}_s" for k in rows[0]["stages"]]
                   + ["nodes", "doors", "nnz", "delta_compile_s",
                      "full_compile_s", "per_msg_s", "monolithic_s"])
        for r in rows:
            w.writerow([r["tokens"], r["sequences"], r["segments"]]
                       + [f"{v:.4f}" for v in r["stages"].values()]
                       + [r["nodes"], r["doors"], r["nnz"],
                          f"{r['delta_compile_s']:.4f}",
                          f"{r['full_compile_s']:.4f}",
                          f"{r['per_msg_s']:.4f}",
                          f"{r['monolithic_s']:.4f}"])
    print(f"\n  csv -> {CSV_PATH}")
