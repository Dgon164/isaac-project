#!/usr/bin/env python3
"""loops.py -- not blind: wrong answers are filed, and he comes back to them.

    python walk/loops.py 10000 -jobs 24              8 passes over 10k questions
    python walk/loops.py 999999 -jobs 24 -loops 12   the other half, 12 passes

Owner: "add a wrong answer to the system and have him do it again later,
but at a random point. see how many loops it takes and how close he can
get to 100."

Each pass asks every question of an article in a fresh random order.
A wrong answer is corrected the way a "no:" correction does it -- the
wrong pick is refused for that question, the right sentence takes the
question words it lacked, the two are compared for his attention
record, and the question is re-asked under every setting for his
selector. The store keeps all of it. The next pass asks the same
questions again, shuffled, so the retry lands at a random point among
the others, with everything he learned since.

Counted per pass: right, newly right, still wrong, and REGRESSIONS --
right last pass, wrong now -- because a correction changes the store
and can break another answer. Held-out articles only.
"""
import json
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "engine"))
from core import Store
from linker import link
import mind
from mind import ask_selected, grade, retry_all, load_tools

SQUAD = os.environ.get(
    "ISAAC_SQUAD",
    r"C:\Users\jtwee\Downloads\New folder (3)\intellon\train-v2.0.json")
LOOPS = 8


def init(loops):
    load_tools()
    global LOOPS
    LOOPS = loops


def one(art):
    try:
        return one_(art)
    except Exception:
        import traceback
        return ("ERR", art["title"], traceback.format_exc())


def one_(art):
    store = Store()
    for p in art["paragraphs"]:
        link(p["context"], store, tag=art["title"])
    qs = [(qa["question"], qa["answers"][0]["text"])
          for p in art["paragraphs"] for qa in p["qas"] if not qa.get("is_impossible")]
    rng = random.Random(len(qs) * 7919 + len(store.items))
    was_right = {}
    out = []
    for k in range(LOOPS):
        order = list(range(len(qs)))
        rng.shuffle(order)                        # the retry lands at a random point
        right = new = regress = corrected = 0
        t0 = time.perf_counter()
        for i in order:
            q, key = qs[i]
            seeds, reached, cands, _ = ask_selected(store, q)
            ok = bool(cands) and key.lower() in str(store.get(cands[0][1]).content).lower()
            if ok:
                right += 1
                new += not was_right.get(i, False)
                grade(store, q, cands, reached, key)   # right is filed too
            else:
                regress += was_right.get(i, False)
                corrected += 1
                retry_all(store, q, key)          # every setting, for his selector
                grade(store, q, cands, reached, key)   # the correction, filed
            was_right[i] = ok
        out.append((len(qs), right, new, regress, corrected, time.perf_counter() - t0))
        if right == len(qs) and k >= 2:
            break
    # what kind of wrong survives: his own diagnosis of what is still wrong
    bins, shown = {}, []
    for i, ok in was_right.items():
        if ok:
            continue
        q, key = qs[i]
        seeds, reached, cands, _ = ask_selected(store, q)
        d = mind.diagnose(store, q, cands, reached, key)
        bins[d["verdict"]] = bins.get(d["verdict"], 0) + 1
        if len(shown) < 1:
            shown.append((q, key, d["verdict"],
                          str(store.get(cands[0][1]).content)[:80] if cands else "-",
                          str(store.get(d["right"]).content)[:80] if d["right"] else "-"))
    return out, bins, shown


def main():
    want = int(sys.argv[1]) if len(sys.argv) > 1 else 10000
    jobs = int(sys.argv[sys.argv.index("-jobs") + 1]) if "-jobs" in sys.argv else 1
    loops = int(sys.argv[sys.argv.index("-loops") + 1]) if "-loops" in sys.argv else LOOPS
    data = json.load(open(SQUAD, encoding="utf-8"))["data"]
    half = len(data) // 2
    arts, n = [], 0
    for art in data[half:]:                     # held-out only
        if n >= want:
            break
        n += sum(1 for p in art["paragraphs"] for qa in p["qas"]
                 if not qa.get("is_impossible"))
        arts.append(art)
    print("prediction, stated first: pass 1 near 63.5%%; pass 2 into the "
          "nineties; then a slow climb that stops short of 100 because "
          "corrections break some other answers.\n")
    t0 = time.perf_counter()
    if jobs > 1:
        from multiprocessing import Pool
        with Pool(jobs, initializer=init, initargs=(loops,)) as pool:
            res = pool.map(one, arts)
    else:
        init(loops)
        res = [one(a) for a in arts]
    print("%d questions in %d held-out articles, %d passes  (%.0fs)\n"
          % (n, len(arts), loops, time.perf_counter() - t0))
    errs = [r for r in res if r is None or r[0] == "ERR"]
    for e in errs[:3]:
        print("WORKER ERROR:", e if e is None else e[1])
        print("" if e is None else e[2][-600:])
    res = [r for r in res if r is not None and r[0] != "ERR"]
    curves = [r[0] for r in res]
    print("  pass   right of all %d      newly right   regressions   corrections filed" % n)
    for k in range(loops):
        rows = [c[k] if k < len(c) else c[-1] for c in curves]   # a finished
        right = sum(r[1] for r in rows)                            # article stays
        live = [c[k] for c in curves if k < len(c)]
        if not live:
            break
        print("  %4d  %6d  %5.1f%%          %11d   %11d   %17d"
              % (k + 1, right, 100.0 * right / n, sum(r[2] for r in live),
                 sum(r[3] for r in live), sum(r[4] for r in live)))
    last = [c[-1] for c in curves]
    right = sum(r[1] for r in last)
    print("\n  after the last pass: %d / %d right (%.1f%%); %d still wrong"
          % (right, n, 100.0 * right / n, n - right))
    bins = {}
    for _, b, _ in res:
        for k, v in b.items():
            bins[k] = bins.get(k, 0) + v
    print("  what kind of wrong survives %d corrections:" % loops)
    for k, v in sorted(bins.items(), key=lambda kv: -kv[1]):
        print("    %-16s %5d" % (k, v))
    print("\n  a few that survive:")
    for _, _, shown in res[:6]:
        for q, key, verdict, his, right in shown:
            print("    [%s] %s\n        key: %s\n        his: %s\n        right: %s"
                  % (verdict, q, key, his, right))


if __name__ == "__main__":
    main()
