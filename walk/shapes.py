#!/usr/bin/env python3
"""shapes.py -- a map of the shapes he knows: answer by analogy, and know
what he does not understand.

    python walk/shapes.py                 lesson, his map, quiz on seen and
                                          UNSEEN wording

Owner: "this sentence looks like these other sentences, these were the
answers for that so this should be the answers to that. A is like B like
C is like what. we are pulling data but not higher order details. he
doesn't understand what he understands."

SHAPE    a problem with the specifics taken out: numbers -> N, people -> P,
         things -> T, a blank -> N?. "Faye has 17 cards and gives 9 to
         Dev. How many cards does Faye have left?" becomes
         "P has N T and gives N to P . how many T does P have left ?"
MEANING  per shape, learned by test: which expression over the number
         slots (first - second, second * first, ...) reproduces the
         answers of every problem of that shape in the lesson.
THE MAP  every shape he has seen, its meaning, how many times, how sure.
         that is his understanding of what he understands.
ANALOGY  a new problem: same shape -> understood, apply the meaning. no
         same shape -> the nearest shapes by structure, their meaning,
         said as an analogy with its closeness. nothing near -> he says
         he does not understand this one, and asks.

The quiz holds one wording per relation OUT of the lesson, so the
analogy is tested on wording he never saw.
"""
import random
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, __file__.rsplit("\\", 1)[0] if "\\" in __file__ else ".")
from problems import FORMS, NAMES, THINGS, numbers, unknown

OPS = {"a + b": lambda a, b: a + b, "a - b": lambda a, b: a - b,
       "b - a": lambda a, b: b - a, "a * b": lambda a, b: a * b,
       "a // b": lambda a, b: a // b if b else None,
       "b // a": lambda a, b: b // a if a else None}


def gen(rng, forms_by_rel, missing=False):
    rel = rng.choice(sorted(forms_by_rel))
    form = rng.choice(forms_by_rel[rel])
    n, m = rng.sample(NAMES, 2)
    x = rng.choice(THINGS)
    b = rng.randint(2, 9)
    a = rng.randint(2, 9) * (b if rel == "divide" else 1) + (0 if rel == "divide" else rng.randint(0, 9))
    if rel == "subtract" and a < b:
        a, b = b, a
    text = form.format(a=a, b=b, x=x, n=n, m=m)
    answer = {"add": a + b, "subtract": a - b, "multiply": a * b, "divide": a // b}[rel]
    if missing:
        val = rng.choice([a, b])
        text = re.sub(r"\b%d\b" % val, "some", text, count=1)
        answer = None
    return {"text": text, "rel": rel, "answer": answer, "form": form}


# ------------------------------------------------------------------ shape
def shape(text):
    toks = re.findall(r"[A-Za-z]+|\d+|[.?,]", text)
    out = []
    for t in toks:
        if t.isdigit():
            out.append("N")
        elif t == "some":
            out.append("N?")
        elif t in NAMES:
            out.append("P")
        elif t.lower() in THINGS or t.lower().rstrip("s") in [x.rstrip("s") for x in THINGS]:
            out.append("T")
        else:
            out.append(t.lower())
    return tuple(out)


def learn_map(lesson):
    """shape -> the expression that reproduces every answer of that shape."""
    seen = defaultdict(list)
    for p in lesson:
        seen[shape(p["text"])].append(p)
    m = {}
    for sh, ps in seen.items():
        fits = []
        for name, f in OPS.items():
            ok = all(len(numbers(p["text"])) == 2 and
                     f(numbers(p["text"])[0], numbers(p["text"])[1]) == p["answer"] for p in ps)
            if ok:
                fits.append(name)
        m[sh] = {"n": len(ps), "meaning": fits[0] if fits else None,
                 "all": fits, "rel": Counter(p["rel"] for p in ps).most_common(1)[0][0]}
    return m


def closeness(a, b):
    """how alike two shapes are: shared token bigrams over all bigrams."""
    ba = set(zip(a, a[1:]))
    bb = set(zip(b, b[1:]))
    return len(ba & bb) / float(len(ba | bb) or 1)


def answer(text, m):
    """understood / by analogy / not understood."""
    sh = shape(text)
    q = numbers(text)
    if "N?" in sh:
        return None, "ask", "How many %s? (one number is missing)" % (unknown(text) or "of them"), sh
    if sh in m and m[sh]["meaning"]:
        val = OPS[m[sh]["meaning"]](q[0], q[1]) if len(q) == 2 else None
        return val, "understood", "shape seen %d times, meaning %s" % (m[sh]["n"], m[sh]["meaning"]), sh
    near = sorted(((closeness(sh, k), k) for k in m if m[k]["meaning"]), reverse=True)[:3]
    if not near or near[0][0] < 0.15:
        return None, "not understood", "no shape I know is like this one", sh
    c, k = near[0]
    val = OPS[m[k]["meaning"]](q[0], q[1]) if len(q) == 2 else None
    return val, "analogy", "like '%s' (%.0f%% alike, seen %d times, meaning %s)" % (
        " ".join(k)[:60], 100 * c, m[k]["n"], m[k]["meaning"]), sh


def main():
    rng = random.Random(5)
    # hold one wording per relation out of the lesson
    held = {rel: forms[0][rng.randrange(len(forms[0]))] for rel, forms in FORMS.items()}
    lesson_forms = {rel: [f for f in forms[0] if f != held[rel]] for rel, forms in FORMS.items()}
    quiz_forms = {rel: [held[rel]] for rel in FORMS}
    print("prediction, stated first: on wording he has seen, near 100%%; on "
          "wording held out of the lesson, the nearest shape carries the "
          "relation about 70%% of the time and slot order is where it slips.\n")
    lesson = [gen(rng, lesson_forms) for _ in range(120)]
    m = learn_map(lesson)
    print("HIS MAP: %d shapes from %d problems" % (len(m), len(lesson)))
    for sh, e in sorted(m.items(), key=lambda kv: -kv[1]["n"]):
        print("  %3dx  %-8s  %-7s  %s" % (e["n"], e["meaning"] or "??", e["rel"], " ".join(sh)[:78]))

    for label, forms in (("SEEN wording", lesson_forms), ("UNSEEN wording", quiz_forms)):
        quiz = [gen(rng, forms, missing=(i % 5 == 4)) for i in range(150)]
        c = Counter()
        shown = []
        by_close = defaultdict(lambda: [0, 0])          # closeness bucket -> [right, n]
        for p in quiz:
            val, how, why, sh = answer(p["text"], m)
            c[how] += 1
            if p["answer"] is None:
                c["ask ok"] += how == "ask"
            else:
                right = val == p["answer"]
                c[how + " right"] += right
                if how == "analogy":
                    pct = int(re.search(r"\((\d+)% alike", why).group(1))
                    b = "50%+" if pct >= 50 else "35-49%" if pct >= 35 else "20-34%" if pct >= 20 else "<20%"
                    by_close[b][0] += right
                    by_close[b][1] += 1
                if how != "understood" and len(shown) < 4:
                    shown.append((p, val, how, why, right))
        print("\nQUIZ on %s: %d problems" % (label, len(quiz)))
        for how in ("understood", "analogy", "not understood"):
            if c[how]:
                print("  %-15s %3d   right %3d" % (how, c[how], c[how + " right"]))
        print("  %-15s %3d   asked %3d" % ("missing number",
              sum(1 for p in quiz if p["answer"] is None), c["ask ok"]))
        if by_close:
            print("  how right the analogy is, by how alike the nearest shape was:")
            for b in ("50%+", "35-49%", "20-34%", "<20%"):
                if by_close[b][1]:
                    print("    %-7s %3d right of %3d" % (b, by_close[b][0], by_close[b][1]))
        for p, val, how, why, right in shown:
            print("    %s %s\n        %s -> %s   %s" % ("v" if right else "x", p["text"], how, val, why))

    # his map corrects its own trust: an analogy is only offered where his
    # record says that closeness has been right; elsewhere he says so and asks
    trusted = {b for b, (r, n) in by_close.items() if n >= 10 and r / float(n) >= 0.8}
    print("\nHE NOW TRUSTS AN ANALOGY ONLY AT: %s (from his own record above)"
          % (", ".join(sorted(trusted)) or "no closeness level"))
    quiz = [gen(rng, quiz_forms) for _ in range(120)]
    c = Counter()
    for p in quiz:
        val, how, why, sh = answer(p["text"], m)
        if how == "analogy":
            pct = int(re.search(r"\((\d+)% alike", why).group(1))
            b = "50%+" if pct >= 50 else "35-49%" if pct >= 35 else "20-34%" if pct >= 20 else "<20%"
            if b not in trusted:
                how, val = "not understood, asks", None
        c[how] += 1
        c[how + " right"] += val == p["answer"]
    print("QUIZ on fresh UNSEEN wording, %d problems, with that trust:" % len(quiz))
    for how in ("understood", "analogy", "not understood, asks", "not understood"):
        if c[how]:
            print("  %-22s %3d   right %3d" % (how, c[how], c[how + " right"]))


if __name__ == "__main__":
    main()
