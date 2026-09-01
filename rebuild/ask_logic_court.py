"""ASK_LOGIC court — the solver road behind the two-tier gate.

Checks: forward query CERTIFIED with replayed legs; certified result
enters the FACTS layer (never the log); reverse query works; the
closed-world guard (unprovable -> filed ask, never a 'no'); and the
RULE-RELATIVITY BOUNDARY demonstrated on the planted dropped-join
rule: replay is sound relative to the rule, so trust rides on rule
ADMISSION (the court receipt), not on replay alone — the standing
lesson from bridge_soundness_probe, kept red-lettered here forever.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "..", "code"))
from isaac import Isaac  # noqa: E402

try:
    import clingo  # noqa: F401
except ImportError:
    print("SKIP: clingo not installed")
    sys.exit(77)

FAILS = []


def check(name, ok):
    print(f"  {'v' if ok else 'x'}  {name}")
    if not ok:
        FAILS.append(name)


W = ["zero", "one", "two", "three", "four", "five", "six", "seven",
     "eight", "nine", "ten"]
m = Isaac()
for a in range(10):
    for b in range(10):
        m.fact_add("sum", [a, b, a + b])
for d, w in enumerate(W):
    m.fact_add("word", [w, d])
m.rule_admit(
    "word_sum_rule", "word_sum", ["A", "B", "C"],
    [("word", ["A", "X"]), ("word", ["B", "Y"]),
     ("sum", ["X", "Y", "Z"]), ("word", ["C", "Z"])],
    "word_sum(A,B,C) :- word(A,X), word(B,Y), sum(X,Y,Z), word(C,Z).",
    court={"held_out": "100/100 leg-verified, logic_bridge_probe"})

n_log = len(m.observed_sequences)
ans, tier, rec = m.ask_logic("word_sum", ["three", "four", None])
check("forward query answers seven", ans == [["three", "four", "seven"]])
check("forward tier CERTIFIED", tier == "CERTIFIED")
check("receipt carries replayed legs",
      any("sum(3,4,7)" in line for line in rec))
check("certified result entered the FACTS layer",
      bool(m.facts_query(pred="word_sum", origin="certified")))
check("the LOG stayed pure", len(m.observed_sequences) == n_log)

ans2, tier2, _ = m.ask_logic("word_sum", ["three", None, "ten"])
check("reverse query (unknown in middle) answers seven",
      ans2 == [["three", "seven", "ten"]] and tier2 == "CERTIFIED")

n_asks = len(m.asks_open())
ans3, tier3, _ = m.ask_logic("word_sum", ["ten", "ten", None])
check("unprovable -> empty answer, tier 'ask'",
      ans3 == [] and tier3 == "ask")
check("closed-world guard: an ask was FILED, not a 'no'",
      len(m.asks_open()) == n_asks + 1)

# THE BOUNDARY, red-lettered: a dropped-join rule (word(C,W) — W
# unbound to the sum) derives wrong conclusions whose replay still
# grounds, because replay is faithful TO THE RULE. If someone admits
# a bogus rule with a fake court receipt, wrong facts certify. The
# trust therefore lives in rule ADMISSION; this check documents the
# boundary by asserting it exists exactly as measured.
m2 = Isaac()
for a in range(5):
    for b in range(5):
        m2.fact_add("sum", [a, b, a + b])
for d, w in enumerate(W[:9]):
    m2.fact_add("word", [w, d])
m2.rule_admit(
    "broken_dropped_join", "wsum2", ["A", "B", "C"],
    [("word", ["A", "X"]), ("word", ["B", "Y"]),
     ("sum", ["X", "Y", "Z"]), ("word", ["C", "W"])],
    "wsum2(A,B,C) :- word(A,X), word(B,Y), sum(X,Y,Z), word(C,W).",
    court={"note": "PLANTED BOGUS COURT — the boundary demo"})
wrong, wtier, _ = m2.ask_logic("wsum2", ["one", "one", "four"])
check("BOUNDARY: bogus-but-admitted rule certifies a wrong "
      "conclusion (rule-relativity is real; admission carries trust)",
      wrong == [["one", "one", "four"]])

print(f"\nGATE: {'PASS' if not FAILS else 'FAIL (' + ','.join(FAILS) + ')'}")
sys.exit(1 if FAILS else 0)
