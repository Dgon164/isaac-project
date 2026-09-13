#!/usr/bin/env python3
"""misses.py -- what is he getting wrong, and how wrong is it?

    python walk/misses.py 5000              counts + a few of each kind
    python walk/misses.py 5000 -show 10     ten examples of each kind

Every question lands in exactly one bin, in the order tested:

    RIGHT          the key is in his top answer
    CLOSE          the key is in his second or third
    LOST TIE       the right sentence shares as many question words as
                   the winner and lost the tie-break
    FEWER WORDS    the right sentence is in the field but shares fewer
                   question words than the winner (the paraphrase gap)
    SHARES NOTHING the right sentence was reached but shares no word
                   with the question or its thesaurus pull
    NO PATH        the right sentence is in the store and the walk
                   never reached it
    NOT STORED     no sentence in the store contains the key at all --
                   the linker lost it, not the walk
    NOTHING        no question word is in the store

Also: which questions the rarity tie-break fixed and which it broke,
against the old order (question words, bag words, then name).
"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "engine"))
from core import Store
from linker import link, terms
from mind import score_all, load_dictionary, SYN

SQUAD = os.environ.get(
    "ISAAC_SQUAD",
    r"C:\Users\jtwee\Downloads\New folder (3)\intellon\train-v2.0.json")
BINS = ("RIGHT", "CLOSE", "LOST TIE", "FEWER WORDS", "SHARES NOTHING",
        "NO PATH", "NOT STORED", "NOTHING")


def old_order(cands):
    """yesterday's ranking: (own words, bag words) then name descending."""
    return sorted(cands, key=lambda c: ((c[0][0], c[0][-1]), c[1]),
                  reverse=True)


def work(art):
    store = Store()
    made = sum(link(p["context"], store, tag=art["title"])
               for p in art["paragraphs"])
    held = sum(1 for i in store.items.values() if i.kind == "sentence")
    sents = [(n, str(i.content).lower()) for n, i in store.items.items()
             if i.kind == "sentence"]
    bins = dict.fromkeys(BINS, 0)
    fixed = broke = 0
    ex = {b: [] for b in BINS}
    for p in art["paragraphs"]:
        for qa in p["qas"]:
            if qa.get("is_impossible"):
                continue
            q = qa["question"]
            key = qa["answers"][0]["text"].lower()
            seeds, reached, cands = score_all(store, q)
            targets = [n for n, c in sents if key in c]
            rank = {n: i for i, (_, n) in enumerate(cands)}
            best = min((rank[t] for t in targets if t in rank), default=None)
            own = set(terms(q))
            if cands:
                oldtop = old_order(cands)[0][1]
                newtop = cands[0][1]
                o = key in str(store.get(oldtop).content).lower()
                n_ = key in str(store.get(newtop).content).lower()
                fixed += int(n_ and not o)
                broke += int(o and not n_)

            if not seeds:
                b = "NOTHING"
            elif best == 0:
                b = "RIGHT"
            elif best is not None and best < 3:
                b = "CLOSE"
            elif best is not None:
                t = cands[best]
                b = "LOST TIE" if t[0][0] == cands[0][0][0] else "FEWER WORDS"
            elif any(t in reached for t in targets):
                b = "SHARES NOTHING"
            elif targets:
                b = "NO PATH"
            else:
                b = "NOT STORED"
            bins[b] += 1
            if len(ex[b]) < 12:
                tgt = cands[best][1] if best is not None else \
                    (targets[0] if targets else None)
                tr = set(store.get(tgt).refs) if tgt else set()
                win = cands[0][1] if cands else None
                wr = set(store.get(win).refs) if win else set()
                ex[b].append({
                    "q": q, "key": key,
                    "his": str(store.get(win).content)[:110] if win else "-",
                    "right": str(store.get(tgt).content)[:110] if tgt else "-",
                    "q_words": sorted(own),
                    "in_right": sorted(own & tr),
                    "in_his": sorted(own & wr),
                    "his_score": cands[0][0] if cands else None,
                    "right_score": cands[best][0] if best is not None else None,
                })
    return bins, fixed, broke, ex, made, held


def main():
    want = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    show = int(sys.argv[sys.argv.index("-show") + 1]) \
        if "-show" in sys.argv else 3
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
        with Pool(jobs, initializer=load_dictionary) as pool:
            res = pool.map(work, arts)
    else:
        load_dictionary()
        res = [work(a) for a in arts]

    bins = dict.fromkeys(BINS, 0)
    for r in res:
        for k, v in r[0].items():
            bins[k] += v
    asked = sum(bins.values())
    fixed, broke = sum(r[1] for r in res), sum(r[2] for r in res)
    made, held = sum(r[4] for r in res), sum(r[5] for r in res)
    print("%d questions, %d articles, %.0fs" % (asked, len(arts),
                                                time.time() - t0))
    print("  sentences linked %d, held %d (%d overwritten by a name clash)"
          % (made, held, made - held))
    for b in BINS:
        print("  %-15s %6d  (%5.1f%%)" % (b, bins[b], 100.0 * bins[b] / asked))
    print("  tie-break vs the old order: fixed %d, broke %d, net %+d"
          % (fixed, broke, fixed - broke))

    for b in BINS:
        if b == "RIGHT":
            continue
        exs = [e for r in res for e in r[3][b]][:show]
        if not exs:
            continue
        print("\n==== %s" % b)
        for e in exs:
            print("  Q: %s" % e["q"])
            print("     key: %s" % e["key"])
            print("     his:   %s  %s" % (e["his"], e["his_score"] or ""))
            print("     right: %s  %s" % (e["right"], e["right_score"] or ""))
            miss = [w for w in e["q_words"] if w not in e["in_right"]]
            print("     question words in right: %s | not in right: %s"
                  % (" ".join(e["in_right"]) or "-", " ".join(miss) or "-"))
            if b in ("LOST TIE", "FEWER WORDS"):
                print("     question words in his:   %s"
                      % (" ".join(e["in_his"]) or "-"))


if __name__ == "__main__":
    main()
