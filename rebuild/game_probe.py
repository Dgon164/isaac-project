"""THE GAME PATTERN — 3-heap Nim, solved and then compressed.

Deep Blue / Chinook shape at honest size. Game: 3 heaps, each 0..7;
players alternate removing >=1 object from ONE heap; taking the last
object WINS (normal play).

  1) SOLVE: memoized minimax labels every position win/loss for the
     player to move — an exact lookup table (checkers-solved in
     miniature). Counts and wall time printed.
  2) PERFECT PLAY: table player as P1 vs a random player, 200 games
     from random winning starts — must win all. From losing starts it
     plays on (any legal move); a move audit proves it never moves
     from a winning position into one the table calls winning for
     the opponent.
  3) LAW HUNT: the engine's operator induction (add/mul/inc/dec/dbl/
     neg/shr/sq chains) cannot express xor — receipt printed. So the
     probe searches its own small predicate space (10 candidates)
     for one that EXACTLY reproduces the solved table's losing set
     over all 512 positions. Winner must be xor==0 (Bouton's law),
     unique; a false candidate is shown failing with a
     counterexample. The law is minted into the facts layer.
  4) PAYOFF: a player using ONLY the induced predicate (no table, no
     search) must also win all 200 winnable games — the one-line law
     replaces the 512-row table. A false-law player is run on the
     same starts and drops games.

Deterministic: fixed seeds; run with PYTHONHASHSEED=0.
"""
import os
import random
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "..", "code"))
from isaac import Isaac  # noqa: E402

FAILS = []


def check(name, ok):
    print(f"  {'v' if ok else 'x'}  {name}")
    if not ok:
        FAILS.append(name)


m = Isaac(fast=True)
m.wave_logging = False
if not (hasattr(m, "induce_op") and hasattr(m, "fact_add")):
    print("SKIP: induction engine / facts layer not built")
    sys.exit(77)

T0 = time.perf_counter()

# ── stage 1: SOLVE — memoized minimax over every position ──────────
t = time.perf_counter()
MAX_HEAP = 7
POSITIONS = [(a, b, c) for a in range(MAX_HEAP + 1)
             for b in range(MAX_HEAP + 1) for c in range(MAX_HEAP + 1)]
MOVES = {}
for pos in POSITIONS:
    out = []
    for i, h in enumerate(pos):
        for take in range(1, h + 1):
            nxt = list(pos)
            nxt[i] = h - take
            out.append(tuple(nxt))
    MOVES[pos] = out

TABLE = {}          # position -> True if the player to move can win


def solved(pos):
    if pos in TABLE:
        return TABLE[pos]
    if pos == (0, 0, 0):
        TABLE[pos] = False   # no move; opponent took the last object
        return False
    r = any(not solved(n) for n in MOVES[pos])
    TABLE[pos] = r
    return r


for pos in POSITIONS:
    solved(pos)
wins = sum(1 for v in TABLE.values() if v)
losses = len(TABLE) - wins
t_solve = time.perf_counter() - t
print(f"stage 1 SOLVE: {len(TABLE)} positions labeled, "
      f"{wins} wins / {losses} losses for the mover "
      f"({t_solve:.3f}s wall)")
check("solved table complete: 512 positions", len(TABLE) == 512)
check("table counts: 448 mover-wins, 64 mover-losses",
      wins == 448 and losses == 64)
check("terminal (0,0,0) is a loss for the mover",
      TABLE[(0, 0, 0)] is False)

# ── stage 2: PERFECT PLAY — table player vs random player ──────────
t = time.perf_counter()


def table_move(rng):
    def mv(pos):
        good = [n for n in MOVES[pos] if not TABLE[n]]
        return rng.choice(good) if good else rng.choice(MOVES[pos])
    return mv


def random_move(rng):
    def mv(pos):
        return rng.choice(MOVES[pos])
    return mv


def play(start, p1, p2, audit=None, trace=None):
    pos, side = start, 1
    if trace is not None:
        trace.append(pos)
    while pos != (0, 0, 0):
        nxt = p1(pos) if side == 1 else p2(pos)
        if audit is not None and side == 1:
            audit.append((pos, nxt))
        pos = nxt
        side = 3 - side
        if trace is not None:
            trace.append(pos)
    return 3 - side          # whoever emptied the board won


WIN_STARTS_ALL = sorted(p for p in POSITIONS if TABLE[p])
LOSE_STARTS_ALL = sorted(p for p in POSITIONS
                         if not TABLE[p] and p != (0, 0, 0))
rng_pick = random.Random(11)
STARTS_200 = [rng_pick.choice(WIN_STARTS_ALL) for _ in range(200)]
STARTS_L100 = [rng_pick.choice(LOSE_STARTS_ALL) for _ in range(100)]

audit = []
p1w = 0
sample = []
p1 = table_move(random.Random(21))
p2 = random_move(random.Random(22))
for i, s in enumerate(STARTS_200):
    tr = sample if i == 0 else None
    if play(s, p1, p2, audit=audit, trace=tr) == 1:
        p1w += 1
print(f"stage 2 PERFECT PLAY: table player {p1w}/200 wins from "
      f"winning starts vs random")
print(f"  sample game: {' -> '.join(str(p) for p in sample)}")
check("table player wins 200/200 from winning starts", p1w == 200)

lose_w = 0
p1 = table_move(random.Random(31))
p2 = random_move(random.Random(32))
for s in STARTS_L100:
    if play(s, p1, p2, audit=audit) == 1:
        lose_w += 1
print(f"  from 100 LOSING starts it played on; random opponent "
      f"blundered enough to hand it {lose_w}/100 wins anyway")

legal = all(nxt in MOVES[pos] for pos, nxt in audit)
no_blunder = all(not TABLE[nxt]
                 for pos, nxt in audit if TABLE[pos])
t_play = time.perf_counter() - t
print(f"  move audit: {len(audit)} table-player moves checked "
      f"({t_play:.3f}s wall for stage 2)")
check("every table-player move was legal (incl. losing starts: "
      "plays on, any move)", legal)
check("never blunders: from a winning position it always moved the "
      "opponent into a solved-loss position", no_blunder)

# ── stage 3: LAW HUNT — induce the rule that IS the table ──────────
t = time.perf_counter()

# receipt: the engine's own induction has no xor in its vocabulary.
# Feed it (packed position -> h1^h2^h3) pairs; it must refuse.
XOR_PROBE = [(1, 2, 3), (1, 4, 5), (2, 4, 6), (3, 5, 6), (7, 7, 0),
             (1, 1, 2), (2, 3, 5), (4, 5, 7), (0, 1, 3), (6, 7, 1),
             (5, 2, 7), (3, 3, 3)]
pairs = [(a * 64 + b * 8 + c, a ^ b ^ c) for a, b, c in XOR_PROBE]
chain = m.induce_op(pairs)
print(f"stage 3 LAW HUNT: engine induce_op on 12 packed xor pairs "
      f"-> {chain} (xor is not in its operator vocabulary)")
check("engine induction refuses the xor pairs (probe-level "
      "predicate search is the road)", chain is None)

# probe-level predicate space: candidate meanings of "the mover is
# LOSING here". Exactly one may reproduce the solved table.
CANDIDATES = {
    "xor_zero":       lambda a, b, c: (a ^ b ^ c) == 0,
    "sum_even":       lambda a, b, c: (a + b + c) % 2 == 0,
    "sum_mod3_zero":  lambda a, b, c: (a + b + c) % 3 == 0,
    "sum_mod4_zero":  lambda a, b, c: (a + b + c) % 4 == 0,
    "all_equal":      lambda a, b, c: a == b == c,
    "two_heaps_equal": lambda a, b, c: a == b or b == c or a == c,
    "pair_and_empty": lambda a, b, c: sorted((a, b, c))[0] == 0
    and sorted((a, b, c))[1] == sorted((a, b, c))[2],
    "max_eq_others":  lambda a, b, c: 2 * max(a, b, c) == a + b + c,
    "all_even":       lambda a, b, c: a % 2 == b % 2 == c % 2 == 0,
    "has_empty_heap": lambda a, b, c: 0 in (a, b, c),
}
mismatch = {}
for name, fn in CANDIDATES.items():
    mismatch[name] = sum(1 for p in POSITIONS
                         if fn(*p) != (not TABLE[p]))
exact = [n for n, k in mismatch.items() if k == 0]
print("  candidate predicate -> mismatches vs solved table "
      "(512 positions):")
for name in CANDIDATES:
    print(f"    {name:16s} {mismatch[name]:3d}"
          f"{'   <- EXACT' if mismatch[name] == 0 else ''}")
check("exactly one candidate reproduces the table", len(exact) == 1)
check("the exact one is xor_zero", exact == ["xor_zero"])

# a false candidate shown failing, with its first counterexample
cx = next(p for p in POSITIONS
          if CANDIDATES["sum_even"](*p) != (not TABLE[p]))
print(f"  false candidate receipt: sum_even calls {cx} "
      f"{'losing' if CANDIDATES['sum_even'](*cx) else 'winning'}, "
      f"solved table says "
      f"{'winning' if TABLE[cx] else 'losing'} "
      f"({mismatch['sum_even']} mismatches total)")
check("false candidates all fail somewhere (>=1 mismatch each)",
      all(k >= 1 for n, k in mismatch.items() if n != "xor_zero"))

law_name = exact[0] if len(exact) == 1 else None
if law_name == "xor_zero":
    m.fact_add("game_law", [law_name], kind="rule", origin="induced",
               text="nim losing iff h1^h2^h3==0",
               sources=["minimax table"])
minted = m.facts_query(pred="game_law", origin="induced")
t_hunt = time.perf_counter() - t
print(f"  minted: {[f['text'] for f in minted]} "
      f"({t_hunt:.3f}s wall for stage 3)")
check("law lives in the facts layer (pred=game_law, origin=induced)",
      len(minted) == 1
      and minted[0]["text"] == "nim losing iff h1^h2^h3==0")

# ── stage 4: PAYOFF — the law alone replaces the table ─────────────
t = time.perf_counter()


def law_move(pred, rng):
    # uses ONLY the predicate: move so the opponent faces a position
    # the law calls losing; else any legal move. No table, no search.
    def mv(pos):
        good = [n for n in MOVES[pos] if pred(*n)]
        return rng.choice(good) if good else rng.choice(MOVES[pos])
    return mv


law_w = 0
if law_name is not None:
    pred = CANDIDATES[law_name]
    p1 = law_move(pred, random.Random(41))
    p2 = random_move(random.Random(42))
    for s in STARTS_200:
        if play(s, p1, p2) == 1:
            law_w += 1
print(f"stage 4 PAYOFF: law-only player {law_w}/200 wins on the "
      f"same winning starts (one line of law vs 512-row table)")
check("law player wins 200/200 -- the induced law replaces the "
      "search table", law_w == 200)

false_w = 0
p1 = law_move(CANDIDATES["sum_even"], random.Random(51))
p2 = random_move(random.Random(52))
for s in STARTS_200:
    if play(s, p1, p2) == 1:
        false_w += 1
t_pay = time.perf_counter() - t
print(f"  false-law control: sum_even player {false_w}/200 on the "
      f"same starts ({t_pay:.3f}s wall for stage 4)")
check("false-law player drops games (< 200/200)", false_w < 200)

print(f"\nwall clock: solve {t_solve:.3f}s | play {t_play:.3f}s | "
      f"hunt {t_hunt:.3f}s | payoff {t_pay:.3f}s | "
      f"total {time.perf_counter() - T0:.3f}s")
print(f"GATE: {'PASS' if not FAILS else 'FAIL (' + ','.join(FAILS) + ')'}")
sys.exit(1 if FAILS else 0)
