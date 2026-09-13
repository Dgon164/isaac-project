#!/usr/bin/env python3
"""overlap.py -- do articles reinforce each other, interfere, or neither?

    python walk/overlap.py 1 -jobs 12      per-article + sample-spread stats
    python walk/overlap.py 10 -jobs 12     stores of 10 articles each
    python walk/overlap.py all -jobs 12    one store holding every article

Same questions, same scoring as bed.py. The only variable is how many
articles share a store. Every top-1 answer is stamped own/foreign by
its tag, so reinforcement (foreign article gave the right answer) and
interference (foreign article stole the top spot with a wrong one)
are counted, not guessed.
"""
import json, os, random, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "engine"))
from core import Store
from linker import link
from mind import ask, load_dictionary

SQUAD = r"C:\Users\jtwee\Downloads\New folder (3)\intellon\train-v2.0.json"


def init():
    load_dictionary()


def work(job):
    build, ask_arts = job
    store = Store()
    for art in build:
        for p in art["paragraphs"]:
            link(p["context"], store, tag=art["title"])
    per_art = []
    tot = [0, 0, 0, 0, 0]   # asked, top1, top3, foreign_right, foreign_wrong
    for art in ask_arts:
        a = t1 = 0
        for p in art["paragraphs"]:
            for qa in p["qas"]:
                if qa.get("is_impossible"):
                    continue
                key = qa["answers"][0]["text"].lower()
                _, _, answers = ask(store, qa["question"])
                got = [str(it.content).lower() for _, it in answers]
                a += 1
                tot[0] += 1
                right = bool(got) and key in got[0]
                if right:
                    t1 += 1
                    tot[1] += 1
                if any(key in g for g in got):
                    tot[2] += 1
                if answers and answers[0][1].tag != art["title"]:
                    tot[3 if right else 4] += 1
        per_art.append((art["title"], a, t1))
    return tot, per_art


def main():
    pool = sys.argv[1] if len(sys.argv) > 1 else "1"
    jobs = int(sys.argv[sys.argv.index("-jobs") + 1]) \
        if "-jobs" in sys.argv else 1
    data = json.load(open(SQUAD, encoding="utf-8"))["data"]

    if pool == "all":
        chunk = max(1, len(data) // max(jobs, 1))
        jobsl = [(data, data[i:i + chunk])
                 for i in range(0, len(data), chunk)]
    else:
        k = int(pool)
        jobsl = [(data[i:i + k], data[i:i + k])
                 for i in range(0, len(data), k)]

    t0 = time.time()
    if jobs > 1:
        from multiprocessing import Pool
        with Pool(jobs, initializer=init) as p:
            results = p.map(work, jobsl)
    else:
        init()
        results = [work(j) for j in jobsl]
    dt = time.time() - t0

    asked = sum(r[0][0] for r in results)
    top1 = sum(r[0][1] for r in results)
    top3 = sum(r[0][2] for r in results)
    fr = sum(r[0][3] for r in results)
    fw = sum(r[0][4] for r in results)
    print("pool=%s  asked %d  top1 %d (%.1f%%)  top3 %d (%.1f%%)  %.0fs"
          % (pool, asked, top1, 100.0 * top1 / asked,
             top3, 100.0 * top3 / asked, dt))
    if pool != "1":
        print("  foreign article gave the RIGHT top answer: %d (%.1f%%)" %
              (fr, 100.0 * fr / asked))
        print("  foreign article STOLE the top spot, wrong: %d (%.1f%%)" %
              (fw, 100.0 * fw / asked))

    if pool == "1":
        arts = [pa for r in results for pa in r[1] if pa[1]]
        accs = sorted(100.0 * t / a for _, a, t in arts)
        print("  per-article top1 spread over %d articles:" % len(accs))
        print("    min %.1f   q1 %.1f   median %.1f   q3 %.1f   max %.1f"
              % (accs[0], accs[len(accs) // 4], accs[len(accs) // 2],
                 accs[3 * len(accs) // 4], accs[-1]))
        rng = random.Random(3)
        diffs = []
        for _ in range(20):
            sh = arts[:]
            rng.shuffle(sh)
            h = len(sh) // 2
            a1 = 100.0 * sum(t for _, _, t in sh[:h]) / sum(a for _, a, _ in sh[:h])
            a2 = 100.0 * sum(t for _, _, t in sh[h:]) / sum(a for _, a, _ in sh[h:])
            diffs.append(abs(a1 - a2))
        print("    random half vs half, 20 draws: differ %.1f to %.1f "
              "points (mean %.1f)" % (min(diffs), max(diffs),
                                      sum(diffs) / len(diffs)))


if __name__ == "__main__":
    main()
