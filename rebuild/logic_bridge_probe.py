# THE LOGIC BRIDGE — first rung: clingo (answer set programming).
# Owner direction 2026-08-23: "change isaac to build and work natively
# in the logic languages of gofai... use the best of the latest gofai
# and apply the learned materials to them."
#
# The pattern under test (from the two-tier discipline):
#   1. Isaac LEARNS material his way (observed sequences).
#   2. His learned facts COMPILE OUT to a logic program (mechanical
#      translation of his own experience — nothing hand-authored).
#   3. The external engine derives consequences he cannot reach
#      natively (the measured inference gap: he knows three=3 and
#      3+4=7 and cannot answer "three plus four").
#   4. Every derived answer is VERIFIED leg by leg against his OWN
#      store before it counts — the engine is an instrument; his
#      books stay the authority. Unverifiable answers are rejected.
#
# Courts: native score on 100 word problems (expect ~0 — never
# taught), bridged score (expect 100), verification rate (expect
# 100%), and the reverse query his matrix cannot do at all
# ("three plus WHAT is ten").
import sys

import clingo

sys.path.insert(0, r"C:\Users\jtwee\Documents\isaac-project\code")
from isaac import Isaac, tokenize                       # noqa: E402

W = ["zero", "one", "two", "three", "four", "five", "six", "seven",
     "eight", "nine", "ten", "eleven", "twelve", "thirteen",
     "fourteen", "fifteen", "sixteen", "seventeen", "eighteen"]

# 1. HE LEARNS (his way; no word-math anywhere)
m = Isaac()
for a in range(10):
    for b in range(10):
        m.observe(tokenize(f"{a} + {b} = {a + b}"))
for d in range(19):
    m.observe(tokenize(f"{W[d]} = {d}"))
m.consolidate()

# 2. NATIVE COURT — the measured gap
native = 0
for a in range(10):
    for b in range(10):
        ans, _ = m.lookup([W[a], "plus", W[b], "="])
        native += ans == W[a + b]
print(f"NATIVE: {native}/100 word problems (never taught in words)")

# 3. HIS EXPERIENCE COMPILES OUT — mechanical translation of his own
#    observed sequences; nothing is authored that he did not learn
facts = []
for seq in m.observed_sequences:
    if (len(seq) == 5 and seq[1] == "+" and seq[3] == "="
            and all(t.isdigit() for t in (seq[0], seq[2], seq[4]))):
        facts.append(f"sum({seq[0]},{seq[2]},{seq[4]}).")
    elif (len(seq) == 3 and seq[1] == "=" and seq[0].isalpha()
            and seq[2].isdigit()):
        facts.append(f"word({seq[0]},{seq[2]}).")
facts = sorted(set(facts))
print(f"EXPORT: {len(facts)} logic facts translated from his "
      f"observed sequences")

RULE = ("word_sum(A,B,C) :- word(A,X), word(B,Y), "
        "sum(X,Y,Z), word(C,Z).")
program = "\n".join(facts) + "\n" + RULE

ctl = clingo.Control(["--warn=none"])
ctl.add("base", [], program)
ctl.ground([("base", [])])
derived = {}
def _grab(model):
    for s in model.symbols(atoms=True):
        if s.name == "word_sum":
            a, b, c = (str(x) for x in s.arguments)
            derived[(a, b)] = c
ctl.solve(on_model=_grab)
print(f"BRIDGE: engine derived {len(derived)} word-sum consequences "
      f"from his facts")

# 4. VERIFICATION — every leg of every used answer checked against
#    HIS OWN store; the engine testifies, his books certify
def verify(a_w, b_w, c_w):
    legs = []
    xa, _ = m.lookup([a_w, "="])
    xb, _ = m.lookup([b_w, "="])
    legs += [(f"{a_w} = {xa}", xa is not None),
             (f"{b_w} = {xb}", xb is not None)]
    if xa is None or xb is None:
        return False, legs
    z, _ = m.lookup([xa, "+", xb, "="])
    legs.append((f"{xa} + {xb} = {z}", z is not None))
    zc, _ = m.lookup([c_w, "="])
    legs.append((f"{c_w} = {zc}", zc == z and z is not None))
    return all(ok for _, ok in legs), legs

bridged = verified = 0
for a in range(10):
    for b in range(10):
        got = derived.get((W[a], W[b]))
        if got == W[a + b]:
            bridged += 1
            ok, _ = verify(W[a], W[b], got)
            verified += ok
print(f"BRIDGED: {bridged}/100 correct   "
      f"VERIFIED against his own store: {verified}/{bridged}")

ok, legs = verify("three", "four", derived[("three", "four")])
print("\nreceipt for 'three plus four':")
for leg, good in legs:
    print(f"    {'v' if good else 'x'} {leg}   (his own lookup)")
print(f"    answer: {derived[('three', 'four')]}  "
      f"[derived externally, certified internally]")

# 4b. NEGATIVE CONTROLS — the verifier must be shown to REJECT.
#     (Review finding 2026-08-23: 100/100 verified is guaranteed by
#     construction when the store, the export, and the checker all
#     agree; prove the checker can fail closed.)
print("\nNEGATIVE CONTROL 1 — planted wrong derivation:")
ok_bad, legs_bad = verify("three", "four", "eight")   # wrong on purpose
print(f"    word_sum(three,four,EIGHT) -> verification "
      f"{'REJECTED (correct)' if not ok_bad else 'ACCEPTED (BUG!)'}")
for leg, good in legs_bad:
    print(f"      {'v' if good else 'x'} {leg}")

print("NEGATIVE CONTROL 2 — store missing a leg:")
m2 = Isaac()                       # twin taught WITHOUT "seven = 7"
for a in range(10):
    for b in range(10):
        m2.observe(tokenize(f"{a} + {b} = {a + b}"))
for d in range(19):
    if W[d] != "seven":
        m2.observe(tokenize(f"{W[d]} = {d}"))
m2.consolidate()
def verify_in(mm, a_w, b_w, c_w):
    xa, _ = mm.lookup([a_w, "="])
    xb, _ = mm.lookup([b_w, "="])
    if xa is None or xb is None:
        return False
    z, _ = mm.lookup([xa, "+", xb, "="])
    zc, _ = mm.lookup([c_w, "="])
    return z is not None and zc == z
ok_missing = verify_in(m2, "three", "four", "seven")
print(f"    same derivation vs a store lacking 'seven = 7' -> "
      f"{'REJECTED (correct)' if not ok_missing else 'ACCEPTED (BUG!)'}")
print("    (leg-verification certifies consistency WITH THE STORE, "
      "not truth; the store's own correctness is the audit road's "
      "job — stated plainly in the handoff)")

# 5. THE REVERSE QUERY — solve for the unknown in the middle,
#    something his matrix has no road for at all
ctl2 = clingo.Control(["--warn=none"])
ctl2.add("base", [], program + '\n#show ans/1.\n'
         'ans(B) :- word_sum(three, B, ten).')
ctl2.ground([("base", [])])
rev = []
ctl2.solve(on_model=lambda mo: rev.extend(
    str(s.arguments[0]) for s in mo.symbols(shown=True)
    if s.name == "ans"))
print(f"\nREVERSE: 'three plus WHAT is ten' -> {rev} "
      f"(want ['seven']; direction his matrix cannot answer)")
