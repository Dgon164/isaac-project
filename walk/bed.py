#!/usr/bin/env python3
"""bed.py -- the curriculum test bed. squad in, the walk answers, score out.

    python walk/bed.py 500              first 500 questions
    python walk/bed.py 500 -misses      also print each miss with the key
    python walk/bed.py 5000 -jobs 8     articles across 8 processes
    python walk/bed.py 999999 -jobs 12  the whole of squad

Jeopardy-style: he gets the wikipedia paragraphs of an article, then
the questions. The key says which detail was the answer, so every miss
is ablation material. Asks are pure reads, so workers change nothing
but the clock: totals must equal the serial run exactly.
"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "engine"))
from core import Store
from linker import link
from mind import ask, load_dictionary

SQUAD = r"C:\Users\jtwee\Downloads\New folder (3)\intellon\train-v2.0.json"


def init():
    load_dictionary()


def work(art):
    store = Store()
    for p in art["paragraphs"]:
        link(p["context"], store, tag=art["title"])
    asked = top1 = top3 = noseed = 0
    misses = []
    for p in art["paragraphs"]:
        for qa in p["qas"]:
            key = qa["answers"][0]["text"].lower()
            _, _, answers = ask(store, qa["question"])
            asked += 1
            got = [str(it.content).lower() for _, it in answers]
            if not answers:
                noseed += 1
                misses.append((art["title"], qa["question"], key, "(nothing)"))
            elif key in got[0]:
                top1 += 1; top3 += 1
            elif any(key in g for g in got):
                top3 += 1
            else:
                misses.append((art["title"], qa["question"], key, got[0][:90]))
    return asked, top1, top3, noseed, misses


def main():
    want = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    jobs = int(sys.argv[sys.argv.index("-jobs") + 1]) \
        if "-jobs" in sys.argv else 1
    data = json.load(open(SQUAD, encoding="utf-8"))["data"]
    arts, n = [], 0
    for art in data:
        if n >= want:
            break
        take = {"title": art["title"], "paragraphs": []}
        for p in art["paragraphs"]:
            qas = [qa for qa in p["qas"]
                   if not qa.get("is_impossible")][:max(0, want - n)]
            n += len(qas)
            take["paragraphs"].append({"context": p["context"], "qas": qas})
        arts.append(take)

    t0 = time.time()
    if jobs > 1:
        from multiprocessing import Pool
        with Pool(jobs, initializer=init) as pool:
            results = pool.map(work, arts)
    else:
        init()
        results = [work(a) for a in arts]
    dt = time.time() - t0

    asked = sum(r[0] for r in results)
    top1 = sum(r[1] for r in results)
    top3 = sum(r[2] for r in results)
    noseed = sum(r[3] for r in results)
    print("asked %d   top1 %d (%.1f%%)   top3 %d (%.1f%%)   nothing %d   "
          "%.1fs (%.0f q/s, jobs=%d)"
          % (asked, top1, 100.0 * top1 / asked, top3,
             100.0 * top3 / asked, noseed, dt, asked / dt, jobs))
    if "-misses" in sys.argv:
        for r in results:
            for t, q, key, got in r[4][:3]:
                print("MISS [%s] %s\n   key: %s\n   his: %s" % (t, q, key, got))


if __name__ == "__main__":
    main()
