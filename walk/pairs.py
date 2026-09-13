#!/usr/bin/env python3
"""pairs.py -- is there a general lesson in the graded runs?

    python walk/pairs.py 999999

Mine the first half of the articles, test on the second half, which
never contributed a pair. Grade every question against its key. When the question uses a word
the article never uses, and the right sentence was found anyway, pair
that question word with each word of the right sentence. A pair that
recurs across articles is a paraphrase he could learn from his own
record (grow -> raised, famous -> fame) -- a thesaurus grown from
feedback instead of installed from a file.
"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "engine"))
from core import Store
from linker import link, terms
from mind import score_all, diagnose, load_dictionary, SYN

SQUAD = os.environ.get(
    "ISAAC_SQUAD",
    r"C:\Users\jtwee\Downloads\New folder (3)\intellon\train-v2.0.json")


def work(art):
    store = Store()
    for p in art["paragraphs"]:
        link(p["context"], store, tag=art["title"])
    pairs = {}
    for p in art["paragraphs"]:
        for qa in p["qas"]:
            if qa.get("is_impossible"):
                continue
            q = qa["question"]
            seeds, reached, cands = score_all(store, q)
            d = diagnose(store, q, cands, reached, qa["answers"][0]["text"])
            if not d["right"] or d["verdict"] == "not stored":
                continue
            rt = [t for t in store.get(d["right"]).refs
                  if store.get(t) and store.get(t).kind == "term"]
            for m in d["missing"]:
                if store.get(m) is not None:     # the article uses it
                    continue
                for f in rt:
                    pairs[(m, f)] = pairs.get((m, f), 0) + 1
    return {k: 1 for k in pairs}                 # once per article


def score_pairs(tot):
    """a pair is a lesson when the two words keep each other's company:
    count squared over how often each word pairs with anything."""
    cm, cf = {}, {}
    for (m, f), c in tot.items():
        cm[m] = cm.get(m, 0) + c
        cf[f] = cf.get(f, 0) + c
    return {k: c * c / float(cm[k[0]] * cf[k[1]]) for k, c in tot.items()}


def bench(arts):
    """bed.py's number on these articles, with whatever SYN holds."""
    asked = top1 = 0
    for art in arts:
        store = Store()
        for p in art["paragraphs"]:
            link(p["context"], store, tag=art["title"])
        for p in art["paragraphs"]:
            for qa in p["qas"]:
                if qa.get("is_impossible"):
                    continue
                key = qa["answers"][0]["text"].lower()
                _, _, cands = score_all(store, qa["question"])
                asked += 1
                if cands and key in str(store.get(cands[0][1]).content).lower():
                    top1 += 1
    return asked, top1


def main():
    want = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    data = json.load(open(SQUAD, encoding="utf-8"))["data"]
    arts, n = [], 0
    for art in data:
        if n >= want:
            break
        n += sum(1 for p in art["paragraphs"] for qa in p["qas"]
                 if not qa.get("is_impossible"))
        arts.append(art)
    load_dictionary()
    half = len(arts) // 2
    learn, exam = arts[:half], arts[half:]

    t0 = time.time()
    tot = {}
    for a in learn:
        for k in work(a):
            tot[k] = tot.get(k, 0) + 1
    sc = score_pairs(tot)
    print("mined %d articles: %d distinct pairs, %.0fs"
          % (len(learn), len(tot), time.time() - t0))
    kept = sorted((k for k, c in tot.items() if c >= 3),
                  key=lambda k: -sc[k])
    print("best pairs by keeping company (seen in 3+ articles):")
    for m, f in kept[:40]:
        print("  %3d  %.3f  %-14s -> %s" % (tot[(m, f)], sc[(m, f)], m, f))

    print("\nthe other %d articles, never mined:" % len(exam))
    installed = {k: set(v) for k, v in SYN.items()}
    arms = [("wordnet only", None, 0)]
    for top in (100, 300, 1000, 3000):
        arms.append(("wordnet + best %d mined" % top, top, 0))
        arms.append(("best %d mined, no wordnet" % top, top, 1))
    for label, top, bare in arms:
        SYN.clear()
        if not bare:
            SYN.update({k: set(v) for k, v in installed.items()})
        n_add = 0
        for m, f in kept[:top or 0]:
            SYN.setdefault(m, set()).add(f)
            n_add += 1
        t0 = time.time()
        asked, top1 = bench(exam)
        print("  %-24s top1 %5d / %d (%.1f%%)   %d pairs added   %.0fs"
              % (label, top1, asked, 100.0 * top1 / asked, n_add,
                 time.time() - t0))


if __name__ == "__main__":
    main()
