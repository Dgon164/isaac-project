# SCALE EVALUATION — generated training data, full-coverage testing.
# (Owner 2026-08-20: "these 3 or 6 question quizzes prove nothing. we
# need scale, and learning, and feed data, and logic problems.")
#
# Training set (generated, exact ground truth):
#   - addition and multiplication tables 0..19      (800 facts)
#   - greater-than comparisons 0..19                (380 facts)
#   - two-operand logic: and/or/xor/implies/not     (18 facts)
# Test set: EVERY fact is quizzed — 1,198 questions, not a sample.
# Honesty test: 200 out-of-range arithmetic questions built ONLY from
#   tokens he knows (so the unknown-word guard cannot help him) —
#   measures wrong-answer rate vs correct refusals at scale.
# Chaining test: 100 three-operand problems (never taught) — measures
#   the known missing feature (no inference) with a real number.
# Also reports: training throughput, index-rebuild (consolidate)
# time, matrix size, save/load time at this scale.
import os
import random
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "..", "code"))
from isaac import Isaac, tokenize                       # noqa: E402

# failed check names collect here; summary + exit code at the bottom
FAILS = []
random.seed(20260820)

m = Isaac()
facts = []
for a in range(20):
    for b in range(20):
        facts.append((f"{a} + {b} =", str(a + b)))
        facts.append((f"{a} * {b} =", str(a * b)))
for a in range(20):
    for b in range(20):
        if a != b:
            facts.append((f"{a} > {b} =", "true" if a > b else "false"))
for x in ["true", "false"]:
    for y in ["true", "false"]:
        xv, yv = x == "true", y == "true"
        facts.append((f"{x} and {y} =", "true" if xv and yv else "false"))
        facts.append((f"{x} or {y} =", "true" if xv or yv else "false"))
        facts.append((f"{x} xor {y} =", "true" if xv ^ yv else "false"))
        facts.append((f"{x} implies {y} =",
                      "true" if (not xv) or yv else "false"))
    facts.append((f"not {x} =", "false" if x == "true" else "true"))

print(f"TRAINING: {len(facts)} generated facts, one pass")
t0 = time.perf_counter()
for q, a in facts:
    m.observe(tokenize(f"{q} {a}"))
t_train = time.perf_counter() - t0
print(f"  {t_train:.1f}s = {len(facts) / t_train:,.0f} facts/sec")

t0 = time.perf_counter()
m.lookup(["0", "+", "0", "="])          # force the index build
t_compile = time.perf_counter() - t0
st = m.status()
print(f"  first-query index build: {t_compile:.1f}s; "
      f"matrix {st['matrix_shape']}")

print(f"\nEXAM 1 — full coverage: all {len(facts)} facts")
t0 = time.perf_counter()
right = 0
top3 = 0
per = {"add": [0, 0], "mult": [0, 0], "compare": [0, 0], "logic": [0, 0]}
for q, want in facts:
    toks = tokenize(q)
    kind = ("add" if "+" in toks else "mult" if "*" in toks
            else "compare" if ">" in toks else "logic")
    ans, _ = m.lookup(toks)
    ok = ans == want
    right += ok
    per[kind][0] += ok
    per[kind][1] += 1
    sel = m.lookup_topk(toks, k=3)
    top3 += want in sel
t_exam = time.perf_counter() - t0
print(f"  exact: {right}/{len(facts)} = {100 * right / len(facts):.1f}%   "
      f"answer-in-top-3: {top3}/{len(facts)} "
      f"= {100 * top3 / len(facts):.1f}%   "
      f"({len(facts) / t_exam:,.0f} questions/sec)")
for k, (r, t) in per.items():
    print(f"    {k:8s} {r}/{t} = {100 * r / max(t, 1):.1f}%")
if right != len(facts):
    FAILS.append("exam1-exact")
if top3 != len(facts):
    FAILS.append("exam1-top3")

print("\nEXAM 2 — honesty at scale: 200 out-of-range questions, "
      "known tokens only")
known = [str(n) for n in range(400) if str(n) in m.net.doors]
big = [n for n in known if int(n) > 25]
refused = wrong = 0
for _ in range(200):
    a, b = random.choice(big), random.choice(big)
    ans, _ = m.lookup([a, "+", b, "="])
    if ans is None:
        refused += 1
    elif ans != str(int(a) + int(b)):
        wrong += 1
print(f"  refused (honest): {refused}/200 = {refused / 2:.1f}%   "
      f"wrong answer given: {wrong}/200 = {wrong / 2:.1f}%   "
      f"accidentally right: {200 - refused - wrong}/200")
if refused != 200:
    FAILS.append("exam2-refused")
if wrong != 0:
    FAILS.append("exam2-wrong")

print("\nEXAM 3 — multi-step: 100 three-operand problems "
      "(historical control: 13/100 correct with 87 confident wrong "
      "answers before the 08-20 reducer; now routed through "
      "pair-at-a-time reduction)")
c_right = c_refused = 0
for _ in range(100):
    a, b, c = (random.randrange(10) for _ in range(3))
    ans, _ = m.lookup([str(a), "+", str(b), "+", str(c), "="])
    if ans == str(a + b + c):
        c_right += 1
    elif ans is None:
        c_refused += 1
print(f"  correct: {c_right}/100   refused: {c_refused}/100   "
      f"wrong: {100 - c_right - c_refused}/100")
print("  (every answer reduces through pairs he actually holds; "
      "general rule-learning beyond arithmetic remains open — see "
      "the logic bridge and R1 in the handoff proposal)")
if c_right != 100:
    FAILS.append("exam3-correct")
if 100 - c_right - c_refused != 0:
    FAILS.append("exam3-wrong")

print("\nSYSTEM COSTS at this scale")
t0 = time.perf_counter()
m.consolidate()
print(f"  consolidate (index/type rebuild): {time.perf_counter() - t0:.1f}s")
# unique temp dir so concurrent harness runs cannot collide
tmpdir = tempfile.mkdtemp(prefix="scale_eval_")
p = os.path.join(tmpdir, "scale_eval.isaac2")
t0 = time.perf_counter()
m.save(p)
t_s = time.perf_counter() - t0
t0 = time.perf_counter()
Isaac.load(p)
t_l = time.perf_counter() - t0
print(f"  save {t_s:.1f}s / load {t_l:.1f}s / file "
      f"{os.path.getsize(p) / 1048576:.1f}MB / "
      f"{m.status()['nodes']} nodes")

if FAILS:
    print(f"GATE: FAIL ({', '.join(FAILS)})")
else:
    print("GATE: PASS")
sys.exit(1 if FAILS else 0)
