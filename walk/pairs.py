#!/usr/bin/env python3
"""pairs.py -- is there a general lesson in the graded runs?

    python walk/pairs.py 999999

Grade every question against its key. When the question uses a word
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
from mind import score_all, diagnose, load_dictionary

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
    t0 = time.time()
    tot = {}
    for a in arts:
        for k in work(a):
            tot[k] = tot.get(k, 0) + 1
    print("%d articles, %d distinct pairs, %.0fs" % (len(arts), len(tot),
                                                     time.time() - t0))
    top = sorted(tot.items(), key=lambda kv: -kv[1])
    print("pairs seen in the most articles (question word -> word in the "
          "right sentence):")
    for (m, f), c in top[:60]:
        print("  %3d  %-14s -> %s" % (c, m, f))


if __name__ == "__main__":
    main()
