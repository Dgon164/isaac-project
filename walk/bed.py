#!/usr/bin/env python3
"""bed.py -- the curriculum test bed. squad in, the walk answers, score out.

    python walk/bed.py 500            first 500 questions
    python walk/bed.py 500 -misses    also print each miss with the key

Jeopardy-style: he gets the wikipedia paragraphs of an article, then
the questions. The key says which detail was the answer, so every miss
is ablation material: question, his answer, the right answer, side by
side. No model, no training step -- the same walk mind.py uses.
"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "engine"))
from core import Store
from linker import link
from mind import ask

SQUAD = r"C:\Users\jtwee\Downloads\New folder (3)\intellon\train-v2.0.json"

want = int(sys.argv[1]) if len(sys.argv) > 1 else 500
show_misses = "-misses" in sys.argv

data = json.load(open(SQUAD, encoding="utf-8"))["data"]
asked = top1 = top3 = noseed = 0
misses = []
t0 = time.time()

for art in data:
    if asked >= want:
        break
    store = Store()
    for para in art["paragraphs"]:
        link(para["context"], store, tag=art["title"])
    for para in art["paragraphs"]:
        for qa in para["qas"]:
            if asked >= want:
                break
            if qa.get("is_impossible"):
                continue
            key = qa["answers"][0]["text"].lower()
            seeds, reached, answers = ask(store, qa["question"])
            asked += 1
            if not answers:
                noseed += 1
                misses.append((art["title"], qa["question"], key, "(nothing)"))
                continue
            got = [str(it.content).lower() for _, it in answers]
            if key in got[0]:
                top1 += 1
                top3 += 1
            elif any(key in g for g in got):
                top3 += 1
            else:
                misses.append((art["title"], qa["question"], key, got[0][:90]))

dt = time.time() - t0
print("asked %d   top1 %d (%.1f%%)   top3 %d (%.1f%%)   nothing %d   "
      "%.1fs (%.0f q/s)" % (asked, top1, 100.0 * top1 / asked,
                            top3, 100.0 * top3 / asked, noseed, dt,
                            asked / dt if dt else 0))
if show_misses:
    for t, q, key, got in misses[:25]:
        print("MISS [%s] %s" % (t, q))
        print("   key: %s" % key)
        print("   his: %s" % got)
