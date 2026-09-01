"""OPS QUEUE PROBE — the dc database design, first working rung.

The owner's original dc vision: Isaac as a database with workers
making calls, operations queued. This probe runs that shape with
this week's parts: ONE WRITER, N READERS.

  - the body file is the database (column-sparse, ~1MB, ms to load)
  - reader workers serve asks off a FROZEN version of the body
  - the single writer owns every observation and consolidation
    (writes stay serial — the order-dependence rule; only reads
    parallelize until the confluence machinery lands)
  - a teach burst bumps the version: the body refreezes and the
    reader pool restarts on the new version

Queue semantics under court: operations execute in queue order at
version granularity — an ask AFTER a teach sees the taught fact
(the planted code-word check); every parallel answer equals the
serial reference twin, bit for bit.
"""
import os
import sys
import tempfile
import time
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "..", "code"))
from isaac import Isaac, tokenize  # noqa: E402

FAILS = []
_reader = None


def _init(body_path):
    global _reader
    _reader = Isaac.load(body_path)
    _reader.wave_logging = False


def _serve(ctx):
    ans, conf = _reader.lookup(list(ctx))
    return ans


def check(name, ok):
    print(f"  {'v' if ok else 'x'}  {name}")
    if not ok:
        FAILS.append(name)


def base_corpus():
    seqs = []
    for a in range(10):
        for b in range(10):
            seqs.append(tokenize(f"{a} + {b} = {a + b}"))
    for i in range(60):
        seqs.append(tokenize(f"item {i} belongs to bin {i % 6} ."))
    return seqs


def build_queue():
    """Mixed operation queue: ask bursts split by teach bursts."""
    ops = []
    for a in range(10):
        for b in range(6):
            ops.append(("ask", tuple(tokenize(f"{a} + {b} ="))))
    ops.append(("teach", tuple(tokenize("the code word is zebra ."))))
    ops.append(("teach", tuple(tokenize("the second word is otter ."))))
    ops.append(("ask", tuple(tokenize("the code word is"))))
    for a in range(10):
        for b in range(6, 10):
            ops.append(("ask", tuple(tokenize(f"{a} + {b} ="))))
    ops.append(("teach", tuple(tokenize("the third word is finch ."))))
    ops.append(("ask", tuple(tokenize("the third word is"))))
    return ops


def run_serial(ops):
    m = Isaac()
    m.wave_logging = False
    for s in base_corpus():
        m.observe(s)
    m.consolidate()
    out = []
    for kind, payload in ops:
        if kind == "teach":
            m.observe(list(payload))
            m.consolidate()
        else:
            out.append(m.lookup(list(payload))[0])
    return out


def run_database(ops, n_workers=8):
    tmp = tempfile.mkdtemp(prefix="ops_queue_")
    writer = Isaac()
    writer.wave_logging = False
    for s in base_corpus():
        writer.observe(s)
    writer.consolidate()
    writer.lookup(["the"])                     # compile before freeze
    version = 0
    body = os.path.join(tmp, f"v{version}.isaac")
    writer.save(body)
    pool = Pool(n_workers, initializer=_init, initargs=(body,))
    out = []
    ask_buf = []
    refreezes = 0

    def flush_asks():
        nonlocal ask_buf
        if ask_buf:
            out.extend(pool.map(_serve, ask_buf, chunksize=8))
            ask_buf = []

    t0 = time.time()
    i = 0
    while i < len(ops):
        kind, payload = ops[i]
        if kind == "ask":
            ask_buf.append(payload)
            i += 1
            continue
        # teach burst: flush reads at the old version, write serially,
        # refreeze, restart readers on the new version
        flush_asks()
        while i < len(ops) and ops[i][0] == "teach":
            writer.observe(list(ops[i][1]))
            i += 1
        writer.consolidate()
        writer.lookup(["the"])
        version += 1
        body = os.path.join(tmp, f"v{version}.isaac")
        writer.save(body)
        pool.close()
        pool.join()
        pool = Pool(n_workers, initializer=_init, initargs=(body,))
        refreezes += 1
    flush_asks()
    pool.close()
    pool.join()
    dt = time.time() - t0
    return out, dt, version, refreezes


def main():
    ops = build_queue()
    n_asks = sum(1 for k, _ in ops if k == "ask")
    print(f"queue: {len(ops)} operations ({n_asks} asks, "
          f"{len(ops) - n_asks} teaches in 2 bursts)")

    t0 = time.time()
    ref = run_serial(ops)
    t_serial = time.time() - t0
    print(f"serial twin: {t_serial:.1f}s")

    out, t_db, version, refreezes = run_database(ops, n_workers=8)
    print(f"database (1 writer + 8 readers): {t_db:.1f}s, "
          f"{version + 1} body versions, {refreezes} refreezes")

    check("every parallel answer equals the serial twin", out == ref)
    zebra = out[ref.index("zebra")] if "zebra" in ref else None
    check("write-then-read ordering: the ask AFTER the teach saw "
          "'zebra'", "zebra" in ref and zebra == "zebra")
    check("second burst visible too", "finch" in ref and
          out[ref.index("finch")] == "finch")
    check("all asks answered", len(out) == n_asks)
    print(f"\n  note: per-op wall-clock — serial {t_serial / len(ops):.3f}s"
          f"/op vs database {t_db / len(ops):.3f}s/op (pool restarts "
          f"included; restart cost amortizes over burst size)")

    print(f"\nGATE: {'PASS' if not FAILS else 'FAIL (' + ','.join(FAILS) + ')'}")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
