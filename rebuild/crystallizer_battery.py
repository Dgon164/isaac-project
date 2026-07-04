"""
CRYSTALLIZER BATTERY — planted ground truth for type formation, specified
by the owner (2026-07-03):

  "penguin is not fly. penguin is swim. with a NOT structure, it should
   not be collapsed — it's not just unknown or possible confusion, it's a
   positively negative result."
  "things should merge if they function or are subgroups, but if they do
   not have overlaps they should not merge. abc and abd are not the same
   thing, but they can both belong to the ab group."

  C1  clean planted categories        -> recovered pure (the regime where
                                         the crystallizer has always worked)
  C2a the abc/abd law                 -> abc and abd SURVIVE as distinct
                                         types AND both belong to an ab
                                         parent (factor, don't collapse)
  C2b the penguin law                 -> a positive negative (not_fly)
                                         VETOES absorption into the
                                         fly-birds type; penguin still
                                         belongs to the shared birds group
  C3  chance co-occurrence            -> junk-type count, measured
                                         (the missing null, documented)
  C5  scale curve                     -> consolidate() seconds at n = 50/
                                         200/800 nodes, measured
"""
import sys
import time

import numpy as np

import os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from isaac import Isaac

rng = np.random.default_rng(47)


def line(c="-", n=66):
    print(c * n)


def profile(isaac, item, props):
    for p in props:
        isaac.observe([item, p])


def types_of(isaac, member):
    return [t for t, c in isaac.types.items() if member in c["members"]]


# ═══════════════════════ C1: the working regime ════════════════════════
line("=")
print("C1 — clean planted categories (the regime it has always handled)")
line("=")
isaac = Isaac()
GROUPS = {"anim": ["dog", "cat", "bird", "fox"],
          "tool": ["saw", "axe", "drill", "file"],
          "food": ["pear", "plum", "corn", "bean"]}
PROPS = {"anim": ["alive", "moves", "eats"],
         "tool": ["metal", "cuts", "held"],
         "food": ["edible", "grows", "tasty"]}
for g, items in GROUPS.items():
    for it in items:
        profile(isaac, it, PROPS[g])
isaac.consolidate()
pure = 0
for g, items in GROUPS.items():
    ts = set(types_of(isaac, items[0]))
    ok = ts and all(set(types_of(isaac, it)) & ts for it in items) and not any(
        set(types_of(isaac, other)) & ts
        for og, oi in GROUPS.items() if og != g for other in oi)
    pure += ok
cat_sound = all(
    any(isaac.types[t]["verdict"] == "sound" for t in types_of(isaac, items[0]))
    for items in GROUPS.values())
print(f"  pure categories recovered: {pure}/3   "
      f"all classified SOUND vs their chance-null: "
      f"{'YES' if cat_sound else 'NO'}")
c1 = pure == 3 and cat_sound

# ═══════════════════════ C2a: abc and abd, under ab ═════════════════════
line("=")
print("C2a — abc/abd: distinct things, one shared parent")
line("=")
isaac = Isaac()
ABC = [f"x{i}" for i in range(4)]
ABD = [f"y{i}" for i in range(4)]
for it in ABC:
    profile(isaac, it, ["a", "b", "c"])
for it in ABD:
    profile(isaac, it, ["a", "b", "d"])
isaac.consolidate()
abc_t = [t for t, c in isaac.types.items()
         if set(ABC) <= c["members"] and not (set(ABD) & c["members"])
         and "c" in c["succs"]]
abd_t = [t for t, c in isaac.types.items()
         if set(ABD) <= c["members"] and not (set(ABC) & c["members"])
         and "d" in c["succs"]]
ab_t = [t for t, c in isaac.types.items()
        if set(ABC) | set(ABD) <= c["members"]
        and {"a", "b"} <= c["succs"] and "c" not in c["succs"]
        and "d" not in c["succs"]]
sub_ok = False
if abc_t and ab_t:
    sub_ok = (isaac.types[abc_t[0]]["parent"] == ab_t[0]
              and abd_t and isaac.types[abd_t[0]]["parent"] == ab_t[0])
print(f"  abc survives as its own type: {'YES' if abc_t else 'NO (collapsed)'}")
print(f"  abd survives as its own type: {'YES' if abd_t else 'NO (collapsed)'}")
print(f"  shared ab parent exists:      {'YES' if ab_t else 'NO'}")
print(f"  both linked under ab:         {'YES' if sub_ok else 'NO'}")
c2a = bool(abc_t and abd_t and ab_t and sub_ok)

# ═══════════════════════ C2b: the penguin law ═══════════════════════════
line("=")
print("C2b — the positive negative: penguin not_fly must veto the collapse")
line("=")
isaac = Isaac()
FLIERS = ["robin", "hawk", "dove", "wren"]
for it in FLIERS:
    profile(isaac, it, ["wings", "beak", "fly"])
profile(isaac, "penguin", ["wings", "beak", "swim"])
isaac.teach_not("penguin", "fly")
isaac.consolidate()
fly_types = [t for t, c in isaac.types.items() if "fly" in c["succs"]]
fly_ok = any(set(FLIERS) <= isaac.types[t]["members"]
             and "penguin" not in isaac.types[t]["members"]
             for t in fly_types)
together = any("penguin" in c["members"] and "robin" in c["members"]
               for c in isaac.types.values())
leak = any("penguin" in isaac.types[t]["members"] for t in fly_types)
print(f"  fly-type exists with the 4 fliers, penguin excluded: "
      f"{'YES' if fly_ok else 'NO (collapsed / fly erased)'}")
print(f"  penguin still shares the birds group with robin:     "
      f"{'YES' if together else 'NO'}")
print(f"  penguin inside any fly-type (must be NO):            "
      f"{'NO' if not leak else 'YES — VIOLATION'}")
c2b = fly_ok and together and not leak

# ═══════════ C2c: the SELF-ASSEMBLED negative (never taught) ════════════
line("=")
print("C2c — the bitter-lesson negative: penguin earns not_fly by being")
print("      WATCHED (nothing taught); a barely-seen chick earns NOTHING")
line("=")
isaac = Isaac()
for _ in range(6):                                # repeated experience
    for it in FLIERS:
        profile(isaac, it, ["wings", "beak", "fly"])
    profile(isaac, "penguin", ["wings", "beak", "swim"])
profile(isaac, "chick", ["wings", "beak"])        # seen only twice:
profile(isaac, "chick", ["wings", "beak"])        # insufficient evidence
isaac.consolidate()
minted = "fly" in isaac.fact_index.get(("penguin", "cannot"), [])
chick_clear = "fly" not in isaac.fact_index.get(("chick", "cannot"), [])
fly_types = [t for t, c in isaac.types.items() if "fly" in c["succs"]]
fly_ok2 = any(set(FLIERS) <= isaac.types[t]["members"]
              and "penguin" not in isaac.types[t]["members"]
              for t in fly_types)
together2 = any("penguin" in c["members"] and "robin" in c["members"]
                for c in isaac.types.values())
print(f"  penguin's not_fly MINTED from experience (never taught): "
      f"{'YES' if minted else 'NO'}")
print(f"  chick (2 sightings) got NO negative — ABSENT stays silent: "
      f"{'YES' if chick_clear else 'NO — over-eager'}")
print(f"  fly-type keeps fly, penguin excluded, shared group kept:  "
      f"{'YES' if (fly_ok2 and together2) else 'NO'}")
c2c = minted and chick_clear and fly_ok2 and together2

# ═══ C3: chance co-occurrence -> WRONG IS KEPT AND CLASSIFIED, WITH WHY ═══
# The owner's law: junk is not prevented and not deleted — it is a
# different classification. "knowing what is right is intelligence.
# knowing what is wrong is wisdom."
line("=")
print("C3 — chance co-occurrence: junk forms, and is FILED AS WRONG")
line("=")
isaac = Isaac()
toks = [f"t{i}" for i in range(24)]
for _ in range(200):
    i, j = rng.integers(0, 24, 2)
    if i != j:
        isaac.observe([toks[i], toks[j]])
isaac.consolidate()
total = len(isaac.types)
wrong = len(isaac.wrong_types)
print(f"  types formed from pure chance: {total}")
print(f"  classified WRONG (chance-level coherence): {wrong} "
      f"({100*wrong/max(total,1):.0f}%)")
if isaac.wrong_types:
    name, c = next(iter(isaac.wrong_types.items()))
    print(f"  a wrong entry, with its why: {name}")
    print(f"    -> {c['why_wrong']}")
c3 = total > 0 and wrong / total >= 0.8
print(f"  wrong section populated, reasons attached: "
      f"{'YES' if c3 else 'NO — too much chance passed as sound'}")

# ═══════════════ C6: supersession — the loser is kept, with why ═════════
line("=")
print("C6 — supersession: 'if there is a and b, and b works better, use b'")
print("     — and a stays on the record, wearing its defeat")
line("=")
isaac = Isaac()
n = 1200
X = rng.normal(0, 1, (n, 2))
X[:, 0] = rng.uniform(-1.2, 1.2, n)
y = 5.0 * np.cos(0.5 * X[:, 0]) + rng.normal(0, 0.02, n)
isaac.discover(X, y, name="pend")                 # narrow view: parabola wins
X2 = np.column_stack([rng.uniform(-4.5, 4.5, 600), rng.normal(0, 1, 600)])
y2 = 5.0 * np.cos(0.5 * X2[:, 0]) + rng.normal(0, 0.02, 600)
res = isaac.confirm("pend", X2, y2)               # wide view: cosine overturns
m = isaac.net.get_meta("law:pend", "model")
sup = m.get("superseded", [])
now_eq = isaac.net.get_meta("law:pend", "equation")
ok_over = res and res["status"].startswith("OVERTURNED") and "cos" in now_eq
ok_kept = bool(sup) and "x0*x0" in sup[0]["equation"] \
    and "overturned by rival" in sup[0]["why"]
print(f"  B in use (cosine law active):            "
      f"{'YES' if ok_over else 'NO'}")
print(f"  A kept with its why "
      f"({'found' if sup else 'MISSING'}): "
      f"{sup[0]['equation'][:40] if sup else '—'}")
if sup:
    print(f"    -> {sup[0]['why']}")
c6 = ok_over and ok_kept

# ═══════════════════════ C5: the scale curve ════════════════════════════
line("=")
print("C5 — scale curve (seconds to consolidate)")
line("=")
for n in (50, 200, 800):
    isaac = Isaac()
    pool = [f"p{i}" for i in range(30)]
    for i in range(n):
        for p in rng.choice(30, 4, replace=False):
            isaac.observe([f"e{i}", pool[p]])
    t0 = time.time()
    isaac.consolidate()
    print(f"  n={n:4d} nodes: {time.time()-t0:6.2f} s   "
          f"({len(isaac.types)} types)")

line("=")
print(f"C1 clean categories (and classified sound): {'PASS' if c1 else 'FAIL'}")
print(f"C2a abc/abd law                            : {'PASS' if c2a else 'FAIL'}")
print(f"C2b penguin (taught)                       : {'PASS' if c2b else 'FAIL'}")
print(f"C2c penguin (earned)                       : {'PASS' if c2c else 'FAIL'}")
print(f"C3  wrong is kept and classified, with why : {'PASS' if c3 else 'FAIL'}")
print(f"C6  supersession keeps the loser + why     : {'PASS' if c6 else 'FAIL'}")
print("C5  scale knee: measurement above (untouched — no optimizing before limits)")
all_ok = c1 and c2a and c2b and c2c and c3 and c6
print(f"VERDICT: {'WORKS to the owner spec' if all_ok else 'SPEC NOT MET (see above)'}")
line("=")
