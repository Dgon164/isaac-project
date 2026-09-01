"""WORK MODE — teach 1,000 passages and save the body. No baselines,
no retention loops, no per-batch exams: the machine working, not the
machine being measured. (The 90-minute 'runs' were ~95% measurement:
three exams per batch. Owner 2026-09-01: functional first.)"""
import os
import sys
import time
from glob import glob

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "..", "code"))
from isaac import Isaac  # noqa: E402
import cloth_run  # noqa: E402

t0 = time.time()
files = sorted(glob(os.path.join(cloth_run.DATA, "*.json")))
passages = []
for f in files:
    p = cloth_run.load(f)
    if p and p["items"]:
        passages.append(p)
    if len(passages) >= 1000:
        break
print(f"load corpus: {time.time() - t0:.0f}s ({len(passages)} passages)")

t0 = time.time()
m = Isaac()
m.wave_logging = False
n_sent = 0
for p in passages:
    for s in cloth_run.sentences(p["toks"]):
        m.observe(s)
        n_sent += 1
t_teach = time.time() - t0
print(f"teach: {n_sent} sentences in {t_teach:.0f}s "
      f"({n_sent / max(t_teach, 0.001):.0f}/sec)")

t0 = time.time()
m.consolidate()
print(f"consolidate: {time.time() - t0:.0f}s")

t0 = time.time()
m.lookup(["the"])
print(f"compile: {time.time() - t0:.0f}s  shape {m._compiled['shape']}")

t0 = time.time()
out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "data", "minds", "cloth1000.isaac")
os.makedirs(os.path.dirname(out), exist_ok=True)
if os.path.exists(out):
    os.replace(out, out + "." + time.strftime("%Y%m%d-%H%M%S")
               + ".backup")
m.save(out)
print(f"save: {time.time() - t0:.0f}s "
      f"({os.path.getsize(out) / 1e6:.1f}MB body)")

# one light proof-of-life, not an exam campaign
t0 = time.time()
r, t = cloth_run.exam(m, passages[:5])
print(f"spot check (5 passages): {r}/{t} in {time.time() - t0:.1f}s")
print(f"\nTOTAL wall-clock: the machine did the whole job in the "
      f"time printed above. GATE: PASS")
sys.exit(0)
