"""RACE TO IDLE (owner doctrine, 2026-09-01): burst at full speed,
finish the whole job, go quiet. The scoreboard is wall-clock to done
and cpu-seconds burned — speed and efficiency as one number.

THE WHOLE JOB: read 1,000 real exam passages, sit the 1,000-question
course exam, save the body. Classic mode vs FAST mode (the cull as a
flag: no type-former, no substitution fallback, single-pass think,
roots-only quick-compressed body).

Accuracy is reported beside speed — fast mode trades the fallback's
occasional rescue for clean refusals; the delta is measured, not
guessed.
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
import tempfile  # noqa: E402

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
print(f"THE JOB: {len(passages)} passages in, {len(exam)}-question "
      f"exam, body out\n")

tmp = tempfile.mkdtemp(prefix="race_")


def run(label, fast):
    w0, c0 = time.perf_counter(), time.process_time()
    m = Isaac(fast=fast)
    m.wave_logging = False
    stages = []

    t = time.perf_counter()
    for p in passages:
        for s in cloth_run.sentences(p["toks"]):
            m.observe(s)
    stages.append(("teach", time.perf_counter() - t))

    t = time.perf_counter()
    m.consolidate()
    stages.append(("consolidate", time.perf_counter() - t))

    t = time.perf_counter()
    m.lookup(["the"])
    stages.append(("compile", time.perf_counter() - t))

    t = time.perf_counter()
    right = 0
    for ctx, opts, truth in exam:
        confs = [(m.check(ctx, o)[1], o) for o in opts]
        right += max(confs)[1] == truth
    stages.append(("exam", time.perf_counter() - t))

    t = time.perf_counter()
    out = os.path.join(tmp, f"{label}.isaac")
    if fast:
        m.save_fast(out)
    else:
        m.save(out)
    stages.append(("save", time.perf_counter() - t))

    wall = time.perf_counter() - w0
    cpu = time.process_time() - c0
    print(f"{label:8s} " + "  ".join(f"{n} {s:6.1f}s"
                                     for n, s in stages))
    print(f"{'':8s} TOTAL {wall:6.1f}s wall, {cpu:6.1f}s cpu — "
          f"score {right}/{len(exam)} = {100 * right / len(exam):.1f}%"
          f"   body {os.path.getsize(out) / 1e6:.1f}MB\n")
    return wall, cpu, right, out


w_c, c_c, r_c, _ = run("CLASSIC", fast=False)
w_f, c_f, r_f, body_f = run("FAST", fast=True)

# resurrection court: the fast body round-trips and still answers
t = time.perf_counter()
m2 = Isaac.load_fast(body_f)
ctx, opts, truth = exam[0]
confs = [(m2.check(ctx, o)[1], o) for o in opts]
print(f"resurrection: fast body loads in {time.perf_counter()-t:.1f}s "
      f"(recompiles from roots), first answer "
      f"{'correct' if max(confs)[1] == truth else 'WRONG'}")

print(f"\nRACE TO IDLE: {w_c:.0f}s -> {w_f:.0f}s wall "
      f"({w_c / max(w_f, 1e-9):.0f}x), {c_c:.0f} -> {c_f:.0f} "
      f"cpu-seconds ({c_c / max(c_f, 1e-9):.0f}x less energy), "
      f"accuracy {100 * r_c / len(exam):.1f}% -> "
      f"{100 * r_f / len(exam):.1f}% "
      f"({r_f - r_c:+d} questions)")
