"""PLANNING probe — the world loop: episodes -> induced operators ->
plans. The model-based planner pattern (NASA Remote Agent in
miniature): act in a world, bind what follows, induce each action's
rule from the record, then compute plans from the LEARNED rules only
and check them against the world.

The hidden world (this probe's secret; Isaac is never told): a
counter; 'press up' adds 1, 'press down' subtracts 1, 'double tap'
doubles. He acts (act_log) and reads the counter (observe). The
correlation binder pairs each act with the counter reading that
follows it (BIND_AT=3 recurrences, dominance over background). From
HIS stores only — bound_episodes for which reading follows which act,
observed_sequences for before -> after — the probe extracts numeric
pairs, induces each action's operator with induce_op (untold), and
mints action_rule facts. meta_hunt supplies level-2 inverses
(dec undoes inc, shr undoes dbl) for backward planning.

Courts: three operators induced untold and matching the world;
a plan 3 -> 12 found by breadth-first search over the induced
operators ONLY, verified in the hidden world; a reverse plan
12 -> 3 found backward through the inverse operators (lossy shr
predecessors rejected by the forward rule); an impossible goal
(3 -> -999 inside a 10-step budget) REFUSED with a receipt that the
whole budgeted space was enumerated.

Run:    PYTHONHASHSEED=0 python rebuild/planning_probe.py
        exit 0 = all courts pass, exit 1 = a court failed,
        exit 77 = engine parts missing (skip).
Demo:   --sabotage forces 'double tap' to the wrong rule after
        induction; the gate must FAIL (exit 1) — proof the courts
        can catch a wrong model (the plan dies against the world).
"""
import os
import sys
import time

SABOTAGE = "--sabotage" in sys.argv
sys.argv = [a for a in sys.argv if a != "--sabotage"]

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "..", "code"))
from isaac import Isaac, tokenize  # noqa: E402

FAILS = []
T_ALL = time.perf_counter()


def check(name, ok):
    print(f"  {'v' if ok else 'x'}  {name}")
    if not ok:
        FAILS.append(name)


# ── the hidden world ────────────────────────────────────────────────
class HiddenWorld:
    """The probe's secret machine. Isaac never reads this class —
    he only sees the token streams the probe emits from it."""
    RULES = {
        "press up": lambda v: v + 1,
        "press down": lambda v: v - 1,
        "double tap": lambda v: v * 2,
    }

    def __init__(self, value=3):
        self.value = value

    def set(self, value):
        self.value = value

    def do(self, action):
        self.value = self.RULES[action](self.value)
        return self.value


ACTIONS = sorted(HiddenWorld.RULES)      # deterministic order everywhere

# Before-values per action, one per phase. All 18 counter values in
# the episode set are distinct, so an after-value names its action
# unambiguously. Binder law: a pair binds at 3 recurrences AND >= 60%
# of that act's total instances — so the 2nd and 3rd outcome of the
# same act need 5 and 12 recurrences to reach 60% share (5/8, 12/20).
EPISODE_VALUES = {
    "press up": [5, 2, 9],       # -> 6, 3, 10
    "press down": [8, 15, 22],   # -> 7, 14, 21
    "double tap": [13, 30, 45],  # -> 26, 60, 90
}
PHASE_REPS = (3, 5, 12)


def run_episodes(m, world):
    """He acts, then reads the counter. Before-reading, act, after-
    reading, then three unique filler lines so the act's 3-observation
    window closes before the next episode's before-reading."""
    filler = 0
    n = 0
    for phase, reps in enumerate(PHASE_REPS):
        for action in ACTIONS:
            before = EPISODE_VALUES[action][phase]
            for _ in range(reps):
                world.set(before)
                m.observe(tokenize(f"counter shows {world.value}"))
                m.act_log(tokenize(action))
                world.do(action)
                m.observe(tokenize(f"counter shows {world.value}"))
                for _ in range(3):
                    filler += 1
                    m.observe(tokenize(
                        f"room hum line {filler} steady ."))
                n += 1
    return n


# ── extraction: HIS stores only ─────────────────────────────────────
def pairs_from_his_stores(m):
    """(before, after) numeric pairs per action, read ONLY from his
    stores: bound_episodes says WHICH counter reading follows WHICH
    act; adjacent counter readings in observed_sequences give
    before -> after. On the recurrence that promotes a pair, the
    fused episode line enters the log between the two readings, so
    one intervening 'then' line is allowed."""
    def reading(seq):
        if len(seq) == 3 and seq[0] == "counter" \
                and seq[1] == "shows" and str(seq[2]).isdigit():
            return int(seq[2])
        return None

    after_of = {}                        # after value -> action text
    for act, inp in m.bound_episodes:
        v = reading(list(inp))
        if v is not None:
            after_of[v] = " ".join(act)

    got = {}
    seqs = m.observed_sequences
    for i in range(len(seqs) - 1):
        a = reading(seqs[i])
        if a is None:
            continue
        j = i + 1
        if reading(seqs[j]) is None and "then" in seqs[j] \
                and j + 1 < len(seqs):
            j += 1                       # skip one fused episode line
        b = reading(seqs[j])
        if b is None:
            continue
        act = after_of.get(b)
        if act is not None:
            got.setdefault(act, set()).add((a, b))
    return {k: sorted(v) for k, v in got.items()}


# ── the planner: search over INDUCED operators only ────────────────
def plan_bfs(start, goal, moves, apply_fn, max_depth, max_nodes):
    """Breadth-first search from start to goal over the induced
    operators. The hidden world is never consulted. Returns
    (plan, receipt); plan = [(action, from, to), ...] or None.
    When no plan is found and neither cap was hit mid-layer, the
    receipt certifies EVERY state within max_depth steps was
    enumerated — the honest refusal."""
    t0 = time.perf_counter()
    parents = {start: None}
    frontier = [start]
    expanded = 0
    depth = 0
    node_cap_hit = False
    found = (start == goal)
    while frontier and not found and depth < max_depth:
        nxt = []
        for v in frontier:
            expanded += 1
            if expanded > max_nodes:
                node_cap_hit = True
                break
            for name, chain in moves:
                w = apply_fn(chain, v)
                if w is None or w in parents:
                    continue
                parents[w] = (v, name)
                nxt.append(w)
                if w == goal:
                    found = True
                    break
            if found:
                break
        if node_cap_hit:
            break
        frontier = nxt
        depth += 1
    plan = None
    if found and start != goal:
        steps = []
        v = goal
        while v != start:
            pv, name = parents[v]
            steps.append((name, pv, v))
            v = pv
        plan = list(reversed(steps))
    receipt = dict(
        expanded=expanded, states_seen=len(parents),
        depth_reached=depth, max_depth=max_depth, max_nodes=max_nodes,
        node_cap_hit=node_cap_hit,
        complete_within_budget=(not found and not node_cap_hit),
        min_value=min(parents), max_value=max(parents),
        wall_s=round(time.perf_counter() - t0, 4))
    return plan, receipt


def plan_backward(start, goal, inv_moves, apply_fn, max_depth,
                  max_nodes):
    """Backward search FROM the goal state using the level-2 inverse
    operators. A predecessor p = inverse(s) counts only when the
    FORWARD induced rule maps p back to s — a lossy inverse (shr on
    an odd value) fabricates predecessors and the forward check
    rejects them. Plan reads start -> goal in forward actions."""
    t0 = time.perf_counter()
    parents = {goal: None}       # state -> (goal-side successor, action)
    frontier = [goal]
    expanded = 0
    rejected = 0
    depth = 0
    node_cap_hit = False
    found = (start == goal)
    while frontier and not found and depth < max_depth:
        nxt = []
        for s in frontier:
            expanded += 1
            if expanded > max_nodes:
                node_cap_hit = True
                break
            for name, inv_chain, fwd_chain in inv_moves:
                p = apply_fn(inv_chain, s)
                if p is None or p in parents:
                    continue
                if apply_fn(fwd_chain, p) != s:
                    rejected += 1        # lossy inverse caught
                    continue
                parents[p] = (s, name)
                nxt.append(p)
                if p == start:
                    found = True
                    break
            if found:
                break
        if node_cap_hit:
            break
        frontier = nxt
        depth += 1
    plan = None
    if found and start != goal:
        steps = []
        v = start
        while v != goal:
            s, name = parents[v]
            steps.append((name, v, s))
            v = s
        plan = steps
    receipt = dict(
        expanded=expanded, states_seen=len(parents),
        depth_reached=depth, lossy_rejected=rejected,
        node_cap_hit=node_cap_hit,
        wall_s=round(time.perf_counter() - t0, 4))
    return plan, receipt


def show_plan(plan):
    for i, (name, a, b) in enumerate(plan, 1):
        print(f"    step {i}: {name:11s} {a} -> {b}")


def run_plan_induced(plan, start, chains, m):
    v = start
    for name, _, _ in plan:
        v = m._ind_apply(chains[name], v)
        if v is None:
            return None
    return v


def run_plan_world(plan, start, world):
    world.set(start)
    for name, _, _ in plan:
        world.do(name)
    return world.value


# ═══ the run ════════════════════════════════════════════════════════
print("PLANNING PROBE — episodes -> induced operators -> plans")
print(f"  PYTHONHASHSEED={os.environ.get('PYTHONHASHSEED', '(unset)')}"
      f"{'   SABOTAGE MODE (gate must FAIL)' if SABOTAGE else ''}")

m = Isaac(fast=True)
m.wave_logging = False
if not (hasattr(m, "act_log") and hasattr(m, "induce_op")
        and hasattr(m, "meta_hunt")):
    print("SKIP: binder / induction / level-2 engine not built")
    sys.exit(77)

# STAGE 1 — episodes against the hidden world
t0 = time.perf_counter()
world = HiddenWorld(3)
n_episodes = run_episodes(m, world)
t_episodes = time.perf_counter() - t0
print(f"\nSTAGE 1 — episodes: {n_episodes} run "
      f"({sum(PHASE_REPS)} per action), "
      f"{len(m.observed_sequences)} sequences in his log, "
      f"{len(m.bound_episodes)} pairs bound   [{t_episodes:.2f}s]")
for act, inp in m.bound_episodes:
    print(f"    bound: {' '.join(act):11s} -> {' '.join(inp)}")

expected_binds = set()
for action in ACTIONS:
    for before in EPISODE_VALUES[action]:
        after = HiddenWorld.RULES[action](before)
        expected_binds.add((tuple(tokenize(action)),
                            tuple(tokenize(f"counter shows {after}"))))
check("binder promoted exactly the 9 planted act->reading pairs",
      set((tuple(a), tuple(b)) for a, b in m.bound_episodes)
      == expected_binds)
check("9 binds-facts minted with origin=bound",
      len(m.facts_query(pred="binds", origin="bound")) == 9)

# STAGE 2 — (before, after) pairs from HIS stores only
t0 = time.perf_counter()
extracted = pairs_from_his_stores(m)
t_extract = time.perf_counter() - t0
print(f"\nSTAGE 2 — pairs from his stores   [{t_extract:.2f}s]")
planted = {a: sorted((v, HiddenWorld.RULES[a](v))
                     for v in EPISODE_VALUES[a]) for a in ACTIONS}
for action in ACTIONS:
    print(f"    {action:11s} {extracted.get(action, [])}")
    check(f"{action} (before,after) pairs recovered from his stores",
          extracted.get(action) == planted[action])

# STAGE 3 — operator induction, untold
t0 = time.perf_counter()
pre_rules = len(m.facts_query(pred="action_rule"))
chains = {}
for action in ACTIONS:
    pairs = extracted.get(action, [])
    chains[action] = m.induce_op(pairs) if len(pairs) >= 3 else None
t_induce = time.perf_counter() - t0

if SABOTAGE:
    print("\n  SABOTAGE: 'double tap' chain forced to ['inc'] after "
          "induction — the courts below must catch it")
    chains["double tap"] = ["inc"]

for action in ACTIONS:
    if chains[action]:
        m.fact_add("action_rule", [action] + chains[action],
                   kind="rule", origin="induced",
                   text=f"{action} : {' then '.join(chains[action])}",
                   sources=[f"{a}->{b}"
                            for a, b in extracted.get(action, [])])
print(f"\nSTAGE 3 — induction (untold)   [{t_induce:.2f}s]")
for action in ACTIONS:
    ch = chains[action]
    print(f"    {action:11s} : "
          f"{' then '.join(ch) if ch else 'REFUSED'}")
    check(f"{action} operator induced and matches the hidden world "
          f"on 0..40",
          ch is not None and all(m._ind_apply(ch, x)
                                 == HiddenWorld.RULES[action](x)
                                 for x in range(41)))
check("no action_rule facts existed before induction",
      pre_rules == 0)
check("3 action_rule facts minted with origin=induced",
      len(m.facts_query(pred="action_rule", origin="induced")) == 3)

# STAGE 4 — level 2: inverses from meta_hunt
t0 = time.perf_counter()
m.meta_hunt()
inv_name = {}
for f in m.facts_query(pred="op_inverse", origin="induced"):
    inv_name.setdefault(f["args"][1], f["args"][0])   # a undoes b
t_meta = time.perf_counter() - t0
print(f"\nSTAGE 4 — level-2 inverses   [{t_meta:.2f}s]")
for b, a in sorted(inv_name.items()):
    print(f"    {a} undoes {b}")
check("meta_hunt minted the needed inverses "
      "(dec undoes inc, inc undoes dec, shr undoes dbl)",
      inv_name.get("inc") == "dec" and inv_name.get("dec") == "inc"
      and inv_name.get("dbl") == "shr")


def invert(chain):
    out = []
    for name in reversed(chain or []):
        if name not in inv_name:
            return None
        out.append(inv_name[name])
    return out or None


# STAGE 5 — plans from the induced rules only
moves = [(a, chains[a]) for a in ACTIONS if chains[a]]
apply_fn = m._ind_apply

print("\nSTAGE 5 — planning over the INDUCED operators only")

# goal A: forward, 3 -> 12
plan_a, rec_a = plan_bfs(3, 12, moves, apply_fn,
                         max_depth=8, max_nodes=5000)
print(f"  goal A: counter 3 -> 12   [{rec_a['wall_s']}s, "
      f"{rec_a['expanded']} states expanded, "
      f"depth {rec_a['depth_reached']}]")
if plan_a:
    show_plan(plan_a)
check("plan 3 -> 12 found within budget", plan_a is not None)
check("plan 3 -> 12 is the 2-step shortest (double tap, double tap)",
      plan_a is not None and len(plan_a) == 2)
check("plan 3 -> 12 verified by simulating the induced rules",
      plan_a is not None
      and run_plan_induced(plan_a, 3, chains, m) == 12)
check("plan 3 -> 12 verified against the hidden world",
      plan_a is not None and run_plan_world(plan_a, 3, world) == 12)

# goal B: reverse, 12 -> 3, backward through the inverses
inv_moves = [(a, invert(chains[a]), chains[a])
             for a in ACTIONS if chains[a] and invert(chains[a])]
print(f"  goal B: counter 12 -> 3, backward via inverses "
      f"({', '.join(a + '<-' + ''.join(ic) for a, ic, _ in inv_moves)})")
plan_b, rec_b = plan_backward(12, 3, inv_moves, apply_fn,
                              max_depth=12, max_nodes=10000)
print(f"    [{rec_b['wall_s']}s, {rec_b['expanded']} states expanded, "
      f"{rec_b['lossy_rejected']} lossy predecessors rejected]")
if plan_b:
    show_plan(plan_b)
check("reverse plan 12 -> 3 found through the inverse operators",
      plan_b is not None)
check("reverse plan is the 9-step shortest (press down x9)",
      plan_b is not None and len(plan_b) == 9
      and all(name == "press down" for name, _, _ in plan_b))
check("backward search validated lossy inverses against the forward "
      "rule (>= 1 rejection)", rec_b["lossy_rejected"] >= 1)
check("reverse plan verified by simulating the induced rules",
      plan_b is not None
      and run_plan_induced(plan_b, 12, chains, m) == 3)
check("reverse plan verified against the hidden world",
      plan_b is not None and run_plan_world(plan_b, 12, world) == 3)

# goal C: impossible within budget — must be REFUSED with a receipt
plan_c, rec_c = plan_bfs(3, -999, moves, apply_fn,
                         max_depth=10, max_nodes=200000)
print(f"  goal C: counter 3 -> -999, budget depth<=10")
if plan_c is None:
    print(f"    REFUSED: enumerated all {rec_c['states_seen']} states "
          f"reachable in <= {rec_c['max_depth']} steps "
          f"({rec_c['expanded']} expanded, node cap "
          f"{'hit' if rec_c['node_cap_hit'] else 'untouched'}); "
          f"most negative value reached {rec_c['min_value']}; "
          f"goal absent   [{rec_c['wall_s']}s]")
check("impossible goal REFUSED (no plan invented)", plan_c is None)
check("refusal receipt certifies the whole <=10-step space was "
      "enumerated (no cap hit)",
      rec_c["complete_within_budget"] and not rec_c["node_cap_hit"])
check("goal -999 is provably beyond everything reached in budget",
      rec_c["min_value"] > -999)

t_total = time.perf_counter() - T_ALL
print(f"\nwall clock: episodes {t_episodes:.2f}s | extract "
      f"{t_extract:.2f}s | induce {t_induce:.2f}s | meta {t_meta:.2f}s"
      f" | plans {rec_a['wall_s'] + rec_b['wall_s'] + rec_c['wall_s']:.2f}s"
      f" | total {t_total:.2f}s")
print(f"\nGATE: {'PASS' if not FAILS else 'FAIL (' + ','.join(FAILS) + ')'}")
sys.exit(1 if FAILS else 0)
