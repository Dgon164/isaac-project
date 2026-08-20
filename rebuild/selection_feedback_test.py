# SELECTION + FEEDBACK TEST (owner design 2026-08-20): ranked top-k
# answers instead of a single final; multi-word completion;
# fill-in-the-blank at beginning/middle/end; good/marginal/bad
# feedback on answers and on suggested connections; feedback changes
# future rankings; everything survives save/load.
import os
import sys

sys.path.insert(0, r"C:\Users\jtwee\Documents\isaac-project\code")
from isaac import Isaac, tokenize                       # noqa: E402

SCRATCH = (r"C:\Users\jtwee\AppData\Local\Temp\claude"
           r"\c--Users-jtwee-Downloads-New-folder--3-"
           r"\d93c0d2c-8d04-45aa-9f80-804c774fbc7e\scratchpad")

m = Isaac()
for s in ["a florb is an animal .", "a grinth is an animal .",
          "the florb walked .", "the grinth flew .",
          "the florb slept .", "the grinth slept .",
          "a florb eats moss .", "a grinth eats seeds .",
          "the small florb walked .", "the big grinth flew ."]:
    for _ in range(3):
        m.observe(tokenize(s))
W = ["zero", "one", "two", "three", "four"]
for a in range(3):
    for b in range(3):
        m.observe(tokenize(f"{W[a]} plus {W[b]} = {W[a + b]}"))
m.consolidate()
passed, failed = 0, []


def court(name, ok, detail=""):
    global passed
    print(f"  {'PASS' if ok else 'FAIL'}  {name}  {detail}")
    if ok:
        passed += 1
    else:
        failed.append(name)


print("1. RANKED SELECTION (end position)")
r = m.lookup_topk(["a", "grinth", "eats"], k=4)
print(f"   a grinth eats -> {[(c, round(s, 2)) for c, s in r]}")
court("ranked list returned (one entry is correct when only one "
      "candidate clears the score floor)", len(r) >= 1)
court("right answer in the selection",
      any(c == "seeds" for c, _ in r))
court("best-to-least order",
      all(r[i][1] >= r[i + 1][1] for i in range(len(r) - 1)))

print("2. FILL-IN-THE-BLANK — beginning / middle / end")
rb = m.cloze_topk([], ["grinth", "flew", "."], k=4)
print(f"   [_] grinth flew . -> {[(c, round(s, 2)) for c, s in rb]}")
court("beginning blank offers sentence starters",
      any(c in ("the", "a") for c, _ in rb))
rm = m.cloze_topk(["the"], ["flew", "."], k=4)
print(f"   the [_] flew .   -> {[(c, round(s, 2)) for c, s in rm]}")
court("middle blank ranks the flyer first",
      bool(rm) and rm[0][0] == "grinth")
re_ = m.lookup_topk(["a", "florb", "is", "an"], k=3)
print(f"   a florb is an [_] -> {[(c, round(s, 2)) for c, s in re_]}")
court("end blank finds the category",
      any(c == "animal" for c, _ in re_))

print("3. MULTI-WORD COMPLETION")
mc = m.complete_topk(["the", "florb"], k=3)
print(f"   the florb ... -> {mc}")
court("multi-word candidates returned", len(mc) >= 2)
court("a full lived sentence among them",
      any(seq[:2] in (["walked", "."], ["slept", "."]) for seq, _ in mc))

print("4. FEEDBACK — good / marginal / bad on answers")
before = m.lookup_topk(["zero", "plus", "zero", "="], k=4)
print(f"   before: zero plus zero = -> "
      f"{[(c, round(s, 2)) for c, s in before]}")
wrongs = [c for c, _ in before if c != "zero"]
if wrongs:
    m.feedback(["zero", "plus", "zero", "="], wrongs[0], "bad")
m.feedback(["zero", "plus", "zero", "="], "zero", "good")
m.feedback(["zero", "plus", "zero", "="], "one", "marginal")
after = m.lookup_topk(["zero", "plus", "zero", "="], k=4)
print(f"   after : zero plus zero = -> "
      f"{[(c, round(s, 2)) for c, s in after]}")
court("good-graded answer now ranks first",
      bool(after) and after[0][0] == "zero")
court("bad-graded answer suppressed",
      not wrongs or [c for c, _ in after].index(wrongs[0]) >
      [c for c, _ in before].index(wrongs[0])
      if wrongs and wrongs[0] in [c for c, _ in after] else True)
court("all three grades logged",
      len(m.feedback_log) == 3
      and {e["grade"] for e in m.feedback_log}
      == {"good", "marginal", "bad"})

print("5. FEEDBACK on suggested connections")
m.feedback_connection("florb", "flew", "good")
court("good connection becomes an edge",
      m.net.has_door("florb", "flew"))
m.feedback_connection("zim", "walked", "bad")
court("bad connection locked out", ("zim", "walked") in m.lockouts)

print("6. SURVIVES SAVE/LOAD (v2 file)")
p = os.path.join(SCRATCH, "selection_test.isaac2")
m.save(p)
t = Isaac.load(p)
court("feedback log persists", len(t.feedback_log) == 5)
ta = t.lookup_topk(["zero", "plus", "zero", "="], k=4)
court("adjusted ranking persists", bool(ta) and ta[0][0] == "zero")
court("locked-out connection persists",
      ("zim", "walked") in t.lockouts)

print(f"\nRESULT: {passed}/{passed + len(failed)} checks passed"
      + (f"; FAILED: {failed}" if failed else ""))
