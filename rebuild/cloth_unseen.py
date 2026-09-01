"""THE UNSEEN-PASSAGE EXAM — the generalization control the demoted
85% claim owes (HANDOFF v2 step N6; W2's companion measurement).

Protocol: teach the SAME first 120 passages cloth_run.py teaches
(identical selection and class), then exam passages he has NEVER
seen (the next 30 in the same corpus) with the identical quiz
mechanics (8-token left context from the unseen passage, his check()
over the 4 real options).

INTERPRETATION, DECLARED BEFORE THE RUN (from the judged plan):
  - score ~ the deterministic tie-policy floor (~27%, measured by
    cloth_trivial_baseline.py): the statistical layer is a text
    memory; the 85% same-passage result is retrieval only.
  - score clearly above the floor: transfer exists, quantified here
    for the first time.
Either way the number publishes. Gate checks are protocol integrity
only — the score is a finding, not a pass condition.
"""
import os
import re
import sys
import time
from glob import glob

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "..", "code"))
from isaac import Isaac  # noqa: E402
import cloth_run  # noqa: E402

FAILS = []

if not os.path.isdir(cloth_run.DATA):
    print("SKIP: CLOTH data not present")
    sys.exit(77)

files = sorted(glob(os.path.join(cloth_run.DATA, "*.json")))
passages = []
for f in files:
    p = cloth_run.load(f)
    if p and p["items"]:
        passages.append(p)
    if len(passages) >= 150:
        break
taught_set, unseen_set = passages[:120], passages[120:150]

t0 = time.time()
m = Isaac()
m.wave_logging = False
for p in taught_set:
    for s in cloth_run.sentences(p["toks"]):
        m.observe(s)
m.consolidate()
print(f"taught 120 passages in {time.time() - t0:.0f}s")

t0 = time.time()
seen_r, seen_t = cloth_run.exam(m, taught_set[:20])
print(f"control — taught passages (batch 1): {seen_r}/{seen_t} = "
      f"{100 * seen_r / max(seen_t, 1):.0f}%   [{time.time() - t0:.0f}s]")

t0 = time.time()
un_r, un_t = cloth_run.exam(m, unseen_set)
pct = 100 * un_r / max(un_t, 1)
print(f"THE UNSEEN EXAM — 30 never-taught passages: {un_r}/{un_t} = "
      f"{pct:.0f}%   (tie-policy floor ~27%, chance 25%)   "
      f"[{time.time() - t0:.0f}s]")

if pct <= 32:
    print("READING (pre-declared): at the floor — the statistical "
          "layer is a text memory; same-passage scores are retrieval.")
elif pct < 50:
    print("READING (pre-declared): above the floor — partial transfer "
          "exists (local English patterns), far below retrieval.")
else:
    print("READING (pre-declared): substantial transfer — revise the "
          "text-memory framing with this number in hand.")

if len(taught_set) != 120:
    FAILS.append("taught-120")
if len(unseen_set) != 30:
    FAILS.append("unseen-30")
if un_t < 100:
    FAILS.append("unseen-items-enough")
if set(id(p) for p in taught_set) & set(id(p) for p in unseen_set):
    FAILS.append("no-overlap")

print(f"\nGATE: {'PASS' if not FAILS else 'FAIL (' + ','.join(FAILS) + ')'}")
sys.exit(1 if FAILS else 0)
