# S0 COMPOSITION PROBE — Arm A of the two-arm composition experiment.
#
# Question under test: can a bounded BIDIRECTIONAL SEARCH over Isaac's
# own stores (his door graph + his raw record of taught fact frames)
# compose multi-hop answers his prediction table cannot?  The measured
# gap (rebuild/logic_bridge_probe.py, Arm B): he holds "three = 3",
# "3 + 4 = 7", "seven = 7" as separate facts and answers 0/100 word-sum
# questions natively.  Arm B bridges the gap with an external logic
# engine (clingo).  Arm A — this file — tries a plain graph search with
# a small operator set instead.  The search lives OUTSIDE the engine:
# this is a probe, nothing here changes isaac.py.
#
# The search, concretely:
#   forward frontier  — states are the question with tokens progressively
#                       resolved through his "=" road (his own lookup,
#                       certified against his taught record);
#   backward frontier — every node in his graph with an "=" door,
#                       resolved the same way, giving value -> word;
#   meeting point     — one of his taught fact frames that unifies with
#                       the resolved question, position by position.
# The quiz token "plus" was never taught; the search must bridge it by
# MEANING (the "=" relation and frame structure), never by the token —
# untaught tokens become wildcards that match by position only.
#
# HONEST ACCOUNTING — the hand-authored schema (this experiment's cost)
# is exactly one question-encoding rule plus three operators:
#   E1 ENCODE : "WHAT" marks the unknown slot; a trailing "=" means the
#               unknown slot follows it (his own ask convention); a
#               never-observed token becomes a wildcard.
#   O1 RESOLVE: token t -> his own lookup([t, "="]), kept only when the
#               exact frame [t, "=", v] is in his taught record (his
#               matrix window-guesses otherwise: lookup(["3","="]) says
#               "9" — the record certification refuses it).
#   O2 JOIN   : unify the current pattern against one taught fact frame;
#               the unknown slot captures its frame token.
#   O3 MAPBACK: a captured value maps back through the backward frontier
#               (the word whose certified "=" resolution is that value).
# Everything else — which facts join, which words map back — comes from
# his own stores.  No sum, no word table, no "plus means +" is authored.
#
# Courts (protocol integrity ONLY — scores are reported, not asserted;
# this is an experiment and either result is a finding): teaching
# happened, the native control ran all 100, the search arm ran all 100
# forward + all 20 reverse, a worked trace printed, and every search
# stayed inside its declared step budget (no unbounded blowup).
import os
import random
import sys
import time
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "..", "code"))
from isaac import Isaac, tokenize                       # noqa: E402

# failed check names collect here; summary + exit code at the bottom
FAILS = []


def check(name, ok):
    if not ok:
        FAILS.append(name)


W = ["zero", "one", "two", "three", "four", "five", "six", "seven",
     "eight", "nine", "ten", "eleven", "twelve", "thirteen",
     "fourteen", "fifteen", "sixteen", "seventeen", "eighteen"]

# ── STAGE 1: TEACH — identical material to logic_bridge_probe.py ────
# digit sums 0-9 and number-word equivalences; NO word-math anywhere
t0 = time.perf_counter()
m = Isaac()
for a in range(10):
    for b in range(10):
        m.observe(tokenize(f"{a} + {b} = {a + b}"))
for d in range(19):
    m.observe(tokenize(f"{W[d]} = {d}"))
m.consolidate()
t_teach = time.perf_counter() - t0
print(f"STAGE 1 TEACH: {len(m.observed_sequences)} facts observed "
      f"(100 digit sums + 19 word equivalences)   "
      f"wall-clock {t_teach:.2f}s")
check("teaching-happened", len(m.observed_sequences) > 0)

# the 100 quiz questions — same for both arms, verbatim
QUIZ = [([W[a], "plus", W[b], "="], W[a + b])
        for a in range(10) for b in range(10)]

# ── STAGE 2: NATIVE CONTROL — his prediction table alone ────────────
t0 = time.perf_counter()
native_asked = native_right = 0
for q, want in QUIZ:
    ans, _ = m.lookup(q)
    native_asked += 1
    native_right += ans == want
t_native = time.perf_counter() - t0
print(f"STAGE 2 NATIVE CONTROL: {native_right}/{native_asked} word "
      f"problems = {native_right}% correct (expect ~0 -- 'plus' never "
      f"taught, stranger guard refuses)   wall-clock {t_native:.2f}s")
check("native-control-ran-100", native_asked == 100)


# ── THE SEARCH MECHANISM (probe-side; the engine is untouched) ──────

class _Cell:                     # wildcard / hole sentinels for patterns
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


WILD = _Cell("*")                # untaught token: matches any frame token
HOLE = _Cell("?")                # the slot the question asks for

BUDGET = 1000                    # declared cap: operator applications
BACK_BUDGET = 200                # declared cap: backward-frontier build

_resolve_cache = {}


def resolve(mind, tok, taught):
    """O1 RESOLVE — his own lookup([tok, '=']), certified against his
    taught record.  Certification matters: his matrix window-frames
    volunteer wrong continuations for bare digits (measured before
    this guard: lookup(['3','=']) -> '9'); only a proposal matching an
    exact taught frame [tok, '=', v] stands."""
    if tok in _resolve_cache:
        return _resolve_cache[tok]
    ans, _ = mind.lookup([tok, "="])
    v = ans if ans is not None and (tok, "=", ans) in taught else None
    _resolve_cache[tok] = v
    return v


def build_backward_frontier(mind, taught, budget=BACK_BUDGET):
    """The backward half of the search: from the answer side, every
    node in his graph holding an '=' door is a candidate; each resolves
    through the same O1 road.  Certified resolutions give the meeting
    map value -> {words}.  Built once — the goal shape (a word answer)
    is the same for every quiz question."""
    steps = 0
    back = {}
    cands = sorted(s for s in list(mind.net.doors)
                   if "=" in mind.net.doors.get(s, set()))
    for c in cands:
        if steps >= budget:
            break
        steps += 1
        v = resolve(mind, c, taught)
        if v is not None and v != c:
            back.setdefault(v, set()).add(c)
    return back, steps, len(cands)


def encode(mind, question):
    """E1 ENCODE — question tokens to a search pattern.  'WHAT' marks
    the unknown slot; otherwise a trailing '=' (his own ask convention,
    the same one the native control uses) gets the unknown slot
    appended after it; a token he has never observed becomes a
    wildcard (bridged by position, never by name)."""
    cells = []
    for t in question:
        if t == "WHAT":
            cells.append(HOLE)
        elif t in mind.net.doors or t in mind.net.preds:
            cells.append(("tok", t))
        else:
            cells.append(WILD)
    if not any(c is HOLE for c in cells):
        if cells and cells[-1] == ("tok", "="):
            cells.append(HOLE)
        else:
            return None                      # nothing is being asked
    if sum(1 for c in cells if c is HOLE) != 1:
        return None                          # exactly one unknown slot
    return tuple(cells)


def unify(state, frame):
    """O2 JOIN core — position-by-position match of a pattern against
    one taught fact frame.  Returns the token captured by the unknown
    slot, or None if the frame does not fit."""
    if len(state) != len(frame):
        return None
    cap = None
    for cell, ftok in zip(state, frame):
        if cell is WILD:
            continue
        if cell is HOLE:
            cap = ftok
            continue
        if cell[1] != ftok:
            return None
    return cap


def compose_search(mind, question, taught, back, budget=BUDGET):
    """The bounded bidirectional search.  Breadth-first frontier over
    resolution states of the question; at every state, a JOIN scan over
    his taught fact frames; captured values meet the backward frontier
    (MAPBACK).  Every operator application costs one step; the loop
    never exceeds the declared budget.  Returns
    (answer_word_or_None, steps_used, trace_lines)."""
    steps = 0
    start = encode(mind, question)
    if start is None:
        return None, steps, ["question refused at encoding (no single "
                             "unknown slot)"]
    frontier = deque([(start, [])])
    seen = {start}
    hits = []                                # (captured, frame, path)
    out_of_budget = False
    while frontier and not out_of_budget:
        state, path = frontier.popleft()
        # O2 JOIN — scan his raw record of taught fact frames
        for frame in mind.observed_sequences:
            if steps >= budget:
                out_of_budget = True
                break
            steps += 1
            cap = unify(state, frame)
            if cap is not None:
                hits.append((cap, tuple(frame), list(path)))
        if out_of_budget:
            break
        # O1 RESOLVE — grow the frontier: each known token tries the
        # '=' road; a certified resolution is a new state
        for i, cell in enumerate(state):
            if cell is WILD or cell is HOLE:
                continue
            if steps >= budget:
                out_of_budget = True
                break
            steps += 1
            v = resolve(mind, cell[1], taught)
            if v is None or v == cell[1]:
                continue
            nxt = state[:i] + (("tok", v),) + state[i + 1:]
            if nxt not in seen:
                seen.add(nxt)
                frontier.append(
                    (nxt, path + [f"{cell[1]} -[=]-> {v}   "
                                  f"(O1 resolve: his lookup, certified "
                                  f"by his taught record)"]))
    # O3 MAPBACK — captured values meet the backward frontier
    found = {}
    for cap, frame, path in hits:
        words = back.get(cap, set())
        if len(words) == 1:
            found.setdefault(next(iter(words)), (cap, frame, path))
    if len(found) == 1:
        w, (cap, frame, path) = next(iter(found.items()))
        trace = list(path)
        trace.append(f"join: {' '.join(frame)}   (O2: his taught fact "
                     f"frame; the question's untaught tokens matched "
                     f"by position, not by name)")
        trace.append(f"{cap} -[= backward]-> {w}   (O3 map-back "
                     f"through the backward frontier)")
        return w, steps, trace
    if not found:
        return None, steps, ["no taught frame joins the resolved "
                             "question -- refused"]
    return None, steps, [f"ambiguous ({sorted(found)}) -- refused"]


# ── STAGE 3: BACKWARD FRONTIER BUILD ────────────────────────────────
t0 = time.perf_counter()
taught = {tuple(s) for s in m.observed_sequences}
back_map, back_steps, back_cands = build_backward_frontier(m, taught)
t_back = time.perf_counter() - t0
print(f"STAGE 3 BACKWARD FRONTIER: {back_cands} graph nodes hold an "
      f"'=' door; {len(back_map)} certified value->word meetings; "
      f"{back_steps} steps (cap {BACK_BUDGET})   "
      f"wall-clock {t_back:.2f}s")
check("backward-build-budget-respected", back_steps <= BACK_BUDGET)

# ── STAGE 4: SEARCH ARM — the same 100 questions ────────────────────
t0 = time.perf_counter()
fwd_asked = fwd_right = fwd_refused = fwd_wrong = 0
fwd_max_steps = 0
example = None
for q, want in QUIZ:
    ans, steps, trace = compose_search(m, q, taught, back_map)
    fwd_asked += 1
    fwd_max_steps = max(fwd_max_steps, steps)
    if ans == want:
        fwd_right += 1
    elif ans is None:
        fwd_refused += 1
    else:
        fwd_wrong += 1
    if q[:3] == ["three", "plus", "four"]:
        example = (q, ans, steps, trace)
t_fwd = time.perf_counter() - t0
print(f"STAGE 4 SEARCH ARM: {fwd_right}/{fwd_asked} = {fwd_right}% "
      f"correct   refused: {fwd_refused}   wrong: {fwd_wrong}   "
      f"max steps/question: {fwd_max_steps} (cap {BUDGET})   "
      f"wall-clock {t_fwd:.2f}s")
check("search-arm-ran-100", fwd_asked == 100)

# the worked example — the found path, printed leg by leg
traced = False
if example is not None:
    q, ans, steps, trace = example
    print(f"\nworked example: {' '.join(q)}  ->  {ans}")
    for line in trace:
        print(f"    {line}")
    print(f"    steps used: {steps} / {BUDGET}")
    traced = True
check("trace-printed", traced)

# ── STAGE 5: REVERSE — the unknown in the middle ────────────────────
# "three plus WHAT is ten": his prediction table has no road for this
# direction at all; the search treats it as the same problem with the
# unknown slot mid-question ('is', also never taught, rides as a
# wildcard exactly like 'plus').
random.seed(20260831)
pairs = random.sample([(a, b) for a in range(10) for b in range(10)], 20)
t0 = time.perf_counter()
rev_asked = rev_right = rev_refused = rev_wrong = 0
rev_max_steps = 0
rev_example = None
for a, b in pairs:
    q = [W[a], "plus", "WHAT", "is", W[a + b]]
    ans, steps, trace = compose_search(m, q, taught, back_map)
    rev_asked += 1
    rev_max_steps = max(rev_max_steps, steps)
    if ans == W[b]:
        rev_right += 1
    elif ans is None:
        rev_refused += 1
    else:
        rev_wrong += 1
    if rev_example is None:
        rev_example = (q, ans, W[b])
t_rev = time.perf_counter() - t0
print(f"\nSTAGE 5 REVERSE: {rev_right}/{rev_asked} correct   "
      f"refused: {rev_refused}   wrong: {rev_wrong}   "
      f"max steps/question: {rev_max_steps} (cap {BUDGET})   "
      f"wall-clock {t_rev:.2f}s")
if rev_example is not None:
    q, ans, want = rev_example
    print(f"  e.g. {' '.join(q)}  ->  {ans}  (want {want})")
check("reverse-arm-ran-20", rev_asked == 20)
check("search-budget-respected",
      fwd_max_steps <= BUDGET and rev_max_steps <= BUDGET)

# ── THE BILL — what was hand-authored vs what his stores supplied ───
print("\nSCHEMA COST (hand-authored): 1 encoding rule + 3 operators")
print("    E1 encode  : 'WHAT' or trailing '=' marks the unknown "
      "slot; untaught tokens become positional wildcards")
print("    O1 resolve : token -> his lookup([t,'=']), certified "
      "against his taught record")
print("    O2 join    : unify pattern against one taught fact frame")
print("    O3 mapback : captured value -> word, via the backward "
      "frontier (every '='-doored node, resolved by O1)")
print("SUPPLIED BY HIS STORES: every fact joined, every word mapped, "
      "every resolution value")
print(f"\nTOTAL wall-clock: "
      f"{t_teach + t_native + t_back + t_fwd + t_rev:.2f}s")

# GATE — protocol integrity only; scores are findings, not gates
if FAILS:
    print(f"\nGATE: FAIL ({', '.join(FAILS)})")
else:
    print("\nGATE: PASS")
sys.exit(1 if FAILS else 0)
