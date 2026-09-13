#!/usr/bin/env python3
"""tools.py -- the tools he builds himself, from his own record.

    python walk/tools.py learn 999999      grade the first half of the
                                            articles, build the tools,
                                            write walk/tools.json
    python walk/tools.py court 999999 -jobs 12
                                            the other half, never learned
                                            from: wordnet vs his tools

No installed dictionary. Everything here is mined from graded runs --
his pick, the right item, the question -- and nothing else.

THESAURUS   a question word the article never used, paired with the
            words of the right sentence; kept when the two keep each
            other's company across articles (begin->began, honor->
            honour, convinced->persuaded).
DICTIONARY  built from reading, per store: the words of the text that
            keep each other's company across its sentences. No feedback
            needed; it comes out of the material he was given.
KINDS       the question's kind word (who / when / where / how many)
            against what the right sentence carried (a year, a number,
            a name, a percent) -- how much more often than the sentences
            he picked wrongly. A reference table for what kind of answer
            counts.
"""
import json, math, os, re, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "engine"))
from core import Store
from linker import link, terms
import mind
from mind import (score_all, diagnose, kind, feats, FEATS, read_dictionary,
                  TOOLSETS, use, select, context_at, load_tools)

SQUAD = os.environ.get(
    "ISAAC_SQUAD",
    r"C:\Users\jtwee\Downloads\New folder (3)\intellon\train-v2.0.json")
TOOLS = os.path.join(HERE, "tools.json")
def split(data, want):
    arts, n = [], 0
    for art in data:
        if n >= want:
            break
        n += sum(1 for p in art["paragraphs"] for qa in p["qas"]
                 if not qa.get("is_impossible"))
        arts.append(art)
    half = len(arts) // 2
    return arts[:half], arts[half:]


def fill(art):
    store = Store()
    for p in art["paragraphs"]:
        link(p["context"], store, tag=art["title"])
    return store


def questions(art):
    return [(qa["question"], qa["answers"][0]["text"])
            for p in art["paragraphs"] for qa in p["qas"]
            if not qa.get("is_impossible")]


# ------------------------------------------------------------- learning
def learn(arts):
    pairs = {}                       # (question word, sentence word) -> articles
    right_f = {}                     # (kind, feat) -> count in right sentences
    wrong_f = {}                     # (kind, feat) -> count in his wrong picks
    n_k = {}                         # kind -> graded questions
    for art in arts:
        store = fill(art)
        seen = set()
        for q, key in questions(art):
            seeds, reached, cands = score_all(store, q)
            d = diagnose(store, q, cands, reached, key)
            if not d["right"] or d["verdict"] == "not stored":
                continue
            k = kind(q)
            n_k[k] = n_k.get(k, 0) + 1
            rf = feats(store.get(d["right"]).content)
            for f, v in rf.items():
                right_f[(k, f)] = right_f.get((k, f), 0) + int(v)
            for _, n in cands[:3]:            # what he ranked up there wrongly
                if n == d["right"]:
                    continue
                wf = feats(store.get(n).content)
                for f, v in wf.items():
                    wrong_f[(k, f)] = wrong_f.get((k, f), 0) + int(v) / 3.0
            rt = [t for t in store.get(d["right"]).refs
                  if store.get(t) and store.get(t).kind == "term"]
            for m in d["missing"]:
                if store.get(m) is not None:
                    continue
                for f in rt:
                    seen.add((m, f))
        for p in seen:
            pairs[p] = pairs.get(p, 0) + 1

    cm, cf = {}, {}
    for (m, f), c in pairs.items():
        cm[m] = cm.get(m, 0) + c
        cf[f] = cf.get(f, 0) + c
    kept = sorted(((c * c / float(cm[m] * cf[f]), m, f)
                   for (m, f), c in pairs.items() if c >= 3), reverse=True)
    thesaurus = {}
    for _, m, f in kept[:3000]:
        thesaurus.setdefault(m, []).append(f)

    kinds = {}
    for k in n_k:
        row = {}
        for f in FEATS:
            r = right_f.get((k, f), 0) / float(n_k[k])
            w = wrong_f.get((k, f), 0) / float(n_k[k])
            row[f] = round(math.log((r + 0.01) / (w + 0.01)), 3)
        kinds[k] = row
    return thesaurus, kinds, len(pairs), n_k


# ------------------------------------------------- the record, the selector
def record_one(art):
    """every toolset on every question of one article: right or not, filed
    under the context at each level. this is his record."""
    store = fill(art)
    qs = questions(art)
    rec = {}
    for name in TOOLSETS:
        use(name)
        for q, key in qs:
            _, _, cands = score_all(store, q)
            right = bool(cands) and \
                key.lower() in str(store.get(cands[0][1]).content).lower()
            for lv in (1, 2):
                c = rec.setdefault((lv, context_at(lv, store, q), name), [0, 0])
                c[0] += int(right)
                c[1] += 1
    return rec


def build_selector(records):
    """the tool for choosing tools. one builder for every level: for each
    context, how often each toolset was right. the count is the reason he
    gives when he picks."""
    table = {}
    for rec in records:
        for (lv, ctx, name), (r, a) in rec.items():
            c = table.setdefault(str(lv), {}).setdefault(ctx, {}) \
                     .setdefault(name, [0, 0])
            c[0] += r
            c[1] += a
    return table


def init_tools(thesaurus, kinds):
    mind.SYN.clear(); mind.KINDS.clear(); mind.SELECTOR.clear()
    mind.SYN.update((k, set(v)) for k, v in thesaurus.items())
    mind.KINDS.update(kinds)


def record(arts, thesaurus, kinds, jobs=1):
    if jobs > 1:
        from multiprocessing import Pool
        with Pool(jobs, initializer=init_tools,
                  initargs=(thesaurus, kinds)) as pool:
            recs = pool.map(record_one, arts)
    else:
        init_tools(thesaurus, kinds)
        recs = [record_one(a) for a in arts]
    return build_selector(recs)


# ------------------------------------------------------------- the court
ARM = {}


def arm(name, his_level=None):
    """this process and every worker (windows spawns, nothing carries):
    his tools loaded, then one fixed toolset, or his own choice up to a
    level."""
    load_tools()
    ARM.clear()
    ARM.update(name=name, his=his_level)
    if name:
        use(name)


def bench_one(art):
    store = fill(art)
    asked = top1 = 0
    picks = {}
    for q, key in questions(art):
        if ARM.get("his"):
            name, _ = select(store, q, ARM["his"])
            use(name)
            picks[name] = picks.get(name, 0) + 1
        _, _, cands = score_all(store, q)
        asked += 1
        if cands and key.lower() in str(store.get(cands[0][1]).content).lower():
            top1 += 1
    return asked, top1, picks


def bench(arts, jobs=1):
    if jobs > 1:
        from multiprocessing import Pool
        with Pool(jobs, initializer=arm,
                  initargs=(ARM.get("name"), ARM.get("his"))) as pool:
            res = pool.map(bench_one, arts)
    else:
        res = [bench_one(a) for a in arts]
    picks = {}
    for r in res:
        for n, c in r[2].items():
            picks[n] = picks.get(n, 0) + c
    return sum(r[0] for r in res), sum(r[1] for r in res), picks


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "court"
    want = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
    jobs = int(sys.argv[sys.argv.index("-jobs") + 1]) \
        if "-jobs" in sys.argv else 1
    data = json.load(open(SQUAD, encoding="utf-8"))["data"]
    learn_arts, exam = split(data, want)

    if cmd == "learn":
        mind.SYN.clear(); mind.KINDS.clear()       # nothing installed
        t0 = time.time()
        thesaurus, kinds, n_pairs, n_k = learn(learn_arts)
        t1 = time.time()
        selector = record(learn_arts, thesaurus, kinds, jobs)
        json.dump({"thesaurus": thesaurus, "kinds": kinds,
                   "selector": selector},
                  open(TOOLS, "w", encoding="utf-8"), indent=1)
        print("learned from %d articles in %.0fs: %d pairs seen, %d kept "
              "into the thesaurus; kinds table over %s"
              % (len(learn_arts), time.time() - t0, n_pairs,
                 sum(len(v) for v in thesaurus.values()),
                 ", ".join("%s %d" % kv for kv in sorted(n_k.items()))))
        print("his kinds table (log odds right vs his wrong picks):")
        print("  %-9s" % "" + "".join("%9s" % f for f in FEATS))
        for k, row in sorted(kinds.items()):
            print("  %-9s" % k + "".join("%9.2f" % row[f] for f in FEATS))
        print("his selector, built in %.0fs from every toolset on every "
              "graded question (%d toolsets):" % (time.time() - t1,
                                                   len(TOOLSETS)))
        print("  level 1, by kind:      his pick                 right   "
              "   next best")
        for ctx, table in sorted(selector["1"].items()):
            ranked = sorted(((r, n) for n, (r, a) in table.items()),
                            reverse=True)
            (r1, n1), (r2, n2) = ranked[0], ranked[1]
            print("  %-9s %-28s %5d/%-5d  %-28s %5d"
                  % (ctx, n1, r1, table[n1][1], n2, r2))
        print("  level 2, kind / words known: %d contexts"
              % len(selector["2"]))
        return

    rows = [(name, name, None) for name in TOOLSETS] + [
        ("HIS CHOICE, level 1 (by kind)", None, 1),
        ("HIS CHOICE, level 2 over 1 (kind / words known)", None, 2)]
    print("the other %d articles, never learned from:" % len(exam))
    for label, name, his in rows:
        arm(name, his)
        t0 = time.time()
        asked, top1, picks = bench(exam, jobs)
        print("  %-48s top1 %5d / %d (%.1f%%)   %.0fs"
              % (label, top1, asked, 100.0 * top1 / asked, time.time() - t0))
        if picks:
            tot = float(sum(picks.values()))
            print("      he picked: " + ", ".join(
                "%s %.0f%%" % (n, 100 * c / tot) for n, c in
                sorted(picks.items(), key=lambda x: -x[1])[:5]))


if __name__ == "__main__":
    main()
