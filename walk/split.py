#!/usr/bin/env python3
"""split.py -- his mined pairs sorted into what they are: translations,
learned connections, refuted, unplaced.

    python walk/split.py -jobs 24

Owner: "thesaurus is close approximal translation, relational connections
are something else." The crawler's records say, per pair, which reference
spoke. A pair a dictionary, wordnet or the stem confirms is a TRANSLATION
and stays in his thesaurus. A pair only the held-out evidence confirms --
it selected the right sentence, but no reference calls it a synonym --
is a RELATION: a learned connection, a tool of its own with its own
switch. A refuted pair goes. A pair no reference speaks to is set aside.

Before writing, each set is looked at once on the held-out half.
"""
import json
import os
import shutil
import sys
import time
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "engine"))
import mind
from mind import score_all, load_tools, use
import tools as T

TOOLS = os.path.join(HERE, "tools.json")
SELF = os.path.join(HERE, "self.json")
VARIANT = {}


def init(syn, rel):
    load_tools()
    use("thes+kinds-second")
    mind.SYN.clear(); mind.SYN.update((k, set(v)) for k, v in syn.items())
    mind.REL.clear(); mind.REL.update((k, set(v)) for k, v in rel.items())
    mind.TOOLSET["rel"] = bool(rel)


def bench_one(art):
    store = T.fill(art)
    asked = top1 = 0
    for q, key in T.questions(art):
        _, _, cands = score_all(store, q)
        asked += 1
        top1 += bool(cands) and key.lower() in str(store.get(cands[0][1]).content).lower()
    return asked, top1


def bench(arts, jobs, syn, rel):
    from multiprocessing import Pool
    with Pool(jobs, initializer=init, initargs=(syn, rel)) as pool:
        res = pool.map(bench_one, arts)
    return sum(r[0] for r in res), sum(r[1] for r in res)


def main():
    jobs = int(sys.argv[sys.argv.index("-jobs") + 1]) if "-jobs" in sys.argv else 1
    records = [r for r in json.load(open(SELF, encoding="utf-8")) if r["kind"] == "thesaurus pair"]
    tools = json.load(open(TOOLS, encoding="utf-8"))
    trans, rel, gone, aside = {}, {}, [], []
    why = Counter()
    for r in records:
        q, s = r["name"].split(">", 1)
        reason = r["reason"]
        if r["truth"] < 0:
            gone.append((q, s)); why["refuted"] += 1
        elif any(k in reason for k in ("morphology", "wordnet: synonyms", "dictionary")):
            trans.setdefault(q, []).append(s); why["translation"] += 1
        elif "evidence" in reason and r["truth"] > 0:
            rel.setdefault(q, []).append(s); why["relation"] += 1
        else:
            aside.append((q, s)); why["unplaced"] += 1
    print("his 3000 mined pairs, sorted: %s" % ", ".join("%s %d" % kv for kv in why.most_common()))
    print("  translations, e.g.: %s" % ", ".join("%s>%s" % (q, s) for q, ss in list(trans.items())[:6] for s in ss[:1]))
    print("  relations,    e.g.: %s" % ", ".join("%s>%s" % (q, s) for q, ss in list(rel.items())[:6] for s in ss[:1]))
    print("  set aside,    e.g.: %s" % ", ".join("%s>%s" % p for p in aside[:6]))

    data = json.load(open(T.SQUAD, encoding="utf-8"))["data"]
    _, exam = T.split(data, 999999)
    print("\nprediction, stated first: translations alone lose a little against the "
          "mixed list; relations alone are worth about as much as the thesaurus "
          "was over wordnet; both together match today.\n")
    print("one look each, the held-out half, thes+kinds-second:")
    for label, syn_v, rel_v in (("all 3000 as thesaurus (today)", tools["thesaurus"], {}),
                                ("translations only", trans, {}),
                                ("relations only", {}, rel),
                                ("translations + relations", trans, rel),
                                ("none", {}, {})):
        t0 = time.perf_counter()
        asked, right = bench(exam, jobs, syn_v, rel_v)
        print("  %-32s %5d / %d  (%.1f%%)  %.0fs" % (label, right, asked, 100.0 * right / asked,
                                                    time.perf_counter() - t0))
    shutil.copy2(TOOLS, TOOLS + ".before-split")
    tools["thesaurus"] = trans
    tools["relations"] = rel
    tools["unplaced"] = ["%s>%s" % p for p in aside]
    json.dump(tools, open(TOOLS, "w", encoding="utf-8"), indent=1)
    print("\nwritten: thesaurus = %d translations, relations = %d connections, %d set aside, %d dropped "
          "(tools.json; the old file is tools.json.before-split)"
          % (sum(len(v) for v in trans.values()), sum(len(v) for v in rel.values()), len(aside), len(gone)))


if __name__ == "__main__":
    main()
