#!/usr/bin/env python3
"""tools.py -- the tools he builds himself, from his own record.

    python walk/tools.py learn 999999      grade the first half of the
                                            articles, build the tools,
                                            write walk/tools.json
    python walk/tools.py court 999999 -jobs 12
                                            the other half, never learned
                                            from: wordnet vs his tools

No installed dictionary. Everything here is mined from graded runs --
his pick, the right item, the question -- and nothing else.

THESAURUS   a question word the article never used, paired with the
            words of the right sentence; kept when the two keep each
            other's company across articles (begin->began, honor->
            honour, convinced->persuaded).
DICTIONARY  built from reading, per store: the words of the text that
            keep each other's company across its sentences. No feedback
            needed; it comes out of the material he was given.
KINDS       the question's kind word (who / when / where / how many)
            against what the right sentence carried (a year, a number,
            a name, a percent) -- how much more often than the sentences
            he picked wrongly. A reference table for what kind of answer
            counts.
"""
import json, math, os, re, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "engine"))
from core import Store
from linker import link, terms
import mind
from mind import score_all, diagnose, kind, feats, FEATS, read_dictionary

SQUAD = os.environ.get(
    "ISAAC_SQUAD",
    r"C:\Users\jtwee\Downloads\New folder (3)\intellon\train-v2.0.json")
TOOLS = os.path.join(HERE, "tools.json")
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


# ------------------------------------------------------------- learning
def learn(arts):
    pairs = {}                       # (question word, sentence word) -> articles
    right_f = {}                     # (kind, feat) -> count in right sentences
    wrong_f = {}                     # (kind, feat) -> count in his wrong picks
    n_k = {}                         # kind -> graded questions
    for art in arts:
        store = fill(art)
        seen = set()
        for q, key in questions(art):
            seeds, reached, cands = score_all(store, q)
            d = diagnose(store, q, cands, reached, key)
            if not d["right"] or d["verdict"] == "not stored":
                continue
            k = kind(q)
            n_k[k] = n_k.get(k, 0) + 1
            rf = feats(store.get(d["right"]).content)
            for f, v in rf.items():
                right_f[(k, f)] = right_f.get((k, f), 0) + int(v)
            for _, n in cands[:3]:            # what he ranked up there wrongly
                if n == d["right"]:
                    continue
                wf = feats(store.get(n).content)
                for f, v in wf.items():
                    wrong_f[(k, f)] = wrong_f.get((k, f), 0) + int(v) / 3.0
            rt = [t for t in store.get(d["right"]).refs
                  if store.get(t) and store.get(t).kind == "term"]
            for m in d["missing"]:
                if store.get(m) is not None:
                    continue
                for f in rt:
                    seen.add((m, f))
        for p in seen:
            pairs[p] = pairs.get(p, 0) + 1

    cm, cf = {}, {}
    for (m, f), c in pairs.items():
        cm[m] = cm.get(m, 0) + c
        cf[f] = cf.get(f, 0) + c
    kept = sorted(((c * c / float(cm[m] * cf[f]), m, f)
                   for (m, f), c in pairs.items() if c >= 3), reverse=True)
    thesaurus = {}
    for _, m, f in kept[:3000]:
        thesaurus.setdefault(m, []).append(f)

    kinds = {}
    for k in n_k:
        row = {}
        for f in FEATS:
            r = right_f.get((k, f), 0) / float(n_k[k])
            w = wrong_f.get((k, f), 0) / float(n_k[k])
            row[f] = round(math.log((r + 0.01) / (w + 0.01)), 3)
        kinds[k] = row
    return thesaurus, kinds, len(pairs), n_k


# ------------------------------------------------------------- the court
ARM = {}


def arm(thes, use_kinds, reading):
    """set the tools for this arm -- in this process and, through the
    pool initializer, in every worker (windows spawns, nothing carries)."""
    mind.SYN.clear(); mind.KINDS.clear()
    tools = json.load(open(TOOLS, encoding="utf-8"))
    if thes == "wordnet":
        mind.load_dictionary(wordnet=True)
    elif thes == "his":
        mind.SYN.update((k, set(v)) for k, v in tools["thesaurus"].items())
    if use_kinds:
        mind.KINDS.update(tools["kinds"])
    ARM.update(thes=thes, kinds=use_kinds, reading=reading)


def bench_one(art):
    store = fill(art)
    if ARM.get("reading"):
        read_dictionary(store)
    asked = top1 = 0
    for q, key in questions(art):
        _, _, cands = score_all(store, q)
        asked += 1
        if cands and key.lower() in str(store.get(cands[0][1]).content).lower():
            top1 += 1
    return asked, top1


def bench(arts, jobs=1):
    if jobs > 1:
        from multiprocessing import Pool
        with Pool(jobs, initializer=arm, initargs=(ARM["thes"], ARM["kinds"],
                                                   ARM["reading"])) as pool:
            res = pool.map(bench_one, arts)
    else:
        res = [bench_one(a) for a in arts]
    return sum(r[0] for r in res), sum(r[1] for r in res)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "court"
    want = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
    data = json.load(open(SQUAD, encoding="utf-8"))["data"]
    learn_arts, exam = split(data, want)

    if cmd == "learn":
        mind.SYN.clear(); mind.KINDS.clear()       # nothing installed
        t0 = time.time()
        thesaurus, kinds, n_pairs, n_k = learn(learn_arts)
        json.dump({"thesaurus": thesaurus, "kinds": kinds},
                  open(TOOLS, "w", encoding="utf-8"), indent=1)
        print("learned from %d articles in %.0fs: %d pairs seen, %d kept "
              "into the thesaurus; kinds table over %s"
              % (len(learn_arts), time.time() - t0, n_pairs,
                 sum(len(v) for v in thesaurus.values()),
                 ", ".join("%s %d" % kv for kv in sorted(n_k.items()))))
        print("his kinds table (log odds right vs his wrong picks):")
        print("  %-9s" % "" + "".join("%9s" % f for f in FEATS))
        for k, row in sorted(kinds.items()):
            print("  %-9s" % k + "".join("%9.2f" % row[f] for f in FEATS))
        return

    arms = [("wordnet (installed)", "wordnet", False),
            ("his thesaurus", "his", False),
            ("his thesaurus + his kinds", "his", True),
            ("nothing", "none", False),
            ("his kinds alone", "none", True),
            ("his dictionary from reading, alone", "none", False, True),
            ("all three of his", "his", True, True)]
    jobs = int(sys.argv[sys.argv.index("-jobs") + 1]) \
        if "-jobs" in sys.argv else 1
    print("the other %d articles, never learned from:" % len(exam))
    for label, thes, use_kinds, *reading in arms:
        arm(thes, use_kinds, bool(reading and reading[0]))
        t0 = time.time()
        asked, top1 = bench(exam, jobs)
        print("  %-28s top1 %5d / %d (%.1f%%)   %.0fs"
              % (label, top1, asked, 100.0 * top1 / asked, time.time() - t0))


if __name__ == "__main__":
    main()
