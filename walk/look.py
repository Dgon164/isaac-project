#!/usr/bin/env python3
"""look.py -- when the critic objects: keep, switch blindly, or look deeper?

    python walk/look.py 10000 -jobs 24        held-out questions, 24 workers

Owner: "the wrong thing shouldn't be a blind change. it's a deeper look
and investigation." On the other half, for every question where his
critic objects to his top answer, three things are compared:

    KEEP     his answer stands
    SWITCH   the blind change: take the runner-up
    LOOK     mind.investigate(): which question words the answer failed,
             translations for them from what he has read, which
             candidates satisfy them, agreement under every setting;
             then a decision, or "don't know" with the reasons

Prediction, stated first: LOOK beats KEEP beats SWITCH by a little, and
most of the "don't know" refusals land on answers that were wrong.
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "engine"))
from core import Store
from linker import link
import mind
from mind import score_all, load_tools, use, critic_score, investigate

SQUAD = os.environ.get(
    "ISAAC_SQUAD",
    r"C:\Users\jtwee\Downloads\New folder (3)\intellon\train-v2.0.json")
CUT = 2.0


def init():
    load_tools()
    use("thes+kinds-second")
    mind.load_critic()


def one(art):
    store = Store()
    for p in art["paragraphs"]:
        link(p["context"], store, tag=art["title"])
    c = dict(asked=0, objected=0, keep=0, switch=0, look=0, refused=0,
             refused_wrong=0, changed=0, changed_right=0, secs=0.0, shown=[])
    for p in art["paragraphs"]:
        for qa in p["qas"]:
            if qa.get("is_impossible"):
                continue
            q, key = qa["question"], qa["answers"][0]["text"].lower()
            seeds, reached, cands = score_all(store, q)
            c["asked"] += 1
            if len(cands) < 2:
                continue
            top = cands[0][1]
            if critic_score(store, q, top) <= CUT:
                continue
            c["objected"] += 1
            right = lambda n: key in str(store.get(n).content).lower()
            c["keep"] += right(top)
            c["switch"] += right(cands[1][1])
            t0 = time.perf_counter()
            chosen, verdict, lines = investigate(store, q, cands, reached)
            c["secs"] += time.perf_counter() - t0
            if verdict == "don't know":
                c["refused"] += 1
                c["refused_wrong"] += not right(top)
                c["look"] += right(top)          # he keeps it, but says unsure
            else:
                c["look"] += right(chosen)
                if chosen != top:
                    c["changed"] += 1
                    c["changed_right"] += right(chosen)
            if len(c["shown"]) < 2 and chosen != top:
                c["shown"].append((q, key, lines, right(chosen)))
    return c


def main():
    want = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    jobs = int(sys.argv[sys.argv.index("-jobs") + 1]) if "-jobs" in sys.argv else 1
    data = json.load(open(SQUAD, encoding="utf-8"))["data"]
    half = len(data) // 2
    arts, n = [], 0
    for art in data[half:]:                     # the other half only
        if n >= want:
            break
        n += sum(1 for p in art["paragraphs"] for qa in p["qas"]
                 if not qa.get("is_impossible"))
        arts.append(art)
    t0 = time.perf_counter()
    if jobs > 1:
        from multiprocessing import Pool
        with Pool(jobs, initializer=init) as pool:
            res = pool.map(one, arts)
    else:
        init()
        res = [one(a) for a in arts]
    tot = {k: sum(r[k] for r in res) for k in res[0] if k != "shown"}
    print("held-out: %d questions in %d articles; the critic objected on %d (%.1f%%)  %.0fs"
          % (tot["asked"], len(arts), tot["objected"],
             100.0 * tot["objected"] / max(tot["asked"], 1), time.perf_counter() - t0))
    o = max(tot["objected"], 1)
    print("  KEEP    right %5d (%.1f%%)" % (tot["keep"], 100.0 * tot["keep"] / o))
    print("  SWITCH  right %5d (%.1f%%)   the blind change" % (tot["switch"], 100.0 * tot["switch"] / o))
    print("  LOOK    right %5d (%.1f%%)   changed his answer on %d, right after the change %d;"
          " said don't know on %d, of which the answer was wrong %d"
          % (tot["look"], 100.0 * tot["look"] / o, tot["changed"], tot["changed_right"],
             tot["refused"], tot["refused_wrong"]))
    print("  a look costs %.1fms on average" % (1000.0 * tot["secs"] / o))
    shown = [s for r in res for s in r["shown"]][:4]
    print("\nfour of his looks that changed the answer (v right / x wrong):")
    for q, key, lines, ok in shown:
        print("  %s %s   [key: %s]" % ("v" if ok else "x", q, key))
        for l in lines:
            print("      " + l)


if __name__ == "__main__":
    main()
