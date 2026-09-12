#!/usr/bin/env python3
"""mind.py -- the walk, usable.

    python walk/mind.py file.txt file.csv           interactive
    python walk/mind.py file.txt -q "a question"    one shot

Type a question, he walks the store and answers with the path.
Runs leave residue: every ask becomes an item pointing at what it
touched, so answers that appeared together grow a link. Corrections:
    no: <the truth>     marks the last top answer wrong, stores yours
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
DICTFILE = r"C:\Users\jtwee\Downloads\New folder (3)\intellon\wordnet_full.json"
SYN = {}


def load_dictionary(path=DICTFILE, cap=50):
    """thesaurus + dictionary as one map: words sharing a sense are
    synonyms; a word whose definition names t is a neighbor of t
    ('fame: ...widely known and popular' makes fame a neighbor of
    popular). capped: glue words relate to thousands and would drown
    the question."""
    entries = json.load(open(path, encoding="utf-8"))
    sense, rel = {}, {}
    for e in entries:
        sense.setdefault(e["sense"], []).append(e["word"].lower())
        w = e["word"].lower()
        for t in terms(e.get("def", "")):
            rel.setdefault(t, set()).add(w)
    for ws in sense.values():
        for w in ws:
            if len(ws) > 1:
                rel.setdefault(w, set()).update(x for x in ws if x != w)
    SYN.clear()
    SYN.update((t, s) for t, s in rel.items() if len(s) <= cap)
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
    open_, resolved = list(seeds), set()
    while open_:
        name = open_.pop(0)
        if name in resolved:
            continue
        resolved.add(name)
        it = store.get(name)
        if it is None:
            continue
        for r in it.refs:
            if r not in resolved and r not in open_ and store.get(r):
                open_.append(r)
    return resolved


def ask(store, question):
    """one bag of words: the question's own words plus their thesaurus
    pull. overlap with the bag is the score, own words count first.
    nothing in the bag = a tangent = not an answer. that is all."""
    own = set(terms(question))
    bag = set(own)
    for t in own:
        bag |= SYN.get(t, set())
    seeds = sorted(t for t in bag if store.get(t))
    if not seeds:
        return [], set(), []
    reached = walk(store, seeds)
    cands = []
    for n in reached:
        it = store.get(n)
        if it.kind not in ("sentence", "row") or it.truth == -1 or it.native:
            continue
        r = set(it.refs) | {n}
        if bag & r:
            cands.append(((len(own & r), len(bag & r)), n))
    cands.sort(reverse=True)
    return seeds, reached, [(n, store.get(n)) for _, n in cands[:3]]


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
def correct(store, text, last_answers):
    if last_answers:
        n, it = last_answers[0]
        it.truth = -1
        print("  marked wrong (kept): %s" % n)
    ts = terms(text)
    name = "h%03d_%s" % (sum(1 for i in store.items.values()
                             if i.tag == "human"), "_".join(ts[:3]))
    store.put(Item(name, "sentence", content=text, tag="human", refs=ts))
    for t in ts:
        it = store.get(t)
        if it is None:
            store.put(Item(t, "term", tag="human", refs=[name]))
        elif name not in it.refs:
            it.refs = tuple(it.refs) + (name,)
    print("  stored as %s" % name)


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
    for path in args:
        fill(path, store)

    last = []
    def handle(q):
        nonlocal last
        q = q.strip()
        if not q:
            return
        if q.startswith("no:"):
            correct(store, q[3:].strip(), last)
            return
        if q == "why":
            for n, it in last:
                print("  %s <- refs %s" % (n, list(it.refs)[:8]))
            return
        prev = find_prev(store, q)      # before this run leaves residue
        seeds, reached, answers = ask(store, q)   # always rerun, never reuse
        show(store, answers, seeds, reached, set(terms(q)))
        if prev and answers:
            compare_runs(store, prev, answers, q)
        if seeds:
            residue(store, q, seeds, answers)
        last = answers

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
