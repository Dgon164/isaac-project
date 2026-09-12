"""WALK COURT — the reference-walk engine (walk/engine) under gate law.

The 2026-09-12 session built a store+walk prototype (store of items
with refs, depth-one pull per step, gates from data, rank survivors)
and documented four numbers. This court re-derives every one on this
machine, exit code is the verdict:

  1. rocket walk settles at 23 pulls; 9 materials persist, 7 rejected
     with a stated reason each
  2. store-size indifference: +50 unrelated items -> pulls unchanged,
     persist set identical, no noise item ever reached
  3. desk law: native items and refused items (negative relevance)
     are set aside, never in play; truth is never touched by relevance
  4. prose linker: forum post -> 114 items; copper touched by 4
     sentences; walk from copper settles at 92 pulls
  5. SABOTAGE ARM (the court can fail): wire one noise item into the
     path -> the indifference check itself must trip

Skips (77) if walk/ is not present.
"""
import io
import contextlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENG = os.path.abspath(os.path.join(HERE, "..", "walk", "engine"))
if not os.path.exists(os.path.join(ENG, "core.py")):
    print("SKIP: walk engine not present")
    sys.exit(77)
sys.path.insert(0, ENG)
from core import Item, Store, Desk, Cycle  # noqa: E402
from linker import link  # noqa: E402

FAILS = []


def check(name, ok):
    print(f"  {'v' if ok else 'x'}  {name}")
    if not ok:
        FAILS.append(name)


def rocket_store():
    """run run_rocket.py silenced; hand back its namespace."""
    ns = {"__file__": os.path.join(ENG, "run_rocket.py"),
          "__name__": "rocket"}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(open(os.path.join(ENG, "run_rocket.py"),
                  encoding="utf-8").read(), ns)
    return ns


NOISE = [("cat", "animal", ["fur", "whiskers", "tuna"]),
         ("bread", "food", ["flour", "yeast", "oven"]),
         ("tuna", "food", ["cat", "ocean"]),
         ("guitar", "instrument", ["strings", "fret"]),
         ("phoenix", "city", ["arizona", "heat"]),
         ("heat", "concept", ["fire", "summer"]),
         ("fire", "concept", ["heat", "oxygen"])] + \
        [("junk_%d" % i, "misc", ["junk_%d" % ((i + 1) % 43)])
         for i in range(43)]

# ---- 1. the rocket walk, exact numbers
ns = rocket_store()
S, CTX, cyc = ns["S"], ns["CTX"], ns["cyc"]
gate_fn, rank_fn = ns["load_vs_capacity"], ns["rank"]
PERSIST = {"steel_1018", "copper", "nickel", "tungsten", "tantalum",
           "graphite", "silicon_carbide", "zirconia", "alumina_ceramic"}
check("rocket walk settles at 23 pulls", cyc.step_no == 23)
check("9 persist, the known set", set(cyc.candidates) == PERSIST)
check("7 rejected, each with a stated reason",
      len(cyc.rejected) == 7 and
      all(why for _, why in cyc.rejected.values()))

# ---- 2. store-size indifference
n0 = len(S.items)
for n, k, r in NOISE:
    S.put(Item(n, k, refs=r))
S.set_rel(CTX, "heat", 3)  # relevance alone cannot summon an item
c2 = Cycle(S, CTX, "thrust", gates=[("load>capacity", gate_fn)],
           rank_by=rank_fn, verbose=False)
c2.run()
print(f"  store {n0} -> {len(S.items)} items; pulls "
      f"{cyc.step_no} -> {c2.step_no}")
check("+50 items: pulls unchanged", c2.step_no == cyc.step_no)
check("+50 items: persist set identical",
      set(c2.candidates) == PERSIST)
check("no noise item ever reached",
      not any(n in c2.resolved for n, _, _ in NOISE))

# ---- 3. desk law: refusal and native set aside, truth untouched
ds = Store()
ds.put(Item("fact_a", "note", truth=1))
ds.put(Item("secret", "record", truth=1, native=True))
ds.put(Item("banned", "note", truth=1))
ds.put(Item("bystander", "note", truth=0))
ds.set_rel("court", "banned", -2)
desk = Desk()
for name in ("fact_a", "secret", "banned", "bystander"):
    desk.take(ds.get(name), "court", ds)
check("plain true item is in play", "fact_a" in desk.in_play)
check("native item set aside, never in play",
      "secret" in desk.set_aside and "secret" not in desk.in_play)
check("negative relevance refuses",
      "banned" in desk.set_aside and
      desk.set_aside["banned"][1].startswith("refused"))
check("truth-0 item present but not for this",
      "bystander" in desk.set_aside)
check("relevance never touched truth",
      all(ds.get(n).truth in (1, 0) for n in
          ("fact_a", "secret", "banned", "bystander")))

# ---- 4. the prose linker and the forum walk
fs = Store()
made = link(open(os.path.join(ENG, "messy.txt"),
                 encoding="utf-8").read(), fs)
cu = fs.get("copper")
fc = Cycle(fs, "forum", "copper", gates=[], rank_by=lambda x: 0,
           verbose=False)
fc.run(max_steps=500)
print(f"  linker: {made} sentences -> {len(fs.items)} items; "
      f"copper touched by {len(cu.refs)}; walk settled at {fc.step_no}")
check("forum post links to 114 items", len(fs.items) == 114)
check("copper touched by 4 sentences (found by counting refs)",
      len(cu.refs) == 4)
check("walk from copper settles at 92 pulls", fc.step_no == 92)

# ---- 5. sabotage arm: the indifference check must be able to fail
sab = rocket_store()
S3, gate3, rank3 = sab["S"], sab["load_vs_capacity"], sab["rank"]
rt = S3.get("reaction_table")
rt.refs = tuple(rt.refs) + ("cat",)  # wire noise into the path
for n, k, r in NOISE:
    S3.put(Item(n, k, refs=r))
c3 = Cycle(S3, sab["CTX"], "thrust",
           gates=[("load>capacity", gate3)], rank_by=rank3,
           verbose=False)
c3.run()
check("SABOTAGE: wired-in noise IS reached (court can fail)",
      c3.step_no > 23 and "cat" in c3.resolved)

print(f"\nGATE: {'PASS' if not FAILS else 'FAIL (' + ','.join(FAILS) + ')'}")
sys.exit(1 if FAILS else 0)
