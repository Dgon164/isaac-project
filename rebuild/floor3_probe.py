"""FLOOR 3 probe — a rule about FINDING rules: the pair-miner
generalized from his own record, untold.

The stock miner (structure_hunt) is hardwired to templates with
exactly TWO number slots. This probe:
  1. teaches prose carrying two pair laws (counter +1, price x2) and
     lets the stock miner mint them, untold;
  2. also teaches prose carrying two TRIPLE laws ("N plus M gives K"
     with K=N+M, "N times M makes K" with K=N*M) — invisible to the
     stock miner, which skips every line that is not a pair;
  3. the floor-3 move: reads the record of successful hunts (facts
     layer: pred=op_rule, origin=induced, source templates with
     number slots) and on that evidence ONLY retries the same recipe
     at three slots, searching a small table of binary operators
     (add, sub, mul, max, min, first, second). An operator answers
     only if it reproduces EVERY triple; the shuffled-output null
     must refuse; results are minted as pred=binop_rule facts;
  4. noise: a 3-slot template with random triples must be refused.
Control: a fresh mind given the same 3-slot prose but holding NO
record of a pair-mining win gets no widening — the driver is the
record, not the prose. The engine is not edited; the widened miner
lives in this file.
"""
import os
import random
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "..", "code"))
from isaac import Isaac, tokenize  # noqa: E402

FAILS = []


def check(name, ok):
    print(f"  {'v' if ok else 'x'}  {name}")
    if not ok:
        FAILS.append(name)


# ── the binary operator table (defined here, not in the engine) ────
BINOPS = {
    "add": lambda a, b: a + b,
    "sub": lambda a, b: a - b,
    "mul": lambda a, b: a * b,
    "max": lambda a, b: a if a >= b else b,
    "min": lambda a, b: a if a <= b else b,
    "first": lambda a, b: a,
    "second": lambda a, b: b,
}


def induce_binop(triples):
    """One operator must reproduce EVERY triple, or nothing answers."""
    for name, fn in BINOPS.items():
        if all(fn(a, b) == c for a, b, c in triples):
            return name
    return None


def widening_license(m):
    """Read the record: which courted rules (op_rule, origin=induced)
    came from templates whose only varying positions were number
    slots? Each win is (rule text, source template, slot count)."""
    wins = []
    for f in m.facts_query(pred="op_rule", origin="induced"):
        for src in f.get("sources", []):
            slots = src.split().count("#")
            if slots >= 2:
                wins.append((f["text"], src, slots))
    return wins


def structure_hunt_wide(m, k=3, recent=400, min_examples=4):
    """The floor-3 move: the stock miner's recipe with the slot count
    read as a parameter instead of the hardwired 2. It runs ONLY when
    the mind's own record shows the k=2 recipe winning in court —
    no recorded win, no widening."""
    wins = widening_license(m)
    out = {"minted": [], "templates": 0, "refused": 0, "license": wins}
    if not wins:
        return out
    temps = {}
    for seq in m.observed_sequences[-recent:]:
        nums = [i for i, t in enumerate(seq)
                if str(t).lstrip("-").isdigit()]
        if len(nums) != k:
            continue
        key = tuple("#" if i in nums else t
                    for i, t in enumerate(seq))
        temps.setdefault(key, []).append(
            tuple(int(seq[i]) for i in nums))
    out["templates"] = len(temps)
    for key, triples in temps.items():
        uniq = sorted(set(triples))
        if len(uniq) < min_examples:
            continue
        op = induce_binop(uniq)
        if op is None:
            out["refused"] += 1
            continue
        # THE NULL: shuffle the output column; if any operator still
        # explains every row, the fit was too easy — refuse the mint.
        rng = random.Random(1)
        outs = [t[-1] for t in uniq]
        rng.shuffle(outs)
        shuffled = [t[:-1] + (o,) for t, o in zip(uniq, outs)]
        if shuffled != uniq and induce_binop(shuffled) is not None:
            out["refused"] += 1
            continue
        name = f"binop{len(m.facts_query(pred='binop_rule')) + 1}"
        m.fact_add("binop_rule", [name, op], kind="rule",
                   origin="induced",
                   text=f"{name} = {op}(slot1, slot2) -> slot3",
                   sources=[" ".join(str(t) for t in key)])
        out["minted"].append((name, op, " ".join(key), len(uniq)))
    return out


t0 = time.perf_counter()
m = Isaac(fast=True)
m.wave_logging = False
if not (hasattr(m, "structure_hunt") and hasattr(m, "fact_add")):
    print("SKIP: induction engine not built")
    sys.exit(77)
t_boot = time.perf_counter()

# ── stage 1: teach — pair laws, triple laws, noise, filler ─────────
rng = random.Random(11)
for n in rng.sample(range(1, 30), 8):
    m.observe(tokenize(f"the counter goes from {n} to {n + 1} ."))
for n in rng.sample(range(1, 20), 8):
    m.observe(tokenize(f"the price doubles from {n} to {n * 2} ."))

pairs_add = []
while len(pairs_add) < 10:
    p = (rng.randrange(1, 40), rng.randrange(1, 40))
    if p not in pairs_add:
        pairs_add.append(p)
pairs_mul = []
while len(pairs_mul) < 10:
    p = (rng.randrange(2, 13), rng.randrange(2, 13))
    if p not in pairs_mul:
        pairs_mul.append(p)
for a, b in pairs_add:
    m.observe(tokenize(f"{a} plus {b} gives {a + b} ."))
for a, b in pairs_mul:
    m.observe(tokenize(f"{a} times {b} makes {a * b} ."))
for _ in range(10):
    m.observe(tokenize(f"gauge {rng.randrange(1, 60)} port "
                       f"{rng.randrange(1, 60)} shows "
                       f"{rng.randrange(1, 200)} ."))
for s in ["the cat sat on the mat .", "rain fell all day .",
          "a dog barked twice ."]:
    m.observe(tokenize(s))
t_teach = time.perf_counter()

# ── stage 2: the stock miner (hardwired to pairs) ──────────────────
rep = m.structure_hunt()
print(f"stock hunt: {len(rep['minted'])} minted from "
      f"{rep['templates']} pair templates, {rep['refused']} refused")
for name, chain, key, n in rep["minted"]:
    print(f"    {name}: {' then '.join(chain)}   (template: "
          f"{key[:46]}, {n} self-collected examples)")
texts = {tuple(c) for _, c, _, _ in rep["minted"]}
check("stock miner: increment law minted untold",
      ("inc",) in texts or ("add_k(1)",) in texts)
check("stock miner: doubling law minted untold",
      ("dbl",) in texts or ("mul_k(2)",) in texts)
check("stock miner blind to triple prose (pair templates only, "
      "though the triples sat in the same log)",
      len(rep["minted"]) == 2 and
      not any(w in key for _, _, key, _ in rep["minted"]
              for w in ("plus", "times", "gives", "makes")))
t_hunt = time.perf_counter()

# ── stage 3: FLOOR 3 — widen the miner from the record ─────────────
wins = widening_license(m)
print(f"\nFLOOR 3 — why widen: the record holds {len(wins)} courted "
      f"rules (pred=op_rule, origin=induced); in every one the law "
      f"rode in the template's number slots and nothing else varied:")
for text, src, slots in wins:
    print(f"    {text}   <- '{src}'  ({slots} slots)")
print("    the slot count (2) is the only hardwired constant in that "
      "recipe,\n    so the same recipe is retried at 3 slots with a "
      "table of binary operators.")
check("widening licensed by recorded wins (>=2 courted rules, all "
      "from 2-slot templates)",
      len(wins) >= 2 and all(s == 2 for _, _, s in wins))

wide = structure_hunt_wide(m)
print(f"wide hunt (k=3): {len(wide['minted'])} minted from "
      f"{wide['templates']} triple templates, "
      f"{wide['refused']} refused")
for name, op, key, n in wide["minted"]:
    print(f"    {name}: {op}(slot1, slot2) -> slot3   (template: "
          f"{key[:46]}, {n} examples)")
check("plus law minted untold as a binary operator",
      any(op == "add" and "plus" in key
          for _, op, key, _ in wide["minted"]))
check("times law minted untold as a binary operator",
      any(op == "mul" and "times" in key
          for _, op, key, _ in wide["minted"]))
check("noise template refused (no operator fits random triples)",
      wide["refused"] >= 1)
check("no false mints (exactly the two real laws)",
      len(wide["minted"]) == 2)
check("minted rules live in the facts layer "
      "(pred=binop_rule, origin=induced)",
      len(m.facts_query(pred="binop_rule", origin="induced")) == 2)

# the null demonstrated directly: mixed outputs must beat no operator
add_triples = sorted({(a, b, a + b) for a, b in pairs_add})
outs = [c for _, _, c in add_triples]
random.Random(7).shuffle(outs)
shuffled = [(a, b, o) for (a, b, _), o in zip(add_triples, outs)]
check("shuffled-output null refuses (mixed plus outputs fit no "
      "operator)",
      shuffled != add_triples and induce_binop(shuffled) is None)
t_wide = time.perf_counter()

# ── stage 4: control — same prose, empty record, no widening ───────
c = Isaac(fast=True)
c.wave_logging = False
for a, b in pairs_add:
    c.observe(tokenize(f"{a} plus {b} gives {a + b} ."))
for a, b in pairs_mul:
    c.observe(tokenize(f"{a} times {b} makes {a * b} ."))
ctrl = structure_hunt_wide(c)
print(f"\ncontrol mind: triple prose present, record empty -> "
      f"license={len(ctrl['license'])} wins, "
      f"{len(ctrl['minted'])} minted (the driver is the record, "
      f"not the prose)")
check("control: no recorded pair-mining win -> widening refused, "
      "nothing minted",
      ctrl["license"] == [] and ctrl["minted"] == [] and
      len(c.facts_query(pred="binop_rule")) == 0)
t_end = time.perf_counter()

print(f"\nstage seconds: boot {t_boot - t0:.2f} | teach "
      f"{t_teach - t_boot:.2f} | stock hunt {t_hunt - t_teach:.2f} | "
      f"floor3 {t_wide - t_hunt:.2f} | control {t_end - t_wide:.2f} "
      f"| total {t_end - t0:.2f}")
print(f"\nGATE: {'PASS' if not FAILS else 'FAIL (' + ','.join(FAILS) + ')'}")
sys.exit(1 if FAILS else 0)
