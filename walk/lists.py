#!/usr/bin/env python3
"""lists.py -- list tests: change one word, then another, then two. the parts
that change are the attention for that kind of question.

    python walk/lists.py                 lesson, his slot rules, the tests
    python walk/lists.py -n 400

Owner: "give it a list of things and say who ran, who jogged, who watched,
who ate. then: what did the person who jogged do? it is teaching it the
parts that change as the attention for that kind of thing."

A LIST    four to six sentences from one skeleton, differing in one, two or
          three slots: "Ana jogged at the park. Ben ran at the beach. ..."
ALIGN     he lines the sentences up and marks the positions whose words
          differ: the changing parts. Everything else is the frame. No
          grammar: the list itself says what varies.
PIN       the question's words that sit in a changing part pin a sentence
          ("jogged" -> Ana's line). the answer is a changing part the
          question did NOT name.
WHICH     when more than one changing part is left, the question's kind
          word decides -- and he learns which kind wants which part from
          the lesson, by comparing questions that were answered by each
          part. when the lesson does not settle it, he asks which.
CHAIN     "what did the person who jogged do" pins by the verb, names the
          person, and asks the verb: the pin and the ask are the same part.
          "where did the person who jogged go" pins the verb, asks the place.
"""
import random
import re
import sys
from collections import Counter, defaultdict

NAMES = ["Ana", "Ben", "Cleo", "Dev", "Emi", "Faye", "Gus", "Hal", "Ivy", "Jon"]
VERBS = ["ran", "jogged", "walked", "swam", "sang", "read", "cooked", "slept", "painted", "waited"]
PLACES = ["park", "beach", "gym", "library", "kitchen", "garden", "station", "market"]
TIMES = ["morning", "noon", "evening", "night", "dawn", "afternoon"]
THINGS = ["soup", "bread", "rice", "cake", "fish", "pasta"]

SKELETONS = {
    1: ["{name} {verb}."],
    2: ["{name} {verb} at the {place}.", "{name} {verb} in the {time}.", "{name} ate {thing} at the {place}."],
    3: ["{name} {verb} at the {place} in the {time}."],
}
SLOT_POOL = {"name": NAMES, "verb": VERBS, "place": PLACES, "time": TIMES, "thing": THINGS}
# what each kind of question asks for, used ONLY to write the keys
ASKS = {"who": "name", "what did X do": "verb", "where": "place", "when": "time", "what did X eat": "thing"}


def make_list(rng, nslots):
    skel = rng.choice(SKELETONS[nslots])
    slots = re.findall(r"\{(\w+)\}", skel)
    n = rng.randint(4, 6)
    values = {s: rng.sample(SLOT_POOL[s], n) for s in slots}
    sents = [skel.format(**{s: values[s][i] for s in slots}) for i in range(n)]
    return skel, slots, values, sents


def make_questions(rng, slots, values, n):
    """questions with keys, every kind the slots allow, pinned by another slot."""
    qs = []
    for i in range(n):
        row = {s: values[s][i] for s in slots}
        for ask in slots:
            pins = [s for s in slots if s != ask]
            if not pins:
                continue
            pin = rng.choice(pins)
            pv = row[pin]
            if ask == "name":
                q = "who %s%s?" % (pv, "" if pin == "verb" else " was at the " + pv if pin == "place"
                                   else " was there in the " + pv if pin == "time" else " ate " + pv)
                if pin == "thing":
                    q = "who ate %s?" % pv
            elif ask == "verb":
                q = ("what did %s do?" % pv if pin == "name" else
                     "what did the person at the %s do?" % pv if pin == "place" else
                     "what did the person do in the %s?" % pv)
            elif ask == "place":
                q = ("where did %s go?" % pv if pin == "name" else
                     "where did the person who %s go?" % pv if pin == "verb" else
                     "where was the person in the %s?" % pv if pin == "time" else
                     "where was the %s eaten?" % pv)
            elif ask == "time":
                q = ("when did %s go?" % pv if pin == "name" else
                     "when did the person who %s go?" % pv if pin == "verb" else
                     "when was the person at the %s there?" % pv)
            else:  # thing
                q = ("what did %s eat?" % pv if pin == "name" else
                     "what was eaten at the %s?" % pv)
            qs.append((q, row[ask], ask, pin))
    rng.shuffle(qs)
    return qs


# ------------------------------------------------------------ his method
def words(t):
    return re.findall(r"[a-z]+", t.lower())


def align(sents):
    """the changing parts: positions whose word differs across the list."""
    rows = [words(s) for s in sents]
    width = min(len(r) for r in rows)
    changing = [i for i in range(width) if len({r[i] for r in rows}) > 1]
    return rows, changing


def column(rows, i):
    """the values a changing part takes across the list: its kind of thing."""
    return {r[i] for r in rows if i < len(r)}


KIND_WORDS = ["who", "where", "when", "what did", "what was"]


def kind_of(q):
    ql = q.lower()
    for k in KIND_WORDS:
        if ql.startswith(k):
            return k
    return "other"


def answer(q, sents, kind_map, rows=None, changing=None):
    """pin, then return the unpinned changing part; if several are left, the
    kind map decides; if it cannot, ask."""
    if rows is None:
        rows, changing = align(sents)
    qw = set(words(q))
    # which sentence: the one whose changing-part words the question names
    pinned = [(sum(1 for i in changing if r[i] in qw), j) for j, r in enumerate(rows)]
    best = max(pinned)
    if best[0] == 0:
        return None, "no changing part of any line is named in the question", None
    if sum(1 for p in pinned if p[0] == best[0]) > 1:
        return None, "more than one line fits the words named", None
    r = rows[best[1]]
    pinned_parts = [i for i in changing if r[i] in qw]
    free = [i for i in changing if i not in pinned_parts]
    k = kind_of(q)
    want = kind_map.get(k, set())                   # the kind of thing this
                                                    # question asks for
    def by_kind(parts):
        scored = sorted(((len(column(rows, i) & want), i) for i in parts), reverse=True)
        if scored and scored[0][0] > 0 and (len(scored) == 1 or scored[0][0] > scored[1][0]):
            return scored[0][1]
        return None
    i = by_kind(changing)
    if i is not None and i in pinned_parts:         # the chain: the question
        return r[i], "the question pins and asks the same part", i   # pins the
    if not free:                                                     # part it asks
        return r[pinned_parts[0]], "the question pins and asks the same part", pinned_parts[0]
    if len(free) == 1:
        return r[free[0]], "the one changing part the question did not name", free[0]
    i = by_kind(free)
    if i is not None:
        return r[i], "%d parts left; '%s' asks for the kind of thing this part holds (learned)" % (
            len(free), k), i
    return None, "which do you mean: %s?" % " or ".join(r[i] for i in free), None


def learn_kind_map(rng, n_lists=60):
    """which kind of question wants which KIND OF THING: from lists with
    keys, the values the keys took for each kind word. 'who' collects
    names, 'where' collects places -- his own word types, from the lists."""
    votes = defaultdict(Counter)
    for _ in range(n_lists):
        skel, slots, values, sents = make_list(rng, rng.choice([2, 3, 3]))
        for q, key, ask, pin in make_questions(rng, slots, values, len(sents)):
            votes[kind_of(q)][key.lower()] += 1
    return {k: set(c) for k, c in votes.items()}, votes


def main():
    n = int(sys.argv[sys.argv.index("-n") + 1]) if "-n" in sys.argv else 200
    rng = random.Random(4)
    print("prediction, stated first: one changing part -> near 100%%; two -> high once "
          "the kind map is learned; three -> the misses are where the kind word alone "
          "cannot pick the part, and he should ask rather than guess.\n")
    skel, slots, values, sents = make_list(rng, 2)
    rows, changing = align(sents)
    print("A LIST, and how he sees it:")
    for s in sents:
        print("  " + s)
    print("  changing parts at positions %s; the frame is: %s"
          % (changing, " ".join(w if i not in changing else "_" for i, w in enumerate(rows[0]))))
    kind_map, votes = learn_kind_map(rng)
    print("\nHIS KIND MAP (which kind of question wants which kind of thing; the things "
          "are his own word types, collected from 60 lists with keys):")
    for k, vals in kind_map.items():
        print("  %-10s -> %d things, e.g. %s" % (k, len(vals), ", ".join(sorted(vals)[:6])))

    print("\nTHE TESTS: %d lists each with one, two, three changing parts" % n)
    for nslots in (1, 2, 3):
        c = Counter()
        shown = []
        for _ in range(n):
            skel, slots, values, sents = make_list(rng, nslots)
            rows, changing = align(sents)
            for q, key, ask, pin in make_questions(rng, slots, values, len(sents)):
                got, why, part = answer(q, sents, kind_map, rows, changing)
                c["asked"] += 1
                if got is None and why.startswith("which do you mean"):
                    c["asked which"] += 1
                elif got is None:
                    c["no answer"] += 1
                elif got == key.lower():
                    c["right"] += 1
                else:
                    c["wrong"] += 1
                if len(shown) < 3 and (got != key.lower()) and nslots > 1:
                    shown.append((sents, q, key, got, why))
        print("  %d changing part%s: right %d / %d (%.1f%%), wrong %d, asked which %d, no answer %d"
              % (nslots, "s" if nslots > 1 else "", c["right"], c["asked"], 100.0 * c["right"] / c["asked"],
                 c["wrong"], c["asked which"], c["no answer"]))
        for sents, q, key, got, why in shown:
            print("      list: %s" % " | ".join(sents))
            print("      Q: %s   key: %s   he: %s   (%s)" % (q, key, got, why))
    print("\nTHE CHAIN, shown:")
    r9 = random.Random(9)
    skel, slots, values, sents = make_list(r9, 3)          # name, verb, place, time
    for s in sents:
        print("  " + s)
    for q in ("who %s?" % values["verb"][0],
              "what did %s do?" % values["name"][1],
              "what did the person who %s do?" % values["verb"][2],
              "where did the person who %s go?" % values["verb"][3],
              "when did the person at the %s go?" % values["place"][4 % len(sents)]):
        got, why, part = answer(q, sents, kind_map)
        print("  Q: %-45s he: %-10s (%s)" % (q, got, why))


if __name__ == "__main__":
    main()
