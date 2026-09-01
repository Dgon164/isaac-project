"""WORKER EXAM PROBE — multiprocess answering over a frozen body.

The owner's P2 design, first rung: exams are read-only, so they
shard across real processes with provably identical results. The
July bench put this machine's knee at 8-12 workers; this probe
measures the curve on the real CLOTH exam and HARD-ASSERTS that
every parallel pick equals the serial pick (parallelism must never
change an answer — that is the admissibility line; consolidation
stays serial until the confluence machinery makes it provable).

Runs engine-external: teaches once, saves a body to temp, workers
each load it and answer their shard. No engine edits.
"""
import os
import re
import sys
import tempfile
import time
from glob import glob
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "..", "code"))
from isaac import Isaac  # noqa: E402
import cloth_run  # noqa: E402

FAILS = []
_worker_mind = None
_BODY = None


def _init(body_path):
    global _worker_mind
    _worker_mind = Isaac.load(body_path)
    _worker_mind.wave_logging = False


def _answer(job):
    ctx, options = job
    confs = [(_worker_mind.check(ctx, o)[1], o) for o in options]
    return max(confs)[1]


def build_jobs(passages):
    jobs, truths = [], []
    for p in passages:
        for b in p["items"]:
            ctx = [t for t in p["toks"][max(0, b["pos"] - cloth_run.CTX):
                                        b["pos"]] if re.match(r"\w", t)]
            if len(ctx) < 2:
                continue
            opts = [cloth_run.tokenize(o)[0] for o in b["options"]]
            jobs.append((ctx, opts))
            truths.append(b["truth"])
    return jobs, truths


def main():
    if not os.path.isdir(cloth_run.DATA):
        print("SKIP: CLOTH data not present")
        sys.exit(77)
    files = sorted(glob(os.path.join(cloth_run.DATA, "*.json")))
    passages = []
    for f in files:
        p = cloth_run.load(f)
        if p and p["items"]:
            passages.append(p)
        if len(passages) >= 120:
            break

    t0 = time.time()
    m = Isaac()
    m.wave_logging = False
    for p in passages:
        for s in cloth_run.sentences(p["toks"]):
            m.observe(s)
    m.consolidate()
    m.lookup(["the"])                      # force compile before save
    body = os.path.join(tempfile.mkdtemp(prefix="worker_probe_"),
                        "frozen.isaac")
    m.save(body)
    print(f"taught 120 passages + frozen body "
          f"({os.path.getsize(body) / 1e6:.1f}MB) in "
          f"{time.time() - t0:.0f}s")

    jobs, truths = build_jobs(passages)
    print(f"{len(jobs)} exam items")

    t0 = time.time()
    serial = [ _answer_serial(m, j) for j in jobs ]
    t_serial = time.time() - t0
    right = sum(a == t for a, t in zip(serial, truths))
    print(f"serial: {right}/{len(jobs)} in {t_serial:.1f}s "
          f"(1 process)")

    for n in (4, 8, 12):
        t0 = time.time()
        with Pool(n, initializer=_init, initargs=(body,)) as pool:
            par = pool.map(_answer, jobs, chunksize=64)
        dt = time.time() - t0
        same = par == serial
        print(f"workers={n:2d}: {dt:6.1f}s   speedup "
              f"{t_serial / max(dt, 1e-9):4.1f}x   answers identical: "
              f"{same}")
        if not same:
            FAILS.append(f"answers-diverge-at-{n}")

    print(f"\nGATE: {'PASS' if not FAILS else 'FAIL (' + ','.join(FAILS) + ')'}")
    sys.exit(1 if FAILS else 0)


def _answer_serial(m, job):
    ctx, options = job
    confs = [(m.check(ctx, o)[1], o) for o in options]
    return max(confs)[1]


if __name__ == "__main__":
    main()
