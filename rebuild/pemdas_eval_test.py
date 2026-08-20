# EXPRESSION REDUCTION TEST — pair-at-a-time evaluation at scale.
# Order of operations is TAUGHT (teach("*","precedes","+")), not
# hard-coded. Every multi-step answer must reduce through pairs he
# actually knows, or refuse. Hundreds of generated problems per exam.
import random
import sys

sys.path.insert(0, r"C:\Users\jtwee\Documents\isaac-project\code")
from isaac import Isaac, tokenize                       # noqa: E402

random.seed(20260820)
m = Isaac()
for a in range(20):
    for b in range(20):
        m.observe(tokenize(f"{a} + {b} = {a + b}"))
        m.observe(tokenize(f"{a} * {b} = {a * b}"))
for x in ["true", "false"]:
    for y in ["true", "false"]:
        xv, yv = x == "true", y == "true"
        m.observe(tokenize(f"{x} and {y} = "
                           f"{'true' if xv and yv else 'false'}"))
        m.observe(tokenize(f"{x} or {y} = "
                           f"{'true' if xv or yv else 'false'}"))
# ORDER OF OPERATIONS, TAUGHT AS FACTS:
m.teach("*", "precedes", "+")
m.teach("and", "precedes", "or")

print("worked example (interim state tracking):")
ans, conf, steps = m.evaluate(tokenize("2 + 3 * 4 ="))
for a_, op, b_, r in steps:
    print(f"    {a_} {op} {b_} -> {r}")
print(f"    answer: {ans} (want 14, NOT 20 — taught precedence)")

print("\nEXAM A — 200 three-operand additions (was 13/100 right, "
      "87/100 WRONG before the reducer)")
right = wrong = refused = 0
for _ in range(200):
    a, b, c = (random.randrange(10) for _ in range(3))
    ans, _ = m.lookup([str(a), "+", str(b), "+", str(c), "="])
    if ans == str(a + b + c):
        right += 1
    elif ans is None:
        refused += 1
    else:
        wrong += 1
print(f"  right {right}/200   refused {refused}/200   WRONG {wrong}/200")

print("\nEXAM B — 200 mixed a + b * c (precedence must beat "
      "left-to-right)")
right = wrong_ltr = wrong = refused = 0
for _ in range(200):
    a = random.randrange(10)
    b = random.randrange(2, 10)
    c = random.randrange(2, 19 // b + 1)
    ans, _ = m.lookup([str(a), "+", str(b), "*", str(c), "="])
    if ans == str(a + b * c):
        right += 1
    elif ans == str((a + b) * c):
        wrong_ltr += 1
    elif ans is None:
        refused += 1
    else:
        wrong += 1
print(f"  right {right}/200   left-to-right-error {wrong_ltr}/200   "
      f"other-wrong {wrong}/200   refused {refused}/200")

print("\nEXAM C — 200 parenthesized ( a + b ) * c (subsections "
      "innermost first)")
right = wrong = refused = 0
for _ in range(200):
    a, b = random.randrange(10), random.randrange(10)
    c = random.randrange(2, 10)
    ans, _ = m.lookup(tokenize(f"( {a} + {b} ) * {c} ="))
    if ans == str((a + b) * c):
        right += 1
    elif ans is None:
        refused += 1
    else:
        wrong += 1
print(f"  right {right}/200   wrong {wrong}/200   refused {refused}/200")

print("\nEXAM D — logic chains, exhaustive: x and y or z / "
      "x or y and z (and-precedes-or must discriminate)")
right = wrong = 0
for x in ["true", "false"]:
    for y in ["true", "false"]:
        for z in ["true", "false"]:
            xv, yv, zv = (v == "true" for v in (x, y, z))
            ans, _ = m.lookup([x, "and", y, "or", z, "="])
            right += ans == ("true" if (xv and yv) or zv else "false")
            wrong += ans not in (None,
                                 "true" if (xv and yv) or zv else "false")
            ans, _ = m.lookup([x, "or", y, "and", z, "="])
            right += ans == ("true" if xv or (yv and zv) else "false")
            wrong += ans not in (None,
                                 "true" if xv or (yv and zv) else "false")
print(f"  right {right}/16   wrong {wrong}/16")

print("\nEXAM E — honesty: 100 expressions with an unanswerable step")
refused = wrong = 0
for i in range(100):
    if i % 2:
        q = tokenize(f"{random.randrange(10)} / 2 + 1 =")   # / untaught
    else:
        q = ["true", "and", str(random.randrange(10)), "or", "false", "="]
    ans, _ = m.lookup(q)
    if ans is None:
        refused += 1
    else:
        wrong += 1
print(f"  refused (honest) {refused}/100   answered-anyway {wrong}/100")

print("\nfailed-step trace (the refusal shows its work):")
ans, conf, steps = m.evaluate(tokenize("8 / 2 + 1 ="))
for a_, op, b_, r in steps:
    print(f"    {a_} {op} {b_} -> {r}")
print(f"    answer: {ans} (refused at the unknown pair)")
