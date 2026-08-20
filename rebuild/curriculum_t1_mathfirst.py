# T1 — THE ABSOLUTE SPINE, and the court of the owner's ruling.
# (owner 2026-08-20: "teaching logic and math first is the best thing
# because its absolute and native language, and then you can go from
# there.") Two claims courted here, plain numbers:
#   COURT 1 (the spine itself): closed worlds — tables, comparisons,
#     truth tables — learned to criterion in one pass, with honest
#     shrugs at every boundary.
#   COURT 2 (the ruling): A/B on the SECOND tongue (word-math).
#     Arm A: math spine first + small word-math dose.
#     Arm B: word-math alone at matched-or-larger dose, no spine.
#     Graded on SEEN word problems and HELD-OUT word problems.
#     If A > B anywhere, math-first transferred — measured, not
#     believed. Where BOTH fail on held-out, the miss localizes the
#     composition/inference wound exactly (the curriculum doubles as
#     diagnosis).
import sys

sys.path.insert(0, r"C:\Users\jtwee\Documents\isaac-project\code")
from isaac import Isaac, tokenize                       # noqa: E402

W = ["zero", "one", "two", "three", "four", "five",
     "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
     "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
     "eighteen"]


def sec(t):
    print("\n" + "=" * 64 + f"\n  {t}\n" + "=" * 64)


# ── COURT 1: the absolute spine, one pass ────────────────────────
sec("COURT 1 — the spine: tables, comparisons, truth tables")
spine = Isaac()
n_obs = 0
for a in range(13):
    for b in range(13):
        spine.observe(tokenize(f"{a} + {b} = {a + b}"))
        spine.observe(tokenize(f"{a} * {b} = {a * b}"))
        n_obs += 2
for a in range(10):
    for b in range(10):
        if a != b:
            spine.observe(tokenize(f"{a} > {b} = "
                                   f"{'true' if a > b else 'false'}"))
            n_obs += 1
for x in ["true", "false"]:
    for y in ["true", "false"]:
        xv, yv = x == "true", y == "true"
        spine.observe(tokenize(f"{x} and {y} = "
                               f"{'true' if xv and yv else 'false'}"))
        spine.observe(tokenize(f"{x} or {y} = "
                               f"{'true' if xv or yv else 'false'}"))
        spine.observe(tokenize(
            f"{x} implies {y} = {'true' if (not xv) or yv else 'false'}"))
        n_obs += 3
    spine.observe(tokenize(f"not {x} = "
                           f"{'false' if x == 'true' else 'true'}"))
    n_obs += 1
spine.consolidate()

quiz = [(["7", "+", "6", "="], "13"), (["11", "*", "12", "="], "132"),
        (["8", ">", "3", "="], "true"), (["2", ">", "9", "="], "false"),
        (["false", "or", "true", "="], "true"),
        (["true", "implies", "false", "="], "false"),
        (["not", "false", "="], "true"),
        (["false", "and", "false", "="], "false")]
ok = 0
for ctx, want in quiz:
    a, c = spine.lookup(ctx)
    ok += a == want
    print(f"  {'v' if a == want else 'x'} {' '.join(ctx)} -> {a} "
          f"(want {want})")
sh = 0
for ctx in [["25", "*", "25", "="], ["true", "xor", "true", "="]]:
    a, c = spine.lookup(ctx)
    honest = a is None
    sh += honest
    print(f"  {'v' if honest else 'x'} untaught {' '.join(ctx)} -> "
          f"{a!r} (shrug = honest; xor never taught here)")
print(f"  SPINE: {ok}/{len(quiz)} correct, {sh}/2 honest shrugs, "
      f"{n_obs} observations, one pass")

# ── COURT 2: the ruling's A/B on the second tongue ───────────────
sec("COURT 2 — A/B: does the spine help the second tongue?")
pairs = [(a, b) for a in range(10) for b in range(10) if a + b <= 18]
train = [(a, b) for (a, b) in pairs if (a * 7 + b * 3) % 5 != 0][:20]
held = [(a, b) for (a, b) in pairs if (a, b) not in train][:12]


def teach_word_map(m, reps):
    for _ in range(reps):
        for d in range(10):
            m.observe(tokenize(f"{W[d]} = {d}"))


def teach_word_sums(m, plist, reps):
    for _ in range(reps):
        for (a, b) in plist:
            m.observe(tokenize(f"{W[a]} plus {W[b]} = {W[a + b]}"))


# Arm A: the spine net CONTINUES (math first, then the bridge dose)
teach_word_map(spine, 3)
teach_word_sums(spine, train, 3)
spine.consolidate()

# Arm B: word-math only, matched-or-larger dose, no spine
b_net = Isaac()
teach_word_map(b_net, 3)
teach_word_sums(b_net, train, 6)          # DOUBLE the word-sum dose
b_net.consolidate()


def grade(m, plist, label):
    right = 0
    misses = []
    for (a, b) in plist:
        ans, _ = m.lookup([W[a], "plus", W[b], "="])
        if ans == W[a + b]:
            right += 1
        else:
            misses.append(f"{W[a]}+{W[b]}->{ans!r}")
    print(f"    {label}: {right}/{len(plist)}"
          + (f"   e.g. {misses[0]}" if misses else ""))
    return right


print("  SEEN word problems (recall):")
a_seen = grade(spine, train[:10], "arm A (spine+words x3)")
b_seen = grade(b_net, train[:10], "arm B (words-only x6)  ")
print("  HELD-OUT word problems (transfer — never taught in words):")
a_held = grade(spine, held, "arm A (spine+words x3)")
b_held = grade(b_net, held, "arm B (words-only x6)  ")
print("  digit check (does B know ANY native math?):")
a, _ = b_net.lookup(["3", "+", "4", "="])
print(f"    arm B 3+4= -> {a!r} (expected shrug — never taught digits"
      f" beyond the word map)")

sec("VERDICT")
print(f"  spine one-pass: {ok}/{len(quiz)}; "
      f"seen A {a_seen}/10 vs B {b_seen}/10; "
      f"held-out A {a_held}/{len(held)} vs B {b_held}/{len(held)}")
if a_held > b_held:
    print("  MATH-FIRST TRANSFERRED: the spine arm answers word "
          "problems it was never taught in words.")
elif a_held == b_held == 0:
    print("  NEITHER ARM COMPOSES: held-out word-math needs an "
          "inference road (word->digit->matrix->digit->word). The "
          "wound is LOCALIZED: recall is exact, composition is "
          "absent — the missing op, seen from the curriculum side.")
else:
    print("  ruling not supported at this dose — filed honestly.")
