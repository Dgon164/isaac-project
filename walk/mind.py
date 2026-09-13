#!/usr/bin/env python3
"""mind.py -- the walk, usable.

    python walk/mind.py file.txt file.csv           interactive
    python walk/mind.py file.txt -q "a question"    one shot

Type a question, he walks the store and answers with the path.
Runs leave residue: every ask becomes an item pointing at what it
touched and pointed at by the question's words, so a later question
reaches what an earlier one found, and its words count in the score.
Corrections:
    no: <the truth>     grades the last question: the run is filed with
                        his pick and the verdict, the pick is refused
                        for that question, the right item learns the
                        question words it lacked
    why                 how the last answer was reached
    quit                saves store.json

State is one file, walk/store.json. Delete it for a blank mind.
"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "engine"))
from core import Item, Store
from linker import link, terms

STOREFILE = os.path.join(HERE, "store.json")
TOOLSFILE = os.path.join(HERE, "tools.json")   # the tools he built himself
DICTFILE = os.environ.get(
    "ISAAC_DICT",
    r"C:\Users\jtwee\Downloads\New folder (3)\intellon\wordnet_full.json")
LIBFILE = os.path.join(HERE, "library.json")
SYN = {}          # word -> words: his thesaurus (or wordnet, on request)
KINDS = {}        # question kind -> {what the right sentence carries: log odds}
FEATS = ("year", "number", "name", "percent", "money")
KIND_WORDS = ("who", "when", "where", "how many", "how much", "how",
              "what", "which", "why")
FEAT = {}         # sentence text -> its features, read once


def kind(question):
    """the question's kind word, read off its opening."""
    q = question.lower().strip()
    for k in KIND_WORDS:
        if q.startswith(k) or (" " + k + " ") in q[:40]:
            return k
    return "other"


def feats(text):
    """what a sentence carries -- a year, a number, a name, a percent,
    money -- read off it with no parser."""
    t = str(text)
    f = FEAT.get(t)
    if f is None:
        f = FEAT[t] = {
            "year": bool(re.search(r"\b(1[0-9]{3}|20[0-9]{2})\b", t)),
            "number": bool(re.search(r"\d", t)),
            "name": bool(re.search(r"\b[A-Z][a-z]+", t[1:])),
            "percent": "%" in t or "percent" in t.lower(),
            "money": bool(re.search(r"[$\u00a3\u20ac]|\bmillion\b|\bbillion\b", t))}
    return f


def read_dictionary(store, cap=8):
    """a dictionary built from reading: the words of this store that
    keep each other's company across its sentences. nothing installed;
    it comes out of the text he was given. kept on the store."""
    sents = [set(it.refs) for it in store.items.values()
             if it.kind == "sentence"]
    c1, c2 = {}, {}
    for ws in sents:
        ws = [w for w in ws if store.get(w) and store.get(w).kind == "term"]
        for a in ws:
            c1[a] = c1.get(a, 0) + 1
        for i, a in enumerate(ws):
            for b in ws[i + 1:]:
                k = (a, b) if a < b else (b, a)
                c2[k] = c2.get(k, 0) + 1
    best = {}
    for (a, b), c in c2.items():
        if c < 2:
            continue
        sc = c * c / float(c1[a] * c1[b])
        best.setdefault(a, []).append((sc, b))
        best.setdefault(b, []).append((sc, a))
    store.dictionary = {w: {b for _, b in sorted(v, reverse=True)[:cap]}
                        for w, v in best.items()}
    return len(store.dictionary)


def load_tools(path=TOOLSFILE):
    """his own thesaurus and kinds table, built by tools.py learn."""
    d = json.load(open(path, encoding="utf-8"))
    SYN.clear(); KINDS.clear()
    SYN.update((k, set(v)) for k, v in d.get("thesaurus", {}).items())
    KINDS.update(d.get("kinds", {}))
    return len(SYN)


def load_dictionary(path=DICTFILE, cap=50, wide=False, rebuild=False,
                    wordnet=False):
    """his own tools first (walk/tools.json, built by tools.py learn);
    wordnet only when asked for, or when he has built nothing yet.

    wordnet: thesaurus + dictionary as one map: words sharing a sense are
    synonyms; a word whose definition names t is a neighbor of t
    ('fame: ...widely known and popular' makes fame a neighbor of
    popular). wide also mines example sentences and antonyms. capped:
    glue words relate to thousands and would drown the question.
    Built once into library.json and loaded from there after."""
    if not wordnet and os.path.exists(TOOLSFILE):
        return load_tools()
    if os.path.exists(LIBFILE) and not rebuild:
        SYN.clear()
        SYN.update((k, set(v)) for k, v in
                   json.load(open(LIBFILE, encoding="utf-8")).items())
        return len(SYN)
    entries = json.load(open(path, encoding="utf-8"))
    sense, rel = {}, {}
    for e in entries:
        sense.setdefault(e["sense"], []).append(e["word"].lower())
        w = e["word"].lower()
        for t in terms(e.get("def", "")):
            rel.setdefault(t, set()).add(w)
        if wide:
            for t in terms(" ".join(e.get("examples", []))):
                rel.setdefault(t, set()).add(w)
            for a in e.get("antonyms", []):
                rel.setdefault(a.lower(), set()).add(w)
    for ws in sense.values():
        for w in ws:
            if len(ws) > 1:
                rel.setdefault(w, set()).update(x for x in ws if x != w)
    SYN.clear()
    SYN.update((t, s) for t, s in rel.items() if len(s) <= cap)
    json.dump({k: sorted(v) for k, v in SYN.items()},
              open(LIBFILE, "w", encoding="utf-8"))
    return len(SYN)


# ---------------------------------------------------------------- persistence
def save(store):
    d = {"items": [[i.name, i.kind, i.content, i.truth, i.native, i.tag,
                    list(i.refs)] for i in store.items.values()],
         "rel": [[c, n, v] for (c, n), v in store.relevance.items()]}
    json.dump(d, open(STOREFILE, "w", encoding="utf-8"), default=str)


def load_store():
    store = Store()
    if os.path.exists(STOREFILE):
        d = json.load(open(STOREFILE, encoding="utf-8"))
        for name, kind, content, truth, native, tag, refs in d["items"]:
            store.put(Item(name, kind, content, truth, native, tag, refs))
        for c, n, v in d.get("rel", []):
            store.set_rel(c, n, v)
    return store


# ---------------------------------------------------------------- filling
def link_table(path, store):
    """a row becomes an item; every non-numeric cell becomes a reference."""
    import csv
    rows = [r for r in csv.reader(open(path, encoding="utf-8")) if r]
    hdr = [h.strip().lower() for h in rows[0]]
    tname = os.path.splitext(os.path.basename(path))[0]
    made = 0
    names = []
    for r in rows[1:]:
        name = r[0].strip().lower().replace(" ", "_")
        content = dict(zip(hdr[1:], (c.strip() for c in r[1:])))
        refs = [c.strip().lower().replace(" ", "_") for c in r[1:]
                if c.strip() and not re.fullmatch(r"-?\d+\.?\d*", c.strip())]
        old = store.get(name)
        if old is not None:  # same name seen in prose: the row absorbs its links
            refs += [r2 for r2 in old.refs if r2 not in refs]
        store.put(Item(name, "row", content=content,
                       tag=os.path.basename(path), refs=refs + [tname]))
        names.append(name)
        for t in refs + [name]:
            it = store.get(t)
            if it is None:
                store.put(Item(t, "term", tag=path, refs=[name]))
            elif name not in it.refs and t != name:
                it.refs = tuple(it.refs) + (name,)
        made += 1
    old = store.get(tname)
    if old is not None:
        names += [r2 for r2 in old.refs if r2 not in names]
    store.put(Item(tname, "table", tag=os.path.basename(path), refs=names))
    # every column is a spine too: the property points at every row
    # carrying it, its words become terms, so "melting point" in a
    # question reaches all materials through one item -- across tables,
    # since a shared header lands in the same property.
    for col in hdr[1:]:
        crefs = list(names)
        old = store.get(col)
        if old is not None:
            crefs += [r2 for r2 in old.refs if r2 not in crefs]
        store.put(Item(col, "property", tag=os.path.basename(path),
                       refs=crefs))
        for w in terms(col.replace("_", " ")):
            it = store.get(w)
            if it is None:
                store.put(Item(w, "term", tag=tname, refs=[col]))
            elif col not in it.refs:
                it.refs = tuple(it.refs) + (col,)
    return made


def fill(path, store):
    if path.lower().endswith(".csv"):
        n = link_table(path, store)
    else:
        n = link(open(path, encoding="utf-8").read(), store,
                 tag=os.path.basename(path))
    print("  filled %d items from %s (store: %d)" %
          (n, os.path.basename(path), len(store.items)))


# ---------------------------------------------------------------- the ask
def walk(store, seeds):
    """depth one per step, nothing pulled twice, settles on its own."""
    open_, seen = list(seeds), set(seeds)
    i = 0
    while i < len(open_):
        it = store.get(open_[i])
        i += 1
        if it is None:
            continue
        for r in it.refs:
            if r not in seen and store.get(r):
                seen.add(r)
                open_.append(r)
    return seen


def ask(store, question):
    """one bag of words: the question's own words plus their thesaurus
    pull. overlap with the bag is the score, own words count first.
    nothing in the bag = a tangent = not an answer. that is all."""
    seeds, reached, cands = score_all(store, question)
    return seeds, reached, [(n, store.get(n)) for _, n in cands[:3]]


def score_all(store, question):
    """the scored field, best first. ask() takes the top three; a probe
    that wants the gap between first and second takes the list."""
    own = set(terms(question))
    bag = set(own)
    read = getattr(store, "dictionary", None)   # built from reading
    for t in own:
        bag |= SYN.get(t, set())
        if read:
            bag |= read.get(t, set())
    seeds = sorted(t for t in bag if store.get(t))
    if not seeds:
        return [], set(), []
    reached = walk(store, seeds)
    ctx = context(question)
    row = KINDS.get(kind(question)) if KINDS else None
    cands = []
    for n in reached:
        it = store.get(n)
        if it.kind not in ("sentence", "row") or it.truth == -1 or it.native:
            continue
        if store.rel(ctx, n) < 0:      # refused for this question: set aside
            continue
        r = set(it.refs) | {n}
        earned = set()
        for x in it.refs:          # words the runs brought: a question
            run = store.get(x)     # this item answered names it too
            if run is not None and run.kind == "run":
                earned |= set(run.content.get("key", ()))
        if bag & (r | earned):
            hit = own & r
            rare = sum(1.0 / len(store.get(t).refs) for t in hit
                       if store.get(t) and store.get(t).refs)
            fit = 0.0                  # does it carry the kind of answer
            if row and it.kind == "sentence":   # the question asks for
                f = feats(it.content)
                fit = round(sum(w for k, w in row.items() if f.get(k)), 2)
            cands.append(((len(hit), fit, rare, len(bag & (r | earned))), n))
    cands.sort(reverse=True)
    return seeds, reached, cands


def clean_win(cands, gap=1):
    """is the winner clear of the runner-up, by that many own words?
    measured on squad: tied fields are right 20% of the time, own +1
    68%, own +2 92%, own +3 95%. a run that was not clear is a guess,
    and banking a guess teaches the store the guess."""
    if not cands:
        return False
    if len(cands) < 2:
        return True
    return cands[0][0][0] - cands[1][0][0] >= gap


def context(question):
    """the question's key words, joined: the context a refusal or a
    graded run is filed under."""
    return " ".join(sorted(set(terms(question))))


def diagnose(store, question, cands, reached, truth):
    """what happened, in his own terms. the right item is any sentence
    or row whose content carries the truth. verdict: right / close /
    lost tie / fewer words / shares nothing / no path / not stored."""
    truth = truth.lower().strip()
    own = set(terms(question))
    rank = {n: i for i, (_, n) in enumerate(cands)}
    right = [n for n, it in store.items.items()
             if it.kind in ("sentence", "row") and not it.native
             and truth in str(it.content).lower()]
    ranked = sorted((rank[n], n) for n in right if n in rank)
    d = {"q": question, "truth": truth, "context": context(question),
         "picked": cands[0][1] if cands else None,
         "right": None, "rank": None, "found": [], "missing": sorted(own)}
    if ranked:
        d["rank"], d["right"] = ranked[0]
    elif right:
        d["right"] = right[0]
    if d["right"]:
        r = set(store.get(d["right"]).refs)
        d["found"] = sorted(own & r)
        d["missing"] = sorted(own - r)
    if d["rank"] == 0:
        d["verdict"] = "right"
    elif d["rank"] is not None and d["rank"] < 3:
        d["verdict"] = "close"
    elif d["rank"] is not None:
        d["verdict"] = ("lost tie" if cands[d["rank"]][0][0] == cands[0][0][0]
                        else "fewer words")
    elif any(n in reached for n in right):
        d["verdict"] = "shares nothing"
    elif right:
        d["verdict"] = "no path"
    else:
        d["verdict"] = "not stored"
    return d


def grade(store, question, cands, reached, truth):
    """feed the outcome back. the run is filed with his pick, the
    verdict and the details. a wrong pick is refused for this
    question. the right item learns the question words it lacked, so
    the next question in those words reaches it. a truth the store
    never held becomes an answer sentence."""
    d = diagnose(store, question, cands, reached, truth)
    n_runs = sum(1 for i in store.items.values() if i.kind == "run")
    name = "run_%03d" % n_runs
    refs = [n for _, n in cands[:3]] + ([d["right"]] if d["right"] else [])
    store.put(Item(name, "run", content=dict(d, key=sorted(set(terms(question))),
                                             answers=[n for _, n in cands[:3]]),
                   tag="graded", refs=refs))
    for t in set(terms(question)):
        it = store.get(t)
        if it is None:
            store.put(Item(t, "term", tag="run", refs=[name]))
        elif name not in it.refs:
            it.refs = tuple(it.refs) + (name,)
    if d["verdict"] == "right":
        return d
    if d["picked"]:
        store.set_rel(d["context"], d["picked"], -1)
    if d["right"]:
        it = store.get(d["right"])       # the right item earns the run:
        if name not in it.refs:          # its words count, second tier
            it.refs = tuple(it.refs) + (name,)
        for w in d["missing"]:           # a specific word it lacked, it
            t = store.get(w)             # takes as its own: a paraphrase.
            if t is not None and len(t.refs) > 1:
                continue                 # a common word is not a lesson
            if w not in it.refs:
                it.refs = tuple(it.refs) + (w,)
            if t is None:
                store.put(Item(w, "term", tag="graded", refs=[d["right"]]))
            elif d["right"] not in t.refs:
                t.refs = tuple(t.refs) + (d["right"],)
    else:
        ts = terms(truth) + [w for w in terms(question) if w not in terms(truth)]
        an = "a%03d_%s" % (sum(1 for i in store.items.values()
                               if i.tag == "answer"), "_".join(ts[:3]))
        store.put(Item(an, "sentence", content=truth, tag="answer", refs=ts))
        for w in ts:
            t = store.get(w)
            if t is None:
                store.put(Item(w, "term", tag="answer", refs=[an]))
            elif an not in t.refs:
                t.refs = tuple(t.refs) + (an,)
        d["right"] = an
    return d


def residue(store, question, seeds, answers):
    """the run goes back into the store; answers that appeared together
    now share a link a future walk can cross."""
    n_runs = sum(1 for i in store.items.values() if i.kind == "run")
    name = "run_%03d" % n_runs
    content = {"q": question, "key": sorted(set(terms(question))),
               "answers": [a for a, _ in answers]}
    store.put(Item(name, "run", content=content, tag="run",
                   refs=list(seeds) + [a for a, _ in answers]))
    for a, _ in answers:
        it = store.get(a)
        if name not in it.refs:
            it.refs = tuple(it.refs) + (name,)
    for t in content["key"]:   # the question's words now reach the run,
        it = store.get(t)      # and through it the answers it found --
        if it is None:         # including words the store had never seen
            store.put(Item(t, "term", tag="run", refs=[name]))
        elif name not in it.refs:
            it.refs = tuple(it.refs) + (name,)
    return name


def find_prev(store, question):
    """the most recent run of this same question, by term set."""
    key = sorted(set(terms(question)))
    hit = None
    for it in store.items.values():
        if it.kind != "run":
            continue
        if isinstance(it.content, dict):
            k, ans = it.content.get("key"), it.content.get("answers", [])
        else:  # old-format run: question stored as a plain string
            k, ans = sorted(set(terms(str(it.content)))), list(it.refs)
        if k == key:
            hit = (it.name, ans)
    return hit


def compare_runs(store, prev, answers, question):
    """asked before: say so. changed: the difference is the lesson."""
    pname, old = prev
    new = [n for n, _ in answers]
    if old and new and old[0] == new[0]:
        print("  (also a previous answer -- rerun agrees)")
        return
    dropped = [n for n in old if n not in new]
    added = [n for n in new if n not in old]
    print("  changed since last time:")
    if dropped:
        print("    then, not now: " + ", ".join(dropped))
    if added:
        print("    now, not then: " + ", ".join(added))
    text = "changed for '%s' -- then not now: %s; now not then: %s" % (
        question, ", ".join(dropped) or "-", ", ".join(added) or "-")
    n_l = sum(1 for i in store.items.values() if i.tag == "lesson")
    store.put(Item("lesson_%03d" % n_l, "sentence", content=text,
                   tag="lesson", refs=sorted(set(terms(question)))))


def conditions(store, reached, qset):
    """conditions the walk reached. if the question names a context,
    only that context's conditions fire; otherwise all of them do."""
    cs = [store.get(n) for n in reached
          if isinstance(getattr(store.get(n), "content", None), dict)
          and "against" in store.get(n).content]
    named = [c for c in cs if c.content.get("context") in qset]
    return named or cs


def gate(store, it, conds):
    """load > capacity, one comparison per condition. a condition
    names what it tests (against); numbers compare, lists attack."""
    out = []
    if not isinstance(it.content, dict):
        return out
    for c in conds:
        cc = c.content
        cap = it.content.get(cc["against"])
        if cap is None:
            continue
        v = cc["value"]
        try:
            if float(v) > float(cap):
                out.append("fails: %s %s > %s %s"
                           % (c.name, v, cc["against"], cap))
            else:
                out.append("holds: %s %s > %s %s"
                           % (cc["against"], cap, c.name, v))
        except ValueError:  # not numbers: an attack list
            if str(cap).strip() in str(v).split():
                out.append("fails: %s attacks %s" % (c.name, cap))
    return out


def field(store, reached, qset):
    """the candidate field, one run per context. a context is a whole:
    all its boundaries apply together, never mixed with another's."""
    by_ctx = {}
    for c in conditions(store, reached, qset):
        by_ctx.setdefault(c.content.get("context", ""), []).append(c)
    for ctx, cs in sorted(by_ctx.items()):
        tested = {c.content["against"] for c in cs}
        rows = [store.get(n) for n in reached
                if store.get(n).kind == "row" and store.get(n).truth != -1
                and isinstance(store.get(n).content, dict)
                and tested & set(store.get(n).content)]
        if len(rows) < 2:
            continue
        alive, dead = [], []
        for r in rows:
            f = [g for g in gate(store, r, cs) if g.startswith("fails")]
            (dead if f else alive).append((r, f))
        print("  %s: %d candidates, %d fail, %d survive"
              % (ctx or "persistence", len(rows), len(dead), len(alive)))
        for r, f in dead:
            print("    x %-16s %s" % (r.name, f[0][7:]))
        def sec(r):
            return (float(r.content.get("cost_per_kg", 9e9)),
                    float(r.content.get("density", 9e9)))
        for r, _ in sorted(alive, key=lambda rf: sec(rf[0])):
            print("    v %-16s cost %-5s density %s"
                  % (r.name, r.content.get("cost_per_kg", "?"),
                     r.content.get("density", "?")))


def props(store, reached, qset):
    """a question naming a property compares everything through it."""
    for n in reached:
        it = store.get(n)
        if it.kind != "property":
            continue
        if not set(terms(n.replace("_", " "))) & qset:
            continue
        vals = []
        for rn in it.refs:
            r = store.get(rn)
            if r and isinstance(r.content, dict) and n in r.content:
                vals.append((r.content[n], rn))
        try:
            vals.sort(key=lambda v: -float(v[0]))
        except ValueError:
            vals.sort(key=lambda v: str(v[0]))
        print("  %s: %s" % (n, ", ".join("%s %s" % (rn, v)
                                         for v, rn in vals)))


def show(store, answers, seeds, reached, qset):
    if not answers:
        print("  nothing reached from %s -- fill more, or say it: no: <truth>"
              % (seeds or "no known term"))
        return
    for i, (n, it) in enumerate(answers):
        body = it.content if isinstance(it.content, str) else \
            ", ".join("%s %s" % kv for kv in it.content.items())
        print("  %d. [%s] %s" % (i + 1, it.tag, body))
        for g in gate(store, it, conditions(store, reached, qset)):
            print("       %s" % g)
    props(store, reached, qset)
    field(store, reached, qset)
    print("  (walked %d items from %s)" % (len(reached), ", ".join(seeds)))


# ---------------------------------------------------------------- corrections
def correct(store, text, last):
    """no: <truth> -- grade the last question against what you said."""
    if not last:
        print("  nothing to correct yet")
        return
    q, cands, reached = last
    d = grade(store, q, cands, reached, text)
    print("  %s -- picked %s, right is %s" % (d["verdict"], d["picked"],
                                              d["right"]))
    if d["missing"] and d["verdict"] != "not stored":
        print("  learned: %s now answers to %s" % (d["right"],
                                                  " ".join(d["missing"])))
    if d["picked"] and d["verdict"] != "right":
        print("  refused for this question: %s" % d["picked"])


# ---------------------------------------------------------------- main
def main():
    args = sys.argv[1:]
    oneshot = None
    if "-q" in args:
        i = args.index("-q")
        oneshot = args[i + 1]
        args = args[:i] + args[i + 2:]
    store = load_store()
    print("store: %d items" % len(store.items))
    if os.path.exists(TOOLSFILE):
        print("his tools: %d words in his thesaurus, kinds for %s"
              % (load_tools(), ", ".join(sorted(KINDS)) or "nothing yet"))
    elif os.path.exists(LIBFILE) or os.path.exists(DICTFILE):
        print("library (wordnet): %d linked words" % load_dictionary())
    for path in args:
        fill(path, store)

    last = None                 # (question, scored field, reached)
    def handle(q):
        nonlocal last
        q = q.strip()
        if not q:
            return
        if q.startswith("no:"):
            correct(store, q[3:].strip(), last)
            return
        if q == "why":
            for _, n in (last[1][:3] if last else []):
                print("  %s <- refs %s" % (n, list(store.get(n).refs)[:8]))
            return
        if q == "redo":   # retroactive: every past answer re-earned today
            runs = [it for it in list(store.items.values())
                    if it.kind == "run" and isinstance(it.content, dict)]
            changed = 0
            for it in runs:
                qq = it.content.get("q", "")
                old = it.content.get("answers", [])
                _, _, answers = ask(store, qq)
                new = [n for n, _ in answers]
                if new != old:
                    changed += 1
                    print("  %s: %s" % (it.name, qq))
                    compare_runs(store, (it.name, old), answers, qq)
                    it.content["answers"] = new
            print("  %d runs rechecked, %d answers changed retroactively"
                  % (len(runs), changed))
            return
        prev = find_prev(store, q)      # before this run leaves residue
        seeds, reached, cands = score_all(store, q)   # always rerun
        answers = [(n, store.get(n)) for _, n in cands[:3]]
        show(store, answers, seeds, reached, set(terms(q)))
        if prev and answers:
            compare_runs(store, prev, answers, q)
        if seeds and clean_win(cands):  # a tied field is not a lesson
            residue(store, q, seeds, answers)
        last = (q, cands, reached)

    if oneshot:
        handle(oneshot)
        save(store)
        return
    while True:
        try:
            q = input("? ")
        except EOFError:
            break
        if q.strip() in ("quit", "exit"):
            break
        handle(q)
    save(store)
    print("saved: %d items" % len(store.items))


if __name__ == "__main__":
    main()
