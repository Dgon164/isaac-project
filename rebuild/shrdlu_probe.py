"""SHRDLU PROBE — bounded natural-language dialogue over his facts,
with WHY.

A small question-answering loop over a taught corpus (the
cat/penguin/containment taxonomy from test_reasoning plus three
has-properties). Template parser, no NLP libraries — the world is
bounded, so the grammar is too. Supported forms:

    is X a Y            -> is_a_check (chain walk)
    can X Z             -> can_check (negative first, then direct,
                           then inherited down the is_a chain)
    what is X           -> is_a chain + has-properties
    what can Z          -> REVERSE enumeration through the logic
                           road (mature.py convert/solve: clingo
                           verdicts with nearest-ancestor-wins)
    what is in the Y    -> transitive containment, reverse
                           enumeration through the same logic road
    why                 -> explain the PREVIOUS answer from the
                           chain / inheritance path actually used
    anything else       -> the honest help line

Unknown subjects get an honest "I do not know" AND file an ask
(m.ask_file), so ignorance leaves a work item instead of vanishing.

Found while building: the ENGINE files its own ask the first time
an is_a walk reaches the top of the taxonomy — lookup(living_thing
is_a) misses and the recall road records the question (deduped
forever after). So ask #1 belongs to him, the dialogue's asks are
#2 and #3, and the court pins all three.

Court: scripted dialogue with exact expected replies, printed as a
readable transcript. Conventions from meta_rules_court.py
(FAILS / GATE / exit 0-1, SKIP 77 when clingo is missing).
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "..", "code"))

try:
    import clingo  # noqa: F401
except ImportError:
    print("SKIP: clingo not installed — the reverse-enumeration "
          "road needs it")
    sys.exit(77)

from isaac import Isaac, tokenize  # noqa: E402
from mature import convert, solve  # noqa: E402  (the tested
#                                    fact_index -> clingo road)

FAILS = []


def check(name, ok):
    print(f"  {'v' if ok else 'x'}  {name}")
    if not ok:
        FAILS.append(name)


# ── the taught corpus (test_reasoning taxonomy + property extras) ──

t0 = time.perf_counter()
m = Isaac()
m.wave_logging = False
for s, o in [("cat", "mammal"), ("dog", "mammal"),
             ("mammal", "animal"), ("animal", "living_thing"),
             ("robin", "bird"), ("penguin", "bird"),
             ("bird", "animal"), ("salmon", "fish"),
             ("fish", "animal"), ("oak", "tree"),
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
for s, o in [("bird", "feathers"), ("mammal", "fur"),
             ("cat", "whiskers")]:
    m.teach(s, "has", o)
for i, o in [("ball", "box"), ("box", "closet"),
             ("closet", "room"), ("room", "house")]:
    m.teach(i, "in", o)
t_teach = time.perf_counter() - t0

# ── the logic road, ground+solve ONCE, reused by every reverse
#    query (mature.py: transitive closure + nearest-ancestor-wins) ──

t0 = time.perf_counter()
program, _taught, _n_math = convert(m)
derived = solve(program)
CAN_YES = {}   # ability -> set of subjects with a yes verdict
for x, a, v in derived["verdict"]:
    if v == "yes":
        CAN_YES.setdefault(a, set()).add(x)
IN_TC = {}     # container -> set of items transitively inside
for r, x, y in derived["tc"]:
    if r == "in":
        IN_TC.setdefault(y, set()).add(x)
t_logic = time.perf_counter() - t0

KNOWN = set()  # every token ever taught, as subject or object
for (s, _r), objs in m.fact_index.items():
    KNOWN.add(s)
    KNOWN.update(str(o) for o in objs)

HELP = ("I only understand: is X a Y / can X Z / what is X / "
        "what can Z / what is in the Y / why.")

LAST = {"kind": None}  # what the previous answer rested on


def article(w):
    return "an" if w[:1] in "aeiou" else "a"


def join_names(names):
    names = list(names)
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " and " + names[-1]


def isa_hops(path):
    """[cat, mammal, animal] -> 'cat is_a mammal and mammal is_a animal'"""
    return " and ".join(f"{a} is_a {b}" for a, b in zip(path, path[1:]))


def index_path(x, relation, stop=None):
    """Deterministic chain walk on the fact index (first parent)."""
    path, cur = [x], x
    while True:
        nxt = m.fact_index.get((cur, relation), [])
        if not nxt or nxt[0] in path:
            return path
        cur = nxt[0]
        path.append(cur)
        if stop is not None and cur == stop:
            return path


def justify_can(x, ability):
    """Why does x hold a yes verdict for ability? (fact-index walk)"""
    if ability in m.fact_index.get((x, "can"), []):
        return f"{x}: taught directly"
    path = index_path(x, "is_a")
    for i, anc in enumerate(path[1:], 1):
        if ability in m.fact_index.get((anc, "can"), []):
            return (f"{x}: is_a {' -> '.join(path[1:i + 1])} "
                    f"and {anc} can {ability}")
    return f"{x}: derived by the logic road"


def unknown_reply(word):
    aid = m.ask_file([word, "is_a", "?"],
                     reason="dialogue met an unknown subject",
                     road="dialogue")
    LAST.clear()
    LAST.update(kind="unknown", word=word, aid=aid)
    return f"I do not know anything about {word}. I filed ask #{aid}."


def answer(question):
    """One dialogue turn: bounded template parse -> reply string."""
    w = question.lower().replace("?", " ").split()

    if w == ["why"]:
        k = LAST.get("kind")
        if k is None:
            return "there is no previous answer to explain."
        if k == "is_a":
            x, y, chain = LAST["x"], LAST["y"], LAST["chain"]
            if LAST["found"]:
                return ("because "
                        + isa_hops(chain[:chain.index(y) + 1]) + ".")
            return (f"because the is_a chain runs "
                    f"{' -> '.join(chain)} and never reaches {y}.")
        if k == "can":
            x, z, chain = LAST["x"], LAST["z"], LAST["chain"]
            verb = "can" if LAST["res"] else "cannot"
            if LAST["res"] is None:
                return (f"because the is_a chain "
                        f"{' -> '.join(chain)} carries no can or "
                        f"cannot verdict for {z}; ask "
                        f"#{LAST['aid']} stays open.")
            if len(chain) == 1:
                return f"because {x} {verb} {z} was taught directly."
            return (f"because {isa_hops(chain)} and "
                    f"{chain[-1]} {verb} {z}.")
        if k == "what_can":
            return ("; ".join(justify_can(x, LAST["z"])
                              for x in LAST["members"]) + ".")
        if k == "in":
            return ("; ".join(
                f"{x}: {' -> '.join(index_path(x, 'in', LAST['y']))}"
                for x in LAST["items"]) + ".")
        if k == "what_is":
            return (f"because that is the is_a chain and the "
                    f"has-properties I hold for {LAST['x']}.")
        if k == "unknown":
            return (f"because nothing I was taught mentions "
                    f"{LAST['word']}; ask #{LAST['aid']} stays open.")

    if len(w) == 4 and w[0] == "is" and w[2] in ("a", "an"):
        x, y = w[1], w[3]
        if x not in KNOWN:
            return unknown_reply(x)
        if y not in KNOWN:
            return unknown_reply(y)
        found, chain = m.is_a_check(x, y)
        LAST.clear()
        LAST.update(kind="is_a", x=x, y=y, found=found, chain=chain)
        if found:
            return f"yes, {x} is {article(y)} {y}."
        return f"no, {x} is not {article(y)} {y}."

    if len(w) == 3 and w[0] == "can":
        x, z = w[1], w[2]
        if x not in KNOWN:
            return unknown_reply(x)
        res, chain = m.can_check(x, z)
        aid = None
        if res is None:
            aid = m.ask_file([x, "can", z, "?"],
                             reason="no verdict on the is_a chain",
                             road="dialogue")
        LAST.clear()
        LAST.update(kind="can", x=x, z=z, res=res, chain=chain,
                    aid=aid)
        if res is True:
            return f"yes, {x} can {z}."
        if res is False:
            return f"no, {x} cannot {z}."
        return (f"I do not know whether {x} can {z}. "
                f"I filed ask #{aid}.")

    if len(w) == 3 and w[:2] == ["what", "can"]:
        z = w[2]
        if z not in KNOWN:
            return unknown_reply(z)
        members = sorted(CAN_YES.get(z, ()))
        LAST.clear()
        LAST.update(kind="what_can", z=z, members=members)
        if not members:
            return f"nothing I know of can {z}."
        return f"{join_names(members)} can {z}."

    if len(w) == 5 and w[:4] == ["what", "is", "in", "the"]:
        y = w[4]
        if y not in KNOWN:
            return unknown_reply(y)
        items = sorted(IN_TC.get(y, ()))
        LAST.clear()
        LAST.update(kind="in", y=y, items=items)
        if not items:
            return f"nothing I know of is in the {y}."
        return f"in the {y}: {', '.join(items)}."

    if len(w) == 3 and w[:2] == ["what", "is"]:
        x = w[2]
        if x not in KNOWN:
            return unknown_reply(x)
        chain = m.reason_chain(x, "is_a")
        props = m.property_check(x)
        LAST.clear()
        LAST.update(kind="what_is", x=x, chain=chain, props=props)
        parts = []
        if len(chain) > 1:
            parts.append(f"{x} is_a {' -> '.join(chain[1:])}")
        else:
            parts.append(f"{x} has no is_a chain")
        if props:
            parts.append("has " + ", ".join(
                f"{p} ({src})" for p, src in props))
        return "; ".join(parts) + "."

    return HELP


# ── the scripted court: exact expected replies ─────────────────────

SCRIPT = [
    ("is cat an animal",
     "yes, cat is an animal."),
    ("why",
     "because cat is_a mammal and mammal is_a animal."),
    ("is cat a plant",
     "no, cat is not a plant."),
    ("why",
     "because the is_a chain runs cat -> mammal -> animal -> "
     "living_thing and never reaches plant."),
    ("can robin fly",
     "yes, robin can fly."),
    ("why",
     "because robin is_a bird and bird can fly."),
    ("can penguin fly",
     "no, penguin cannot fly."),
    ("why",
     "because penguin cannot fly was taught directly."),
    ("what can swim",
     "fish, penguin and salmon can swim."),
    ("why",
     "fish: taught directly; penguin: taught directly; "
     "salmon: is_a fish and fish can swim."),
    ("what is penguin",
     "penguin is_a bird -> animal -> living_thing; "
     "has feathers (from bird)."),
    ("what is in the closet",
     "in the closet: ball, box."),
    ("why",
     "ball: ball -> box -> closet; box: box -> closet."),
    ("is dragon an animal",
     "I do not know anything about dragon. I filed ask #2."),
    ("why",
     "because nothing I was taught mentions dragon; "
     "ask #2 stays open."),
    ("can cat fly",
     "I do not know whether cat can fly. I filed ask #3."),
    ("what is in the house",
     "in the house: ball, box, closet, room."),
    ("open the pod bay doors",
     HELP),
]

print("=" * 66)
print("  SHRDLU PROBE — dialogue over his facts, with WHY")
print("=" * 66)
check("no asks filed during teaching (dialogue starts clean)",
      len(m.asks_open()) == 0)

t0 = time.perf_counter()
results = []
print()
for q, expected in SCRIPT:
    got = answer(q)
    results.append((q, expected, got))
    print(f"  YOU>   {q}")
    print(f"  ISAAC> {got}")
t_dialogue = time.perf_counter() - t0

print()
for i, (q, expected, got) in enumerate(results, 1):
    check(f"turn {i:02d} ({q})", got == expected)

# the named lane requirements, asserted explicitly
check("why-trace shows the is_a chain actually used",
      results[1][2] == "because cat is_a mammal and mammal is_a "
                       "animal.")
check("reverse enumeration through the logic road",
      sorted(CAN_YES.get("swim", ())) == ["fish", "penguin",
                                          "salmon"])
check("honest unknown filed an ask (dragon is_a ?)",
      any(a["status"] == "open"
          and tuple(a["question"]) == ("dragon", "is_a", "?")
          for a in m.asks_open()))
check("no-verdict question filed an ask (cat can fly ?)",
      any(a["status"] == "open"
          and tuple(a["question"]) == ("cat", "can", "fly", "?")
          for a in m.asks_open()))
check("the engine filed ITS OWN chain-top ask (living_thing is_a)",
      any(a["road"] == "recall"
          and tuple(a["question"]) == ("living_thing", "is_a")
          for a in m.asks_open()))
check("exactly three open asks: his chain-top one + two dialogue",
      len(m.asks_open()) == 3)
check("at least 10 scripted turns", len(SCRIPT) >= 10)

print(f"\nwall-clock: teach {1000 * t_teach:.0f}ms | logic "
      f"ground+solve {1000 * t_logic:.0f}ms | dialogue "
      f"{1000 * t_dialogue:.0f}ms | total "
      f"{1000 * (t_teach + t_logic + t_dialogue):.0f}ms")

print(f"\nGATE: {'PASS' if not FAILS else 'FAIL (' + ','.join(FAILS) + ')'}")
sys.exit(1 if FAILS else 0)
