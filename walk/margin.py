#!/usr/bin/env python3
"""margin.py -- when the top answer beats the second, is it right?

    python walk/margin.py 5000

Every question is scored as usual; then the gap between the first and
second candidate is recorded with whether the first was correct. If
the gap predicts correctness, two things follow: he can refuse when
the field is tied, and a run can bank only the answers it won
cleanly. If it does not predict, the score is flat and neither is
available.
"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "engine"))
from core import Store
from linker import link
from mind import score_all, load_dictionary

SQUAD = os.environ.get(
    "ISAAC_SQUAD",
    r"C:\Users\jtwee\Downloads\New folder (3)\intellon\train-v2.0.json")


def gap(cands):
    """how far the winner is clear of the runner-up: own words first,
    then bag words. no second candidate means uncontested."""
    if len(cands) < 2:
        return "uncontested"
    a, b = cands[0][0], cands[1][0]        # (own words, ..., bag words)
    if a[0] > b[0]:
        return "own +%d" % min(a[0] - b[0], 3)
    if a[1:] > b[1:]:
        return "broken by tie-break"
    return "tied"


def work(art):
    store = Store()
    for p in art["paragraphs"]:
        link(p["context"], store, tag=art["title"])
    out = {}
    for p in art["paragraphs"]:
        for qa in p["qas"]:
            if qa.get("is_impossible"):
                continue
            key = qa["answers"][0]["text"].lower()
            _, _, cands = score_all(store, qa["question"])
            if not cands:
                bucket, right = "nothing", False
            else:
                bucket = gap(cands)
                right = key in str(store.get(cands[0][1]).content).lower()
            a, b = out.get(bucket, (0, 0))
            out[bucket] = (a + 1, b + int(right))
    return out


def main():
    want = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    jobs = int(sys.argv[sys.argv.index("-jobs") + 1]) \
        if "-jobs" in sys.argv else 1
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
    if jobs > 1:
        from multiprocessing import Pool
        with Pool(jobs, initializer=load_dictionary) as pool:
            res = pool.map(work, arts)
    else:
        res = [work(a) for a in arts]
    tot = {}
    for r in res:
        for k, (a, b) in r.items():
            x, y = tot.get(k, (0, 0))
            tot[k] = (x + a, y + b)

    asked = sum(a for a, _ in tot.values())
    right = sum(b for _, b in tot.values())
    print("%d questions over %d articles, %.0fs -- top1 %.1f%% overall"
          % (asked, len(arts), time.time() - t0, 100.0 * right / asked))
    order = ["own +3", "own +2", "own +1", "broken by tie-break",
             "uncontested", "tied", "nothing"]
    for k in order:
        if k not in tot:
            continue
        a, b = tot[k]
        print("  %-12s %6d questions (%4.1f%%)   right %5.1f%%"
              % (k, a, 100.0 * a / asked, 100.0 * b / a))
    print("  answer only when the winner is clear (not tied, not nothing):")
    a = sum(v[0] for k, v in tot.items() if k not in ("tied", "nothing"))
    b = sum(v[1] for k, v in tot.items() if k not in ("tied", "nothing"))
    print("    covers %.1f%% of questions, right %.1f%% of the time"
          % (100.0 * a / asked, 100.0 * b / a))


if __name__ == "__main__":
    main()
