#!/usr/bin/env python3
"""curve.py -- does asking questions make the next question easier?

    python walk/curve.py 5000            first 5000 questions
    python walk/curve.py 5000 -jobs 8    articles across 8 processes

Per article the questions are cut in half. The second half is the
exam, and neither arm ever processes it:

    COLD   fill the text, ask the exam
    WARM   fill the text, run the first half through the loop
           (every ask banks residue), then ask the same exam
    CLEAN  the same, but only wins clear of the runner-up are banked
    TAUGHT fill the text, ask the first half and GRADE every answer
           against its key (the feedback path: verdict filed, wrong
           pick refused, right item learns the words it lacked), then
           ask the same exam. RE-ASK is the first half asked again
           after grading -- did the feedback land at all.

Same questions, same scoring as bed.py. The only difference is what
the store was asked before the exam and what it kept. If residue is
worth having, WARM or CLEAN beats COLD. If it is noise, they lose,
and that is the answer too.
"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "engine"))
from core import Store
from linker import link
from mind import score_all, clean_win, residue, grade, load_dictionary

SQUAD = os.environ.get(
    "ISAAC_SQUAD",
    r"C:\Users\jtwee\Downloads\New folder (3)\intellon\train-v2.0.json")


def init():
    load_dictionary()


def score(store, exam):
    t1 = t3 = 0
    first = []
    for q, key in exam:
        _, _, cands = score_all(store, q)
        got = [str(store.get(n).content).lower() for _, n in cands[:3]]
        first.append(got[0] if got else "")
        if got and key in got[0]:
            t1 += 1; t3 += 1
        elif any(key in g for g in got):
            t3 += 1
    return t1, t3, first


def warm_up(art, warmup, gated):
    """fill the text, run the warm-up questions, keep what this arm
    keeps. gated: only a clean win is banked."""
    store = Store()
    for p in art["paragraphs"]:
        link(p["context"], store, tag=art["title"])
    held = 0
    for q, _ in warmup:
        seeds, _, cands = score_all(store, q)
        if not seeds:
            continue
        if gated and not clean_win(cands):
            held += 1
            continue
        residue(store, q, seeds, [(n, store.get(n)) for _, n in cands[:3]])
    return store, held


def taught(art, warmup):
    """fill the text, ask the warm-up questions, grade each with its
    key. returns the store and how many were wrong before grading."""
    store = Store()
    for p in art["paragraphs"]:
        link(p["context"], store, tag=art["title"])
    verdicts = {}
    for q, key in warmup:
        seeds, reached, cands = score_all(store, q)
        d = grade(store, q, cands, reached, key)
        verdicts[d["verdict"]] = verdicts.get(d["verdict"], 0) + 1
    return store, verdicts


def work(art):
    qas = [(qa["question"], qa["answers"][0]["text"].lower())
           for p in art["paragraphs"] for qa in p["qas"]
           if not qa.get("is_impossible")]
    if len(qas) < 4:
        return (0,) * 15 + ({},)
    half = len(qas) // 2
    warmup, exam = qas[:half], qas[half:]

    cold = Store()
    for p in art["paragraphs"]:
        link(p["context"], cold, tag=art["title"])
    c1, c3, cfirst = score(cold, exam)

    warm, _ = warm_up(art, warmup, False)
    w1, w3, wfirst = score(warm, exam)

    clean, held = warm_up(art, warmup, True)
    g1, g3, gfirst = score(clean, exam)

    tstore, verdicts = taught(art, warmup)
    t1, t3, tfirst = score(tstore, exam)
    r1, _, _ = score(tstore, warmup)          # the graded half, re-asked

    moved = sum(1 for a, b in zip(cfirst, wfirst) if a != b)
    gmoved = sum(1 for a, b in zip(cfirst, gfirst) if a != b)
    tmoved = sum(1 for a, b in zip(cfirst, tfirst) if a != b)
    return (len(exam), c1, c3, w1, w3, g1, g3, moved, gmoved, held,
            t1, t3, tmoved, r1, len(warmup), verdicts)


def main():
    want = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
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

    t0 = time.time()
    if jobs > 1:
        from multiprocessing import Pool
        with Pool(jobs, initializer=init) as pool:
            res = pool.map(work, arts)
    else:
        init()
        res = [work(a) for a in arts]
    dt = time.time() - t0

    asked = sum(r[0] for r in res)
    c1, c3 = sum(r[1] for r in res), sum(r[2] for r in res)
    w1, w3 = sum(r[3] for r in res), sum(r[4] for r in res)
    g1, g3 = sum(r[5] for r in res), sum(r[6] for r in res)
    moved, gmoved = sum(r[7] for r in res), sum(r[8] for r in res)
    held = sum(r[9] for r in res)
    t1, t3 = sum(r[10] for r in res), sum(r[11] for r in res)
    tmoved, r1 = sum(r[12] for r in res), sum(r[13] for r in res)
    warmed = sum(r[14] for r in res)
    verdicts = {}
    for r in res:
        for k, v in r[15].items():
            verdicts[k] = verdicts.get(k, 0) + v
    print("%d articles, %d exam questions, %.0fs" % (len(arts), asked, dt))
    for nm, a, b in (("COLD", c1, c3), ("WARM", w1, w3), ("CLEAN", g1, g3),
                     ("TAUGHT", t1, t3)):
        print("  %-6s top1 %5d (%5.1f%%)   top3 %5d (%5.1f%%)"
              % (nm, a, 100.0 * a / asked, b, 100.0 * b / asked))
    print("  WARM   moved the top answer on %d exam questions (%.1f%%), "
          "net top1 %+d" % (moved, 100.0 * moved / asked, w1 - c1))
    print("  CLEAN  moved the top answer on %d exam questions (%.1f%%), "
          "net top1 %+d" % (gmoved, 100.0 * gmoved / asked, g1 - c1))
    print("  TAUGHT moved the top answer on %d exam questions (%.1f%%), "
          "net top1 %+d" % (tmoved, 100.0 * tmoved / asked, t1 - c1))
    print("  CLEAN held back %d warm-up runs as too close to call" % held)
    print("  RE-ASK the graded half: %d of %d right (%.1f%%) -- graded as: %s"
          % (r1, warmed, 100.0 * r1 / warmed,
             ", ".join("%s %d" % kv for kv in sorted(verdicts.items()))))


if __name__ == "__main__":
    main()
