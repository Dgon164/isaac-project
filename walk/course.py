#!/usr/bin/env python3
"""course.py -- the curriculum experiment. five arms, same questions.

    python walk/course.py 2000            document order
    python walk/course.py 2000 -shuffle   randomized question order

Per article (questions unlock only after its text is filled):
    PRE    ask before filling      -- can he answer what he hasn't learned
    TEST   fill, then ask          -- the standard test; every ask loops
                                      (residue goes back into the store)
    POST   ask again               -- did the loop alone change anything
    TEACH  the keys are given      -- each answer becomes an item
    FINAL  ask again               -- does giving the answers matter
"""
import json, os, random, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "engine"))
from core import Store, Item
from linker import link, terms
from mind import ask, residue, load_dictionary

SQUAD = r"C:\Users\jtwee\Downloads\New folder (3)\intellon\train-v2.0.json"
want = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
shuffle = "-shuffle" in sys.argv
rng = random.Random(7)

print("dictionary: %d linked words" % load_dictionary())
data = json.load(open(SQUAD, encoding="utf-8"))["data"]

ARMS = ("PRE", "TEST", "POST", "FINAL")
t1 = dict.fromkeys(ARMS, 0)
t3 = dict.fromkeys(ARMS, 0)
asked = 0
t0 = time.time()

def attempt(store, arm, qas, loop=False):
    for q, key in qas:
        seeds, _, answers = ask(store, q)
        got = [str(it.content).lower() for _, it in answers]
        if got and key in got[0]:
            t1[arm] += 1; t3[arm] += 1
        elif any(key in g for g in got):
            t3[arm] += 1
        if loop and seeds:
            residue(store, q, seeds, answers)

for art in data:
    if asked >= want:
        break
    qas = [(qa["question"], qa["answers"][0]["text"].lower())
           for p in art["paragraphs"] for qa in p["qas"]
           if not qa.get("is_impossible")]
    qas = qas[:want - asked]
    if shuffle:
        rng.shuffle(qas)
    asked += len(qas)

    store = Store()
    attempt(store, "PRE", qas)                      # nothing filled yet
    for p in art["paragraphs"]:
        link(p["context"], store, tag=art["title"])
    attempt(store, "TEST", qas, loop=True)          # the loop runs
    attempt(store, "POST", qas, loop=True)
    for i, (q, key) in enumerate(qas):              # the keys are given
        ts = terms(key) + [t for t in terms(q) if t not in terms(key)]
        store.put(Item("key_%03d" % i, "sentence", content=key,
                       tag="answer", refs=ts))
        for t in ts:
            it = store.get(t)
            if it is not None and "key_%03d" % i not in it.refs:
                it.refs = tuple(it.refs) + ("key_%03d" % i,)
    attempt(store, "FINAL", qas)

print("%d questions, %s order, %.0fs" %
      (asked, "shuffled" if shuffle else "document", time.time() - t0))
for a in ARMS:
    note = {"PRE": "before the material", "TEST": "standard",
            "POST": "after the loop", "FINAL": "answers given"}[a]
    print("  %-6s top1 %4d (%5.1f%%)   top3 %4d (%5.1f%%)   %s"
          % (a, t1[a], 100.0 * t1[a] / asked,
             t3[a], 100.0 * t3[a] / asked, note))
