#!/usr/bin/env python3
"""problems.py -- word problems: set them up, resolve them, or ask.

    python walk/problems.py                lesson, his rules, quiz in three modes
    python walk/problems.py -quiz 300

Owner: "functional challenges. have him start using language. break
down word problems. at first just setting them up, and other times
resolving them, or asking for specifics again."

A generator writes simple word problems in varied wording and labels
each one itself: the quantities, what is asked, the relation, and the
answer (python computes it). Some leave a needed quantity out on
purpose. From a lesson of labeled problems he works out, by trying his
locators, where the quantities sit, what the unknown is, and which
words mean add / take away / times / split -- the relation words are
found by his own compare of problems that differ only in relation.

Three modes, graded separately:
    SET UP    quantities found, unknown named, relation classified
    RESOLVE   the expression built from the setup and RUN in python
    ASK       a quantity the relation needs is missing: he asks for it
              by name instead of answering
"""
import random
import re
import sys

# ----------------------------------------------------------- the generator
NAMES = ["Ana", "Ben", "Cleo", "Dev", "Emi", "Faye", "Gus", "Hal"]
THINGS = ["apples", "marbles", "books", "coins", "stickers", "pencils",
          "shells", "cards"]

# relation -> (templates, expression). {a} {b} numbers, {x} thing, {n} {m} names.
FORMS = {
    "add": (["{n} has {a} {x} and {m} gives {n} {b} more. How many {x} does {n} have now?",
             "There are {a} {x} in one box and {b} {x} in another. How many {x} are there in all?",
             "{n} picked {a} {x} in the morning and {b} {x} in the afternoon. How many {x} did {n} pick altogether?",
             "{n} had {a} {x}. Then {n} found {b} {x}. How many {x} does {n} have in total?"],
            "a + b"),
    "subtract": (["{n} has {a} {x} and gives {b} to {m}. How many {x} does {n} have left?",
                  "There were {a} {x} on the table. {n} took {b} of them. How many {x} remain?",
                  "{n} has {a} {x} and {m} has {b} {x}. How many more {x} does {n} have than {m}?",
                  "Out of {a} {x}, {b} were lost. How many {x} are left?"],
                 "a - b"),
    "multiply": (["{n} has {a} bags with {b} {x} in each bag. How many {x} does {n} have?",
                  "Each of {a} friends brings {b} {x}. How many {x} do they bring in all?",
                  "A shelf holds {b} {x}. How many {x} do {a} shelves hold?",
                  "{n} buys {a} packs of {x}, {b} per pack. How many {x} is that?"],
                 "a * b"),
    "divide": (["{n} shares {a} {x} equally among {b} friends. How many {x} does each friend get?",
                "{a} {x} are put into {b} equal piles. How many {x} are in each pile?",
                "{n} has {a} {x} and packs {b} in each box. How many boxes does {n} fill?",
                "If {a} {x} are split evenly into {b} groups, how many {x} are in each group?"],
               "a // b"),
}


def make(rng, missing=False):
    rel = rng.choice(sorted(FORMS))
    forms, expr = FORMS[rel]
    n, m = rng.sample(NAMES, 2)
    x = rng.choice(THINGS)
    b = rng.randint(2, 9)
    a = rng.randint(2, 9) * (b if rel == "divide" else 1) + (0 if rel == "divide" else rng.randint(0, 9))
    if rel == "subtract" and a < b:
        a, b = b, a
    text = rng.choice(forms).format(a=a, b=b, x=x, n=n, m=m)
    answer = eval(expr, {}, {"a": a, "b": b})
    if missing:                                  # take one quantity out
        drop = rng.choice(["a", "b"])
        val = a if drop == "a" else b
        text = re.sub(r"\b%d\b" % val, "some", text, count=1)
        return {"text": text, "rel": rel, "quantities": [b if drop == "a" else a],
                "thing": x, "answer": None, "missing": True}
    return {"text": text, "rel": rel, "quantities": [a, b], "thing": x,
            "answer": answer, "missing": False}


# ----------------------------------------------------------- his locators
def words(text):
    return re.findall(r"[a-z]+|\d+", text.lower())


def numbers(text):
    return [int(t) for t in re.findall(r"\b\d+\b", text)]


def unknown(text):
    """what is asked: the words after 'how many' up to the verb."""
    m = re.search(r"how many (\w+)", text.lower())
    return m.group(1) if m else None


def learn_relation(lesson):
    """by differentiation: for each relation, the word all its problems
    share that the most problems of other relations lack -- and the next
    such words, so one missing cue does not lose it."""
    by = {}
    for p in lesson:
        by.setdefault(p["rel"], []).append(set(words(p["text"])) - set(map(str, p["quantities"])))
    sig = {}
    for rel, sets in by.items():
        others = [s for r2, ss in by.items() if r2 != rel for s in ss]
        score = {}
        for w in set.union(*sets):
            here = sum(1 for s in sets if w in s) / len(sets)
            there = sum(1 for s in others if w in s) / max(len(others), 1)
            if here > there:
                score[w] = here - there
        sig[rel] = sorted(score.items(), key=lambda kv: -kv[1])[:6]
    return sig


def classify(text, sig):
    ws = set(words(text))
    best = None
    for rel, cues in sig.items():
        s = sum(v for w, v in cues if w in ws)
        if best is None or s > best[0]:
            best = (s, rel)
    return best[1] if best and best[0] > 0 else None


EXPR = {"add": "a + b", "subtract": "a - b", "multiply": "a * b", "divide": "a // b"}


def setup(text, sig):
    """his setup of a problem: quantities, unknown, relation."""
    q = numbers(text)
    return {"quantities": q, "unknown": unknown(text), "rel": classify(text, sig),
            "asks": "some" in words(text)}


def resolve(su):
    """RUN: the expression from the setup, in python."""
    if su["rel"] is None or len(su["quantities"]) < 2:
        return None
    a, b = su["quantities"][0], su["quantities"][1]
    try:
        return eval(EXPR[su["rel"]], {}, {"a": a, "b": b})
    except Exception:
        return None


def respond(text, sig):
    """set up; if a needed quantity is missing, ask; else resolve."""
    su = setup(text, sig)
    if su["rel"] is None:
        return su, "I don't know what to do with this one", None
    if len(su["quantities"]) < 2:
        thing = su["unknown"] or "them"
        return su, "How many %s? (one quantity is missing)" % thing, None
    ans = resolve(su)
    return su, "%s %s %s = %s" % (su["quantities"][0], {"add": "+", "subtract": "-",
                                                        "multiply": "x", "divide": "/"}[su["rel"]],
                                  su["quantities"][1], ans), ans


def main():
    n_quiz = int(sys.argv[sys.argv.index("-quiz") + 1]) if "-quiz" in sys.argv else 120
    n_lesson = int(sys.argv[sys.argv.index("-lesson") + 1]) if "-lesson" in sys.argv else 24
    learn_on = "-nolearn" not in sys.argv
    rng = random.Random(11)
    print("prediction, stated first: quantities and unknown above 90%; the "
          "relation from the words about 85%; resolving where the setup is "
          "right about 80%; asking when a quantity is missing above 90%.\n")
    lesson = [make(rng) for _ in range(n_lesson)]
    print("THE LESSON: %d problems, labeled by the generator. four of them:" % len(lesson))
    for p in lesson[:4]:
        print("  %s\n      quantities %s, relation %s, answer %s"
              % (p["text"], p["quantities"], p["rel"], p["answer"]))
    sig = learn_relation(lesson)
    print("\nHIS RELATION WORDS (found by comparing problems that differ in relation):")
    for rel, cues in sig.items():
        print("  %-9s %s" % (rel, ", ".join("%s %.2f" % kv for kv in cues)))

    quiz = [make(rng, missing=(i % 4 == 3)) for i in range(n_quiz)]
    c = dict(setup_q=0, setup_u=0, setup_rel=0, resolve=0, resolve_of=0, ask=0, ask_of=0,
             ask_right_thing=0, wrong_ask=0)
    shown = {"setup": [], "resolve": [], "ask": []}
    quarters = []
    q_right = q_n = 0
    for qi, p in enumerate(quiz):
        su, said, ans = respond(p["text"], sig)
        if learn_on and su["rel"] != p["rel"]:      # wrong: the problem joins
            lesson.append(p)                        # his lesson, he relearns
            sig = learn_relation(lesson)
        q_n += 1
        q_right += su["rel"] == p["rel"]
        if (qi + 1) % max(n_quiz // 4, 1) == 0:
            quarters.append(100.0 * q_right / q_n)
            q_right = q_n = 0
        ok_q = su["quantities"] == p["quantities"]
        ok_u = su["unknown"] is not None
        ok_r = su["rel"] == p["rel"]
        c["setup_q"] += ok_q; c["setup_u"] += ok_u; c["setup_rel"] += ok_r
        if p["missing"]:
            c["ask_of"] += 1
            asked = said.startswith("How many")
            c["ask"] += asked
            c["ask_right_thing"] += asked and (p["thing"] in said or (su["unknown"] or "") in p["text"])
            if len(shown["ask"]) < 2:
                shown["ask"].append((p, su, said, asked))
        else:
            c["resolve_of"] += 1
            right = ans == p["answer"]
            c["resolve"] += right
            c["wrong_ask"] += said.startswith("How many")
            if len(shown["resolve"]) < 3 or (not right and len(shown["resolve"]) < 5):
                shown["resolve"].append((p, su, said, right))
    n = len(quiz)
    print("\nTHE QUIZ: %d problems, one in four with a quantity missing" % n)
    print("  SET UP    quantities found %d/%d (%.0f%%)   unknown named %d/%d (%.0f%%)   "
          "relation right %d/%d (%.0f%%)"
          % (c["setup_q"], n, 100.0 * c["setup_q"] / n, c["setup_u"], n, 100.0 * c["setup_u"] / n,
             c["setup_rel"], n, 100.0 * c["setup_rel"] / n))
    print("  RESOLVE   right answer %d/%d (%.0f%%); asked instead of answering %d"
          % (c["resolve"], c["resolve_of"], 100.0 * c["resolve"] / max(c["resolve_of"], 1), c["wrong_ask"]))
    print("  ASK       asked when a quantity was missing %d/%d (%.0f%%); for the right thing %d"
          % (c["ask"], c["ask_of"], 100.0 * c["ask"] / max(c["ask_of"], 1), c["ask_right_thing"]))
    print("  relation right by quarter of the quiz%s: %s   (lesson grew to %d)"
          % ("" if learn_on else " (no learning during the quiz)",
             "  ".join("%.0f%%" % q for q in quarters), len(lesson)))
    if learn_on:
        print("\nHIS RELATION WORDS after the quiz:")
        for rel, cues in sig.items():
            print("  %-9s %s" % (rel, ", ".join("%s %.2f" % kv for kv in cues)))
    print("\nsome of his work (v right / x wrong):")
    for p, su, said, ok in shown["resolve"] + shown["ask"]:
        print("  %s %s" % ("v" if ok else "x", p["text"]))
        print("      setup: quantities %s, unknown '%s', relation %s"
              % (su["quantities"], su["unknown"], su["rel"]))
        print("      he says: %s%s" % (said, "" if ok or p["missing"] else
                                        "   (answer %s)" % p["answer"]))


if __name__ == "__main__":
    main()
