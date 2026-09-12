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
    made = 0
    for r in rows[1:]:
        name = r[0].strip().lower().replace(" ", "_")
        content = dict(zip(hdr[1:], (c.strip() for c in r[1:])))
        refs = [c.strip().lower().replace(" ", "_") for c in r[1:]
                if c.strip() and not re.fullmatch(r"-?\d+\.?\d*", c.strip())]
        old = store.get(name)
        if old is not None:  # same name seen in prose: the row absorbs its links
            refs += [r2 for r2 in old.refs if r2 not in refs]
        store.put(Item(name, "row", content=content,
                       tag=os.path.basename(path), refs=refs))
        for t in refs + [name]:
            it = store.get(t)
            if it is None:
                store.put(Item(t, "term", tag=path, refs=[name]))
            elif name not in it.refs and t != name:
                it.refs = tuple(it.refs) + (name,)
        made += 1
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
    qterms = [t for t in terms(question)]
    seeds = [t for t in qterms if store.get(t)]
    if not seeds:
        return seeds, set(), []
    reached = walk(store, seeds)
    qset = set(qterms)
    cands = []
    for n in reached:
        it = store.get(n)
        if it.kind not in ("sentence", "row") or it.truth == -1 or it.native:
            continue
        hit = len(qset & (set(it.refs) | {n}))
        if hit:
            human = 1 if it.tag == "human" else 0
            cands.append((hit, human, -len(it.refs), n, it))
    cands.sort(reverse=True)
    return seeds, reached, [(n, it) for _, _, _, n, it in cands[:3]]


def residue(store, question, seeds, answers):
    """the run goes back into the store; answers that appeared together
    now share a link a future walk can cross."""
    n_runs = sum(1 for i in store.items.values() if i.kind == "run")
    name = "run_%03d" % n_runs
    store.put(Item(name, "run", content=question, tag="run",
                   refs=list(seeds) + [a for a, _ in answers]))
    for a, _ in answers:
        it = store.get(a)
        if name not in it.refs:
            it.refs = tuple(it.refs) + (name,)
    return name


def show(answers, seeds, reached):
    if not answers:
        print("  nothing reached from %s -- fill more, or say it: no: <truth>"
              % (seeds or "no known term"))
        return
    for i, (n, it) in enumerate(answers):
        body = it.content if isinstance(it.content, str) else \
            ", ".join("%s %s" % kv for kv in it.content.items())
        print("  %d. [%s] %s" % (i + 1, it.tag, body))
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
        seeds, reached, answers = ask(store, q)
        show(answers, seeds, reached)
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
