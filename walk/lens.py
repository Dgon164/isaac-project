#!/usr/bin/env python3
"""lens.py -- random lenses over his misses: something nobody designed.

    python walk/lens.py 999999 -jobs 24              3 generations, 4 seeds
    python walk/lens.py 999999 -jobs 24 -gens 5 -seeds 6

Owner: "a series of self-configuring randomized lenses... reward is best
match... if an answer is wrong, compare the answer vs the other, cycle
through random reservoirs and do atomic extraction to see what is
contributing meaning and how much."

ATOMS      what he can already see about a question and a candidate:
           the question's kind, which common words each carries, how
           many words they share and how rare, what the candidate
           carries (a year, a name, a number), whether a thesaurus pull
           landed. about a hundred yes/no facts. nothing weighted.
LENS       a few hundred RANDOM conjunctions of two or three atoms.
           nobody picks them. that is the reservoir: random, fixed, wide.
READOUT    for every graded question on his half, the right sentence
           beside the one he picked (or nearly picked). for each
           conjunction: present on the right side how often, on the
           wrong side how often. the log of that ratio is what the
           conjunction has earned. his differentiation, run wide.
RE-RANK    on a new question he answers as he does now; the lens then
           reorders his top twenty by what their conjunctions earned.
GENERATION several seeds, each tested ONCE on the other half. keep the
           best; drop the conjunctions that never separated anything;
           spawn new random ones in their place; test again.
EXTRACTION the top conjunctions printed as sentences: what carries
           meaning, and how much. the net is scaffolding; these are his.
"""
import json
import math
import os
import random
import sys
import time
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "engine"))
from core import Store
from linker import link, terms
import mind
from mind import score_all, diagnose, kind, feats, FEATS, load_tools, use

SQUAD = os.environ.get(
    "ISAAC_SQUAD",
    r"C:\Users\jtwee\Downloads\New folder (3)\intellon\train-v2.0.json")
TOP = 20                 # the field the lens reorders
COMMON = []              # the common question words, set from his half


def split(data, want):
    arts, n = [], 0
    for art in data:
        if n >= want:
            break
        n += sum(1 for p in art["paragraphs"] for qa in p["qas"]
                 if not qa.get("is_impossible"))
        arts.append(art)
    half = len(arts) // 2
    return arts[:half], arts[half:]


def fill(art):
    store = Store()
    for p in art["paragraphs"]:
        link(p["context"], store, tag=art["title"])
    return store


def questions(art):
    return [(qa["question"], qa["answers"][0]["text"])
            for p in art["paragraphs"] for qa in p["qas"]
            if not qa.get("is_impossible")]


# ------------------------------------------------------------------ atoms
def atoms(store, question, own, name):
    """the yes/no facts about one question and one candidate."""
    it = store.get(name)
    r = set(it.refs)
    a = {"q:" + kind(question)}
    shared = own & r
    a.add("share:%s" % (len(shared) if len(shared) < 3 else "3+"))
    if shared:
        rare = max(1.0 / len(store.get(t).refs) for t in shared
                   if store.get(t) and store.get(t).refs)
        a.add("rare:" + ("hi" if rare >= 0.5 else "mid" if rare >= 0.1 else "lo"))
    f = feats(it.content)
    for k in FEATS:
        if f.get(k):
            a.add("c:" + k)
    pulls = set()
    for t in own:
        pulls |= mind.SYN.get(t, set())
    if (pulls - own) & r:
        a.add("pull")
    for w in COMMON:
        if w in own:
            a.add("q:" + w)
            if w in r:
                a.add("both:" + w)
        elif w in r:
            a.add("c:" + w)
    n = len(r)
    a.add("len:" + ("short" if n < 8 else "mid" if n < 16 else "long"))
    return a


def all_atoms():
    out = ["q:" + k for k in mind.KIND_WORDS + ("other",)]
    out += ["share:0", "share:1", "share:2", "share:3+", "rare:hi", "rare:mid",
            "rare:lo", "pull", "len:short", "len:mid", "len:long"]
    out += ["c:" + k for k in FEATS]
    for w in COMMON:
        out += ["q:" + w, "c:" + w, "both:" + w]
    return out


# ------------------------------------------------------------------- lens
def new_lens(seed, size=300):
    rng = random.Random(seed)
    pool = all_atoms()
    conj = set()
    while len(conj) < size:
        k = rng.choice([2, 2, 3])
        conj.add(tuple(sorted(rng.sample(pool, k))))
    return sorted(conj)


LENS = []            # the conjunctions, in every worker
EARNED = {}          # conjunction -> log odds, in every worker


def init(common, lens, earned):
    load_tools()
    use("thes+kinds-second")
    COMMON[:] = common
    LENS[:] = lens
    EARNED.clear()
    EARNED.update(earned)


def pairs_one(art):
    """one article of his half: for each graded question, the atoms of
    the right sentence and of the one he picked or nearly picked."""
    store = fill(art)
    right_c, wrong_c = Counter(), Counter()
    n = 0
    for q, key in questions(art):
        seeds, reached, cands = score_all(store, q)
        d = diagnose(store, q, cands, reached, key)
        if not d["right"] or d["verdict"] == "not stored" or not cands:
            continue
        field = [name for _, name in cands[:TOP]]
        if d["right"] not in field:
            continue                     # the lens reorders his field only
        own = set(terms(q))
        for name in field:               # the right one against every other
            a = atoms(store, q, own, name)
            side = right_c if name == d["right"] else wrong_c
            for i, c in enumerate(LENS):
                if all(x in a for x in c):
                    side[i] += 1
            side["_n"] += 1
        n += 1
    return right_c, wrong_c, n


def readout(right_c, wrong_c):
    """what each conjunction earned: how much more often it sits on the
    right sentence than on the others, as a rate, so the many wrong
    candidates per question do not drown the one right one."""
    npos, nneg = max(right_c.get("_n", 0), 1), max(wrong_c.get("_n", 0), 1)
    return {i: math.log((right_c.get(i, 0) + 0.5) / npos /
                        ((wrong_c.get(i, 0) + 0.5) / nneg))
            for i in range(len(LENS))}


def rerank(store, q, cands, mode):
    """the lens as a direction signal where he has none. 'tie': it decides
    only exact ties in his full score, which today fall to name order.
    'seat': it takes the seat the kinds table holds, after shared words
    and rarity, before the rest."""
    own = set(terms(q))
    scored = []
    for j, (key, name) in enumerate(cands[:TOP]):
        a = atoms(store, q, own, name)
        s = sum(EARNED[i] for i, c in enumerate(LENS) if all(x in a for x in c))
        if mode == "tie":
            scored.append((tuple(-x for x in key), -s, j, key, name))
        else:
            scored.append(((-key[0], -key[1]), -s, j, key, name))
    scored.sort()
    return [(key, name) for _, _, _, key, name in scored] + cands[TOP:]


def exam_one(art):
    """the other half: right before the lens, right after it."""
    store = fill(art)
    asked = before = 0
    after = {"tie": 0, "seat": 0}
    for q, key in questions(art):
        _, _, cands = score_all(store, q)
        asked += 1
        k = key.lower()
        if cands and k in str(store.get(cands[0][1]).content).lower():
            before += 1
        for mode in after:
            if cands:
                re = rerank(store, q, cands, mode)
                if k in str(store.get(re[0][1]).content).lower():
                    after[mode] += 1
    return asked, before, after["tie"], after["seat"]


def run(fn, arts, jobs, common, lens, earned):
    if jobs > 1:
        from multiprocessing import Pool
        with Pool(jobs, initializer=init, initargs=(common, lens, earned)) as pool:
            return pool.map(fn, arts)
    init(common, lens, earned)
    return [fn(a) for a in arts]


def say(c):
    """a conjunction as a sentence."""
    words = []
    for x in c:
        k, _, v = x.partition(":")
        words.append({"q": "question is '%s'" % v if v in mind.KIND_WORDS + ("other",)
                      else "question has '%s'" % v,
                      "c": "candidate has '%s'" % v if v not in FEATS
                      else "candidate carries a %s" % v,
                      "both": "both have '%s'" % v,
                      "share": "they share %s words" % v,
                      "rare": "shared word is %s rarity" % v,
                      "len": "candidate is %s" % v,
                      "pull": "a thesaurus pull landed"}[k])
    return " AND ".join(words)


def main():
    want = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    jobs = int(sys.argv[sys.argv.index("-jobs") + 1]) if "-jobs" in sys.argv else 1
    gens = int(sys.argv[sys.argv.index("-gens") + 1]) if "-gens" in sys.argv else 3
    seeds = int(sys.argv[sys.argv.index("-seeds") + 1]) if "-seeds" in sys.argv else 4
    data = json.load(open(SQUAD, encoding="utf-8"))["data"]
    learn, exam = split(data, want)
    load_tools()
    cnt = Counter(t for art in learn for q, _ in questions(art) for t in set(terms(q)))
    COMMON[:] = [w for w, _ in cnt.most_common(40)]
    print("atoms: %d (the 40 common question words: %s ...)"
          % (len(all_atoms()), " ".join(COMMON[:12])))
    print("prediction, stated first: a first lens gains 1 to 3 points on the "
          "other half; its top atoms look like the kinds table plus "
          "paraphrase pairs.\n")

    best = None                          # (after, lens, earned, right_c, wrong_c)
    population = [new_lens(s) for s in range(seeds)]
    for g in range(1, gens + 1):
        print("GENERATION %d: %d lenses of %d conjunctions" % (g, len(population), len(population[0])))
        for li, lens in enumerate(population):
            t0 = time.perf_counter()
            parts = run(pairs_one, learn, jobs, COMMON, lens, {})
            rc, wc = Counter(), Counter()
            for r, w, n in parts:
                rc.update(r); wc.update(w)
            npairs = sum(n for _, _, n in parts)
            LENS[:] = lens
            earned = readout(rc, wc)
            res = run(exam_one, exam, jobs, COMMON, lens, earned)
            asked = sum(r[0] for r in res); before = sum(r[1] for r in res)
            tie = sum(r[2] for r in res); seat = sum(r[3] for r in res)
            after = max(tie, seat)
            print("  lens %d: %d pairs read; other half before %d; as tie-break "
                  "%d (%+d); in the kinds seat %d (%+d)   %.0fs"
                  % (li, npairs, before, tie, tie - before, seat, seat - before,
                     time.perf_counter() - t0))
            if best is None or after > best[0]:
                best = (after, lens, earned, rc, wc, asked, before)
        after, lens, earned, rc, wc, asked, before = best
        live = [c for i, c in enumerate(lens)
                if rc.get(i, 0) + wc.get(i, 0) >= 20 and abs(earned[i]) >= 0.3]
        print("  best so far %d (%+d). %d of %d conjunctions earned their place; "
              "the rest are replaced with new random ones\n"
              % (after, after - before, len(live), len(lens)))
        if g < gens:
            population = []
            for s in range(seeds):
                fresh = new_lens(1000 * g + s, size=len(lens) - len(live))
                population.append(sorted(set(live) | set(fresh)))

    after, lens, earned, rc, wc, asked, before = best
    print("RESULT: other half %d / %d before the lens (%.1f%%), %d after (%.1f%%), %+d"
          % (before, asked, 100.0 * before / asked, after, 100.0 * after / asked,
             after - before))
    print("\nWHAT CARRIES MEANING (top conjunctions by what they earned; "
          "right count / wrong count):")
    ranked = sorted(range(len(lens)), key=lambda i: -abs(earned[i]))
    shown = 0
    for i in ranked:
        if rc.get(i, 0) + wc.get(i, 0) < 20:
            continue
        print("  %+.2f  %5d / %-5d  %s" % (earned[i], rc.get(i, 0), wc.get(i, 0), say(lens[i])))
        shown += 1
        if shown == 24:
            break
    json.dump({"lens": [list(c) for c in lens], "earned": {str(i): earned[i] for i in earned},
               "right": dict(rc), "wrong": dict(wc), "common": COMMON},
              open(os.path.join(HERE, "lens.json"), "w", encoding="utf-8"))
    print("\nsaved walk/lens.json")


if __name__ == "__main__":
    main()
