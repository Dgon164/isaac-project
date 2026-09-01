"""E1 — the first experiment of the new mode. UNKNOWN ANSWER.

Question: if Isaac's graph facts translate mechanically into a logic
program, does a traditional symbolic engine (clingo, already
installed) reproduce his reasoning — and what does it add that he
cannot do at all?

Everything here is openable and checkable: the taught facts are the
battery's own taxonomy (cat/mammal/penguin/ball-in-box), the export
is printed, and every answer shows side by side.
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "..", "code"))
from isaac import Isaac, tokenize  # noqa: E402

try:
    import clingo
except ImportError:
    print("SKIP: clingo not installed")
    sys.exit(77)

m = Isaac()
m.wave_logging = False
for s, o in [("cat", "mammal"), ("dog", "mammal"), ("mammal", "animal"),
             ("animal", "living_thing"), ("robin", "bird"),
             ("penguin", "bird"), ("bird", "animal"),
             ("salmon", "fish"), ("fish", "animal"), ("oak", "tree"),
             ("tree", "plant"), ("plant", "living_thing")]:
    m.teach(s, "is_a", o)
for s, o in [("bird", "fly"), ("bird", "sing"), ("fish", "swim"),
             ("cat", "purr"), ("cat", "climb"), ("dog", "bark"),
             ("penguin", "swim"), ("living_thing", "grow"),
             ("animal", "move")]:
    m.teach(s, "can", o)
for s, o in [("penguin", "fly"), ("fish", "walk")]:
    m.observe(tokenize(f"{s} cannot {o}"))
    m.fact_index[(s, "cannot")].append(o)
for i, o in [("ball", "box"), ("box", "closet"), ("closet", "room"),
             ("room", "house")]:
    m.teach(i, "in", o)
if "--no-consolidate" not in sys.argv:
    m.consolidate()
    print("(consolidated — pass --no-consolidate for the A/B arm)")
else:
    print("(NOT consolidated — the battery's own condition)")

# ── the mechanical export: fact_index -> logic facts ────────────────
t0 = time.perf_counter()
lines = []
for (subj, rel), objs in m.fact_index.items():
    pred = {"is_a": "isa", "can": "can", "cannot": "cannot",
            "in": "inside"}.get(rel)
    if pred:
        for ob in objs:
            lines.append(f"{pred}({subj},{ob}).")
RULES = """
isa_t(X,Y) :- isa(X,Y).
isa_t(X,Z) :- isa(X,Y), isa_t(Y,Z).
inside_t(X,Y) :- inside(X,Y).
inside_t(X,Z) :- inside(X,Y), inside_t(Y,Z).
% nearest-ancestor-wins capability (Isaac's own walk, as a rule):
verdict(X,A,yes) :- can(X,A).
verdict(X,A,no)  :- cannot(X,A).
verdict(X,A,V)   :- isa(X,Y), verdict(Y,A,V),
                    not can(X,A), not cannot(X,A).
"""
program = "\n".join(sorted(set(lines))) + RULES
t_export = time.perf_counter() - t0
print(f"EXPORT: {len(set(lines))} facts translated mechanically from "
      f"fact_index in {1000 * t_export:.1f}ms + 7 rules (printed in "
      f"this file)")

ctl = clingo.Control(["--warn=none"])
ctl.add("base", [], program)
t0 = time.perf_counter()
ctl.ground([("base", [])])
derived = {"isa_t": set(), "inside_t": set(), "verdict": set()}
ctl.solve(on_model=lambda mo: [
    derived[s.name].add(tuple(str(a) for a in s.arguments))
    for s in mo.symbols(atoms=True) if s.name in derived])
t_solve = time.perf_counter() - t0
print(f"SOLVE: everything derivable derived in {1000 * t_solve:.1f}ms "
      f"({sum(len(v) for v in derived.values())} conclusions)\n")


def logic_isa(x, y):
    return (x, y) in derived["isa_t"]


def logic_can(x, a):
    if (x, a, "yes") in derived["verdict"]:
        return True
    if (x, a, "no") in derived["verdict"]:
        return False
    return None


def logic_in(x, y):
    return (x, y) in derived["inside_t"]


# ── side by side: the battery's questions, both engines ─────────────
print(f"{'question':<28} {'native':>10} {'logic':>10}  agree")
agree = total = 0
for q, nat, log in [
    ("cat is_a animal", m.is_a_check("cat", "animal")[0],
     logic_isa("cat", "animal")),
    ("cat is_a living_thing", m.is_a_check("cat", "living_thing")[0],
     logic_isa("cat", "living_thing")),
    ("robin is_a animal", m.is_a_check("robin", "animal")[0],
     logic_isa("robin", "animal")),
    ("cat is_a plant", m.is_a_check("cat", "plant")[0],
     logic_isa("cat", "plant")),
    ("can robin fly", m.can_check("robin", "fly")[0],
     logic_can("robin", "fly")),
    ("can robin sing", m.can_check("robin", "sing")[0],
     logic_can("robin", "sing")),
    ("can cat climb", m.can_check("cat", "climb")[0],
     logic_can("cat", "climb")),
    ("can cat grow", m.can_check("cat", "grow")[0],
     logic_can("cat", "grow")),
    ("can penguin fly", m.can_check("penguin", "fly")[0],
     logic_can("penguin", "fly")),
    ("can penguin swim", m.can_check("penguin", "swim")[0],
     logic_can("penguin", "swim")),
    ("ball in house", m.containment_check("ball", "house")[0],
     logic_in("ball", "house")),
    ("can salmon walk (mid-chain block)",
     m.can_check("salmon", "walk")[0], logic_can("salmon", "walk")),
    ("can oak grow (plant side)", m.can_check("oak", "grow")[0],
     logic_can("oak", "grow")),
    ("can oak move (animal-only)", m.can_check("oak", "move")[0],
     logic_can("oak", "move")),
]:
    total += 1
    same = (bool(nat) == bool(log)) if nat is not None \
        and log is not None else (nat is None and log is None)
    agree += same
    print(f"{q:<28} {str(nat):>10} {str(log):>10}  "
          f"{'v' if same else 'X  <-- DISAGREEMENT'}")
print(f"\nagreement: {agree}/{total}")

# ── what the logic engine adds: questions with NO native road ───────
print("\nWHAT THE TRANSLATION ADDS (no native road exists):")
fliers = sorted(x for (x, a, v) in derived["verdict"]
                if a == "fly" and v == "yes")
print(f"  WHAT can fly?          -> {fliers}")
growers = sorted(x for (x, a, v) in derived["verdict"]
                 if a == "grow" and v == "yes")
print(f"  WHAT can grow?         -> {growers}")
in_house = sorted(x for (x, y) in derived["inside_t"] if y == "house")
print(f"  WHAT is in the house?  -> {in_house}")
anims = sorted(x for (x, y) in derived["isa_t"] if y == "animal")
print(f"  WHAT is an animal?     -> {anims}")

sys.exit(0 if agree == total else 1)
