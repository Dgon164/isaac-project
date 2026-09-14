#!/usr/bin/env python3
"""crawl.py -- the net crawler: everything he built, as records, verified.

    python walk/crawl.py 999999 -jobs 24        crawl, verify, write self.csv

Owner: "a net crawler. build an informational database it can try to
evaluate and verify. see if the things being built are correct. the
information is there and it's readable, so how do we analyze it at scale
to see exactly what is happening and why?"

CRAWL    every rule he holds becomes a record: kind, name, content, where
         it came from, how much it rests on. Sources: tools.json (his
         thesaurus, kinds table, selector, settings, decisions), lens.json
         (his lens chain and critic), his shape map, store.json (his
         confirmations, refusals, runs, sense readings), attention.json,
         python_store.json (the textbook examples he verified).
VERIFY   each record is re-tested on data it was NOT built from -- the
         other half of squad, fresh problems, a rerun -- and stamped:
         +1 holds, -1 refuted, 0 untested (too few sightings to say).
WRITE    walk/self.csv and walk/self.json: the database of himself. The
         csv is a table, so the walk can be asked about it like any other.
"""
import json
import math
import os
import random
import sys
import time
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "engine"))
from core import Store, Item
from linker import link, terms
import mind
from mind import score_all, diagnose, kind, feats, FEATS, load_tools, use, rank_table
import tools as T
import lens as L
import shapes as S

SQUAD = T.SQUAD
TOOLS = os.path.join(HERE, "tools.json")
LENS = os.path.join(HERE, "lens.json")
STORE = os.path.join(HERE, "store.json")
PYSTORE = os.path.join(HERE, "python_store.json")
ATT = os.path.join(HERE, "attention.json")
WORDNET = os.environ.get(
    "ISAAC_DICT",
    r"C:\Users\jtwee\Downloads\New folder (3)\intellon\wordnet_full.json")
CACHE = os.path.join(HERE, "self_cache.json")   # the held-out evidence, kept


def stem(w):
    """the crude stem: enough to see that began is begin's form and honour
    is honor's spelling."""
    w = w.lower().replace("our", "or").replace("ise", "ize").replace("yse", "yze")
    for suf in ("ings", "ing", "ies", "ied", "ers", "ed", "es", "er", "ly", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            w = w[:-len(suf)]
            break
    if w.endswith("ie"):
        w = w[:-2] + "y"
    return w.rstrip("e")


def load_wordnet():
    """three things wordnet can say about a pair: synonym (same sense or
    listed), mentioned in the definition or examples, or antonym."""
    syn, defw, ant = defaultdict(set), defaultdict(set), defaultdict(set)
    by_sense = defaultdict(set)
    for e in json.load(open(WORDNET, encoding="utf-8")):
        w = e["word"].lower().replace("-", "_")
        by_sense[e["sense"]].add(w)
        for x in e.get("synonyms", []) or []:
            syn[w].add(x.lower().replace("-", "_").replace(" ", "_"))
        for x in e.get("antonyms", []) or []:
            ant[w].add(x.lower().replace("-", "_"))
        text = " ".join([e.get("def", "")] + list(e.get("examples", []) or []))
        defw[w].update(terms(text))
    for ws in by_sense.values():
        for w in ws:
            syn[w] |= ws
    return syn, defw, ant


def rec(kind_, name, content, origin, support, truth, reason):
    return {"kind": kind_, "name": name, "content": content, "origin": origin,
            "support": support, "truth": truth, "reason": reason}


# --------------------------------------------------- the held-out evidence
def init():
    load_tools()
    use("thes+kinds-second")


def evidence_one(art):
    """one held-out article: per question, what the right sentence carried
    and what his pick carried. the evidence every word rule is tested on."""
    store = T.fill(art)
    out = []
    for q, key in T.questions(art):
        seeds, reached, cands = score_all(store, q)
        d = diagnose(store, q, cands, reached, key)
        if not d["right"] or d["verdict"] == "not stored":
            continue
        r = store.get(d["right"])
        p = store.get(d["picked"]) if d["picked"] and d["picked"] != d["right"] else None
        out.append({"kind": kind(q), "own": sorted(set(terms(q))),
                    "right": sorted(r.refs), "pick": sorted(p.refs) if p else [],
                    "rf": feats(r.content), "pf": feats(p.content) if p else None,
                    "ok": d["verdict"] == "right"})
    return out


def main():
    want = int(sys.argv[1]) if len(sys.argv) > 1 else 999999
    jobs = int(sys.argv[sys.argv.index("-jobs") + 1]) if "-jobs" in sys.argv else 1
    t0 = time.perf_counter()
    data = json.load(open(SQUAD, encoding="utf-8"))["data"]
    learn, exam = T.split(data, want)
    tools = json.load(open(TOOLS, encoding="utf-8"))
    load_tools()
    R = []

    # ---------------------------------------------------------- evidence
    print("prediction, stated first: most thesaurus pairs untestable (rare words), "
          "a minority of the testable refuted; kinds rows mostly hold; the big "
          "selector picks hold, thin level-2 ones flip; about half the lens "
          "conjunctions keep their sign; shapes hold outright.\n")
    cache = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) and "-fresh" not in sys.argv else {}
    if "ev" in cache:
        ev = cache["ev"]
    elif jobs > 1:
        from multiprocessing import Pool
        with Pool(jobs, initializer=init) as pool:
            ev = [e for part in pool.map(evidence_one, exam) for e in part]
    else:
        init()
        ev = [e for a in exam for e in evidence_one(a)]
    print("evidence: %d held-out questions with the right sentence known%s  (%.0fs)"
          % (len(ev), " (cached)" if "ev" in cache else "", time.perf_counter() - t0))
    syn, defw, ant = load_wordnet()
    print("wordnet read: synonyms for %d words, definitions for %d  (%.0fs)"
          % (len(syn), len(defw), time.perf_counter() - t0))
    by_word = defaultdict(list)
    for e in ev:
        for w in e["own"]:
            by_word[w].append(e)

    # ---------------------------------------------------------- thesaurus
    refs = Counter()
    for q, ss in tools["thesaurus"].items():
        for s in ss:
            qs = by_word.get(q, [])
            r = sum(1 for e in qs if s in e["right"])
            w = sum(1 for e in qs if s in e["pick"])
            said = []                       # what each reference says
            if max(r, w) >= 3 and r > w:
                said.append(("evidence", 1, "right sentence %d, wrong pick %d" % (r, w)))
            elif max(r, w) >= 3 and w > r:
                said.append(("evidence", -1, "wrong pick %d, right sentence %d" % (w, r)))
            if s in ant.get(q, ()) or q in ant.get(s, ()):
                said.append(("wordnet", -1, "antonyms"))
            elif s in syn.get(q, ()) or q in syn.get(s, ()):
                said.append(("wordnet", 1, "synonyms"))
            elif s in defw.get(q, ()) or q in defw.get(s, ()):
                said.append(("dictionary", 1, "one is in the other's definition or examples"))
            if stem(q) == stem(s) and q != s:
                said.append(("morphology", 1, "same stem: %s" % stem(q)))
            votes = [v for _, v, _ in said]
            if not votes:
                truth, why = 0, "no reference can speak: seen in %d questions, unknown to wordnet, different stems" % len(qs)
            elif min(votes) < 0 and max(votes) > 0:
                truth, why = 0, "references disagree: " + "; ".join("%s says %s" % (a, c) for a, v, c in said)
            else:
                truth = 1 if max(votes) > 0 else -1
                why = "; ".join("%s: %s" % (a, c) for a, v, c in said)
            for a, v, _ in said:
                refs[(a, v)] += 1
            R.append(rec("thesaurus pair", "%s>%s" % (q, s), "%s means %s" % (q, s),
                         "tools.py learn: graded record, his half", len(qs), truth, why))
    print("thesaurus references: " + ", ".join(
        "%s %s %d" % (a, "confirms" if v > 0 else "refutes", n) for (a, v), n in sorted(refs.items())))

    # ---------------------------------------------------------- kinds
    by_kind = defaultdict(list)
    for e in ev:
        by_kind[e["kind"]].append(e)
    for k, row in tools["kinds"].items():
        es = by_kind.get(k, [])
        wrongs = [e for e in es if e["pf"] is not None]
        for f, wgt in row.items():
            if len(es) < 20:
                truth, why = 0, "%d held-out questions of this kind" % len(es)
            else:
                rr = sum(1 for e in es if e["rf"].get(f)) / float(len(es))
                wr = sum(1 for e in wrongs if e["pf"].get(f)) / float(len(wrongs) or 1)
                held = (rr > wr) if wgt > 0 else (rr < wr) if wgt < 0 else True
                truth = 1 if held else -1
                why = "right sentences carry it %.0f%%, his wrong picks %.0f%% (learned log odds %+.2f)" % (
                    100 * rr, 100 * wr, wgt)
            R.append(rec("kinds row", "%s carries %s" % (k, f), "%+.2f" % wgt,
                         "tools.py learn: graded record, his half", len(es), truth, why))

    # ---------------------------------------------------------- selector
    t1 = time.perf_counter()
    if "held" in cache:
        held = cache["held"]
    else:
        held = T.record(exam, tools["thesaurus"], tools["kinds"], {}, jobs)   # held-out, every toolset
        json.dump({"ev": ev, "held": held}, open(CACHE, "w", encoding="utf-8"))
    print("selector: every toolset on the held-out half%s  (%.0fs)"
          % (" (cached)" if "held" in cache else "", time.perf_counter() - t1))
    for lv, table in tools["selector"].items():
        for ctx, row in table.items():
            ranked = rank_table(row)
            if not ranked:
                R.append(rec("selector pick", "level %s %s" % (lv, ctx), "no pick",
                             "tools.py learn: every toolset on every graded question", 0, 0,
                             "below his record minimum"))
                continue
            pick, prec = ranked[0]
            hrow = held.get(lv, {}).get(ctx, {})
            hp = hrow.get(pick)
            if not hp or hp[1] < 20:
                truth, why = 0, "held-out has %d asks in this context" % (hp[1] if hp else 0)
            else:
                best = max(hrow.items(), key=lambda kv: kv[1][0] / float(kv[1][1]))
                prate, brate = hp[0] / float(hp[1]), best[1][0] / float(best[1][1])
                runner = ranked[1] if len(ranked) > 1 else None
                rrate = None
                if runner and runner[0] in hrow:
                    rr = hrow[runner[0]]
                    rrate = rr[0] / float(rr[1])
                if rrate is not None and prate < rrate:
                    truth = -1
                    why = "held-out: his pick %.1f%%, his runner-up %.1f%% (best there %s %.1f%%)" % (
                        100 * prate, 100 * rrate, best[0], 100 * brate)
                else:
                    truth = 1
                    why = "held-out: his pick %.1f%%%s; best there %s %.1f%%" % (
                        100 * prate, "" if rrate is None else ", runner-up %.1f%%" % (100 * rrate),
                        best[0], 100 * brate)
            R.append(rec("selector pick", "level %s %s" % (lv, ctx), pick,
                         "tools.py learn: every toolset on every graded question",
                         prec[1], truth, why))

    # ---------------------------------------------------------- settings, decisions
    for k, v in tools.get("settings", {}).items():
        R.append(rec("setting", k, str(v), "tools.py tune", 0, 1 if tools.get("decisions") else 0,
                     "chosen by one look on the held-out half" if tools.get("decisions") else "default, never tested"))
    for k, v in tools.get("decisions", {}).items():
        truth = 1 if "KEPT" in v else -1 if "refused" in v else 0
        R.append(rec("decision", k, v, "tools.py tune", 0, truth, v))

    # ---------------------------------------------------------- lens chain
    if os.path.exists(LENS):
        lj = json.load(open(LENS, encoding="utf-8"))
        L.SETTINGS.update(lj["settings"])
        names = lj["atoms"]
        index = {a: i for i, a in enumerate(names)}
        t2 = time.perf_counter()
        fields = L.run(L.pass_fields, [(a, "other") for a in exam], jobs, index)
        oth = L.Side(fields)
        print("lens: the held-out half as atoms  (%.0fs)" % (time.perf_counter() - t2))
        import torch
        for li, (lens, earned) in enumerate(zip(lj["chain"], lj["earned"])):
            lens = [tuple(c) for c in lens]
            C = oth.conj(lens, len(names))
            e_o, rc, wc = L.readout(C, oth.right, torch.ones(oth.n, dtype=torch.bool, device=L.DEV))
            e_o = e_o.cpu().numpy(); rc = rc.cpu().numpy(); wc = wc.cpu().numpy()
            for i, c in enumerate(lens):
                e_h = earned[i]
                if abs(e_h) < 0.3:
                    continue                      # never earned a place
                if rc[i] + wc[i] < 20:
                    truth, why = 0, "seen %d times on the held-out half" % (rc[i] + wc[i])
                elif (e_o[i] > 0) == (e_h > 0) and abs(e_o[i]) >= 0.3:
                    truth, why = 1, "his half %+.2f, held-out %+.2f" % (e_h, e_o[i])
                elif (e_o[i] > 0) != (e_h > 0) and abs(e_o[i]) >= 0.3:
                    truth, why = -1, "his half %+.2f, held-out %+.2f: the sign flipped" % (e_h, e_o[i])
                else:
                    truth, why = 0, "his half %+.2f, held-out %+.2f: too weak to say" % (e_h, e_o[i])
                R.append(rec("lens conjunction", "L%d:%s" % (li + 1, L.say(names, c)), "%+.2f" % e_h,
                             "lens.py: right vs field, his half", int(rc[i] + wc[i]), truth, why))

    # ---------------------------------------------------------- shapes
    rng = random.Random(5)
    held_forms = {rel: forms[0][rng.randrange(len(forms[0]))] for rel, forms in S.FORMS.items()}
    lesson_forms = {rel: [f for f in forms[0] if f != held_forms[rel]] for rel, forms in S.FORMS.items()}
    lesson = [S.gen(rng, lesson_forms) for _ in range(120)]
    m = S.learn_map(lesson)
    rng99 = random.Random(99)
    fresh = [S.gen(rng99, lesson_forms) for _ in range(600)]
    for sh, e in m.items():
        ps = [p for p in fresh if S.shape(p["text"]) == sh]
        if not e["meaning"]:
            truth, why = 0, "no meaning fit his lesson"
        elif len(ps) < 5:
            truth, why = 0, "%d fresh problems of this shape" % len(ps)
        else:
            ok = sum(1 for p in ps if S.OPS[e["meaning"]](*S.numbers(p["text"])[:2]) == p["answer"])
            truth, why = (1 if ok == len(ps) else -1), "%d of %d fresh problems reproduced" % (ok, len(ps))
        R.append(rec("shape meaning", " ".join(sh)[:70], e["meaning"] or "-",
                     "shapes.py: 120 labeled problems", e["n"], truth, why))

    # ---------------------------------------------------------- his live store
    if os.path.exists(STORE):
        st = mind.load_store()
        conf = [(c, n, v) for (c, n), v in st.relevance.items()]
        runs = sum(1 for i in st.items.values() if i.kind == "run")
        senses = [i for i in st.items.values() if i.kind == "sense"]
        for c, n, v in conf:
            if v > 0 and st.get(n) is not None:
                q = c
                seeds, reached, cands = score_all(st, q)
                top = cands[0][1] if cands else None
                truth = 1 if top == n else -1
                why = "rerun: it is his top answer" if top == n else "rerun: his top is %s" % top
                R.append(rec("confirmation", "%s -> %s" % (c[:40], n), "+1", "a correction or a key", 1, truth, why))
            elif v < 0:
                R.append(rec("refusal", "%s -x- %s" % (c[:40], n), "-1", "a correction", 1, 1, "stands"))
        R.append(rec("run record", "runs banked", str(runs), "residue", runs, 0, "his own asks; not a claim"))
        graded = [s for s in senses if "verdict" in s.content]
        R.append(rec("sense record", "readings kept", str(len(senses)), "sense_keep", len(senses), 0,
                     "%d graded" % len(graded)))

    # ---------------------------------------------------------- attention, textbook
    if os.path.exists(ATT):
        att = json.load(open(ATT, encoding="utf-8")).get("1", {})
        R.append(rec("attention record", "words with a record", str(len(att)), "his compare on corrections",
                     len(att), 0, "not re-tested here"))
    if os.path.exists(PYSTORE):
        d = json.load(open(PYSTORE, encoding="utf-8"))
        ex = [(n, tr) for n, k, c, tr, nat, tag, refs in d["items"] if k == "sentence" and tag.endswith(" example")]
        R.append(rec("textbook example", "python tutorial >>> examples", "%d" % len(ex),
                     "school.py: run against the book", len(ex), 0,
                     "%d verified (+1), %d unverified (0)" % (sum(1 for _, t in ex if t == 1),
                                                            sum(1 for _, t in ex if t != 1))))

    # ---------------------------------------------------------- write, summarise
    json.dump(R, open(os.path.join(HERE, "self.json"), "w", encoding="utf-8"), indent=0)
    import csv
    with open(os.path.join(HERE, "self.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        # first column is the row's name in his store, so it must be unique
        w.writerow(["record", "kind", "name", "content", "origin", "support", "truth", "verdict", "reason"])
        for i, r in enumerate(R):
            w.writerow(["%s %d" % (r["kind"], i), r["kind"], r["name"], r["content"], r["origin"],
                        r["support"], r["truth"],
                        {1: "holds", -1: "refuted", 0: "untested"}[r["truth"]], r["reason"]])
    print("\nTHE DATABASE OF HIMSELF: %d records -> walk/self.csv, walk/self.json  (%.0fs in all)\n"
          % (len(R), time.perf_counter() - t0))
    print("  %-18s %7s %7s %7s %8s" % ("kind", "built", "holds", "refuted", "untested"))
    kinds = []
    for k in dict.fromkeys(r["kind"] for r in R):
        rs = [r for r in R if r["kind"] == k]
        kinds.append(k)
        print("  %-18s %7d %7d %7d %8d" % (k, len(rs), sum(1 for r in rs if r["truth"] == 1),
                                           sum(1 for r in rs if r["truth"] == -1),
                                           sum(1 for r in rs if r["truth"] == 0)))
    print("\nREFUTED, a few of each kind, with why:")
    for k in kinds:
        bad = [r for r in R if r["kind"] == k and r["truth"] == -1]
        for r in sorted(bad, key=lambda r: -r["support"])[:3]:
            print("  [%s] %s = %s\n      %s" % (k, r["name"][:60], r["content"][:30], r["reason"]))
    print("\nHOLDS, the strongest of the word rules:")
    for k in ("thesaurus pair", "kinds row", "lens conjunction"):
        good = [r for r in R if r["kind"] == k and r["truth"] == 1]
        for r in sorted(good, key=lambda r: -r["support"])[:3]:
            print("  [%s] %s = %s\n      %s" % (k, r["name"][:60], r["content"][:30], r["reason"]))


if __name__ == "__main__":
    main()
