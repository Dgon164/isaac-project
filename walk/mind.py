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
import json, os, re, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "engine"))
from core import Item, Store
from linker import link, terms

STOREFILE = os.path.join(HERE, "store.json")
TOOLSFILE = os.path.join(HERE, "tools.json")   # the tools he built himself
ATTFILE = os.path.join(HERE, "attention.json")  # his attention record (big,
                                                # rebuilt by tools.py learn)
LENSFILE = os.path.join(HERE, "lens.json")      # his lenses and his critic
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


# ------------------------------------------------------- the tools as switches
# every tool he has is a switch; a toolset is one setting of the switches.
# which setting to use is HIS call, from his own record (SELECTOR, built by
# tools.py learn): for each context, how often each toolset was right.
def toolsets():
    out = {}
    for thes in (False, True):
        for reading in (False, True):
            for kinds in ("off", "second", "first"):
                for venn in (False, True):
                    parts = [p for p, on in (("thes", thes),
                                             ("reading", reading)) if on]
                    if kinds != "off":
                        parts.append("kinds-" + kinds)
                    if venn:
                        parts.append("venn")
                    out["+".join(parts) or "none"] = {
                        "thes": thes, "reading": reading, "kinds": kinds,
                        "venn": venn}
    return out


TOOLSETS = toolsets()
DEFAULT = "thes+kinds-second"
TOOLSET = dict(TOOLSETS[DEFAULT])   # what is switched on right now
SELECTOR = {}                       # level -> context -> toolset -> [right, asked]
# ------------------------------------------------------------ his settings
# every knob in how he decides is a setting with a few alternatives, and
# it is his to set: tools.py tune predicts whether an alternative would
# change any pick, tests it once on material he never learned from,
# keeps what is more right and then quicker, and files the decision with
# its reason. nothing here is a constant.
SETTINGS = {"min_record": 20,          # graded asks before a context counts
            "rank": "right,quick",     # how he orders his tools
            "levels": "finest-first"}  # which record he trusts first
OPTIONS = {"min_record": [5, 20, 100],
           "rank": ["right,quick", "right", "quick,right"],
           "levels": ["finest-first", "coarsest-first"]}


def use(name):
    TOOLSET.clear()
    TOOLSET.update(TOOLSETS[name])
    return name


# --------------------------------------------------------------- attention
# attention is a venn intersection, decided per question (owner: "which
# animals are not a dog: in a list of animals you do not need animals as
# attention; in a list from chairs to koalas you do. when was x born: look
# up x, look up dates, look which date is related to born"). every
# question word is a constraint on the candidates; the kind word is a
# constraint on the FORM of the answer (when -> a date). start with the
# loose constraints and tighten with the details. a word that cuts nothing
# is not attention here; a word that would leave nothing is a wrong
# translation and is dropped; the words that cut are the attention words,
# and the trace is the idea the question was carrying. narrow() does it;
# the venn switch makes the survivors the answer. the record below is
# what corrections compare (selects / trips) and is kept for the why.
ATTENTION = {}
MIN_ATT = 5
CHANGED = set()


def attention(word, ctx=None):
    """his verdict on one word: +1 attention, -1 fluff, 0 tied or not yet
    assessed. the finest level with a record decides."""
    for lv, key in ((2, (ctx or "") + "/" + word), (1, word)):
        rec = ATTENTION.get(lv, {}).get(key)
        if rec and rec[0] + rec[1] >= MIN_ATT:
            if rec[0] > rec[1]:
                return 1, "%s+ (selects %d vs trips %d)" % (word, rec[0], rec[1])
            if rec[1] > rec[0]:
                return -1, "%s- (trips %d vs selects %d)" % (word, rec[1], rec[0])
            return 0, "%s= (tied %d)" % (word, rec[0])
    return 0, word + "? (flagged probably attention, no record yet)"


def assess(store, question, right, other, table=None):
    """the assessment tool, by differentiation. the right answer and the
    one he gave (or nearly gave), side by side: a question word in the
    right one and not the other is what selects; a question word in the
    other and not the right one is what tripped him. filed per word and
    per kind of question / word. returns what he found."""
    table = ATTENTION if table is None else table
    R, O = store.get(right), store.get(other)
    found = {"selects": [], "trips": [], "other": other}
    if R is None or O is None:
        return found
    r, o = set(R.refs), set(O.refs)
    k = kind(question)
    for w in sorted(set(terms(question))):
        if (w in r) == (w in o):
            continue                      # no difference here
        which = 0 if w in r else 1
        found["selects" if which == 0 else "trips"].append(w)
        for lv, key in ((1, w), (2, k + "/" + w)):
            c = table.setdefault(lv, {}).setdefault(key, [0, 0])
            c[which] += 1
    return found


def score_key(own, rare, fit, bagc):
    """the ranking tuple, in the order his toolset says."""
    key = [own]
    key += [fit, rare] if TOOLSET["kinds"] == "first" else [rare, fit]
    key.append(bagc)
    return tuple(key)


# ------------------------------------------------------------------ the venn
LAST_TRACE = []


def narrow(store, question, reached):
    """the question as constraints; the candidates as sets. loose first,
    then the details. returns the survivors and the trace: ("cut", word,
    before, after) / ("no cut", word) / ("dropped", word) / ("unknown",
    word)."""
    own = set(terms(question))
    ctx = context(question)
    sents = []
    for n in reached:
        it = store.get(n)
        if it.kind not in ("sentence", "row") or it.truth == -1 or it.native:
            continue
        if store.rel(ctx, n) < 0:
            continue
        sents.append(n)
    read = getattr(store, "dictionary", None) if TOOLSET["reading"] else None
    cons = []
    for w in sorted(own):
        pull = {w}
        if TOOLSET["thes"]:
            pull |= SYN.get(w, set())
        if read:
            pull |= read.get(w, set())
        cons.append((w, {n for n in sents if pull & set(store.get(n).refs)}))
    row = KINDS.get(kind(question)) if KINDS and TOOLSET["kinds"] != "off" \
        else None
    if row:                                  # the form the answer takes
        f, wgt = max(row.items(), key=lambda kv: kv[1])
        if wgt > 0:
            cons.append((kind(question) + ">" + f,
                         {n for n in sents
                          if feats(store.get(n).content).get(f)}))
    C, trace = set(sents), []
    for w, S in sorted(cons, key=lambda c: -len(c[1])):   # loose first
        if not S:
            trace.append(("unknown", w, 0, 0))
        elif not (S & C):
            trace.append(("dropped", w, len(C), 0))
        elif C <= S:
            trace.append(("no cut", w, len(C), len(C)))
        else:
            before = len(C)
            C &= S
            trace.append(("cut", w, before, len(C)))
            if len(C) == 1:
                break
    LAST_TRACE[:] = trace
    return C, trace


def venn_line(trace=None):
    """the trace in one line: what cut, what did not, what was dropped."""
    trace = LAST_TRACE if trace is None else trace
    cuts = ["%s %d>%d" % (w, b, a) for t, w, b, a in trace if t == "cut"]
    parts = ["attention: " + (", ".join(cuts) or "-")]
    for label in ("no cut", "dropped", "unknown"):
        ws = [w for t, w, b, a in trace if t == label]
        if ws:
            parts.append(label + ": " + " ".join(ws))
    return " | ".join(parts)


def context_at(level, store, question):
    """what a record is filed under. level 1: the kind of question.
    level 2: the kind, and how many of its words the store knows. one
    builder makes every level; only this key changes."""
    k = kind(question)
    if level == 1:
        return k
    known = sum(1 for t in set(terms(question)) if store.get(t))
    return "%s/%d" % (k, min(known, 4))


def rank_table(table):
    """the tools in a context's record, best first, the way his settings
    say: right rate then quicker, right only, or quicker then right."""
    rows = [(name, rec) for name, rec in table.items()
            if rec[1] >= SETTINGS["min_record"] and name in TOOLSETS]

    def key(nr):
        name, rec = nr
        rate = rec[0] / float(rec[1])
        ms = rec[2] / rec[1] if len(rec) > 2 else 0.0
        if SETTINGS["rank"] == "right":
            return (rate, rec[0], name)
        if SETTINGS["rank"] == "quick,right":
            return (-ms, rate, rec[0], name)
        return (rate, -ms, rec[0], name)
    return sorted(rows, key=key, reverse=True)


def select(store, question, max_level=None):
    """his choice of toolset for this question, and the reason. the record
    his settings say to trust first decides; the reason is the count and
    the time for his pick against the runner-up. no record -> the default."""
    finest = SETTINGS["levels"] == "finest-first"
    for lv in sorted(SELECTOR, reverse=finest):
        if max_level and lv > max_level:
            continue
        ctx = context_at(lv, store, question)
        table = SELECTOR[lv].get(ctx)
        if not table:
            continue
        ranked = rank_table(table)
        if not ranked:
            continue
        name, rec = ranked[0]
        ms = rec[2] / rec[1] * 1000 if len(rec) > 2 else 0.0
        why = "level %d, %s: %s right %d/%d in %.1fms" % (
            lv, ctx, name, rec[0], rec[1], ms)
        if len(ranked) > 1:
            n2, r2 = ranked[1]
            why += " vs %s %d/%d in %.1fms" % (
                n2, r2[0], r2[1], r2[2] / r2[1] * 1000 if len(r2) > 2 else 0.0)
        return name, why
    return DEFAULT, "no record for this question; default " + DEFAULT


def ask_selected(store, question, max_level=None):
    """he picks the tools, then answers. the why and the sense come back
    with it."""
    sense_start(store, question)
    name, why = select(store, question, max_level)
    use(name)
    seeds, reached, cands = score_all(store, question)
    if reached and not TOOLSET["venn"]:
        narrow(store, question, reached)   # for the report only
    sense_end(store, question, seeds, reached, cands)
    SENSE["tools"] = name
    return seeds, reached, cands, why + "\n  " + venn_line() + \
        "\n  " + sense_line()


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
    SYN.clear(); KINDS.clear(); SELECTOR.clear()
    SYN.update((k, set(v)) for k, v in d.get("thesaurus", {}).items())
    KINDS.update(d.get("kinds", {}))
    SELECTOR.update((int(k), v) for k, v in d.get("selector", {}).items())
    SETTINGS.update(d.get("settings", {}))
    ATTENTION.clear()
    if os.path.exists(ATTFILE):
        ATTENTION.update((int(k), v) for k, v in
                         json.load(open(ATTFILE, encoding="utf-8")).items())
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
    if "attention" in CHANGED:
        json.dump({str(lv): tab for lv, tab in ATTENTION.items()},
                  open(ATTFILE, "w", encoding="utf-8"))
    if "selector" in CHANGED and os.path.exists(TOOLSFILE):
        d = json.load(open(TOOLSFILE, encoding="utf-8"))
        d["selector"] = {str(lv): tab for lv, tab in SELECTOR.items()}
        json.dump(d, open(TOOLSFILE, "w", encoding="utf-8"), indent=1)


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
        SENSE["pulls"] = SENSE.get("pulls", 0) + 1
        i += 1
        if it is None:
            continue
        for r in it.refs:
            SENSE["lookups"] = SENSE.get("lookups", 0) + 1
            if r not in seen and store.get(r):
                seen.add(r)
                open_.append(r)
    return seen


# ---------------------------------------------------------------- his senses
# what he can tell about his own answer, before anyone grades it. one
# native item per ask: it never leaves him, and the selector, the
# telemetry and his corrections all read the same line.
SENSE = {"pulls": 0, "lookups": 0, "writes": 0, "t0": 0.0}
CALIB = {}        # what he said -> [right, said]. does his "sure" mean sure?
SURE = [(3, "sure"), (2, "likely"), (1, "maybe"), (0, "guess")]


def sense_start(store, question):
    SENSE.clear()
    SENSE.update(pulls=0, lookups=0, writes=0, t0=time.perf_counter(), q=question,
                 store=len(store.items))


def sense_end(store, question, seeds, reached, cands):
    """the reading. margin says how sure he is (measured: own+3 is right
    95% of the time, tied 22%); the rest is what the work cost."""
    own = set(terms(question))
    known = [t for t in own if store.get(t)]
    gap = (cands[0][0][0] - cands[1][0][0]) if len(cands) > 1 else \
        (cands[0][0][0] if cands else 0)
    word = "nothing" if not cands else \
        next(w for g, w in SURE if gap >= g)
    top = cands[0][1] if cands else None
    it = store.get(top) if top else None
    support = len(it.refs) if it is not None else 0
    told = it.tag if it is not None else "-"
    prev = find_prev(store, question)
    same = "-" if not prev else ("agrees" if prev[1][:1] == [top] else "differs")
    SENSE.update(sure=word, gap=gap, field=len(cands), reached=len(reached),
                 seeds=len(seeds), known=len(known), unknown=len(own) - len(known),
                 support=support, source=told, again=same,
                 secs=round(time.perf_counter() - SENSE["t0"], 4), answer=top)
    return SENSE


def sense_line(sense=None):
    d = SENSE if sense is None else sense
    if not d:
        return ""
    return ("sense: %s (gap %s of %d in the field) | %d words known, %d not | "
            "support %d from %s | %.2fms, %d pulls, %d lookups, %d writes | "
            "store %d | %s"
            % (d.get("sure"), d.get("gap"), d.get("field"), d.get("known"),
               d.get("unknown"), d.get("support"), d.get("source"),
               d.get("secs", 0) * 1000, d.get("pulls", 0), d.get("lookups", 0),
               d.get("writes", 0), d.get("store", 0), d.get("again")))


def senses(store):
    """his own telemetry, read back out of his own store: how sure he was
    and whether he was right, and what the asks cost."""
    rows = [i.content for i in store.items.values() if i.kind == "sense"]
    if not rows:
        print("  no readings yet")
        return
    print("  %d asks kept. graded: %d" %
          (len(rows), sum(1 for r in rows if "verdict" in r)))
    print("  %-8s %6s %6s %8s" % ("he said", "asks", "graded", "right"))
    for word in [w for _, w in SURE] + ["nothing"]:
        sel = [r for r in rows if r.get("sure") == word]
        graded = [r for r in sel if "verdict" in r]
        if sel:
            print("  %-8s %6d %6d %8s" % (
                word, len(sel), len(graded),
                "%d" % sum(1 for r in graded if r["verdict"] == "right")
                if graded else "-"))
    print("  cost per ask: %.2fms, %d pulls, %d lookups, %d writes (averages)"
          % (1000 * sum(r.get("secs", 0) for r in rows) / len(rows),
             sum(r.get("pulls", 0) for r in rows) / len(rows),
             sum(r.get("lookups", 0) for r in rows) / len(rows),
             sum(r.get("writes", 0) for r in rows) / len(rows)))
    tried = [r for r in rows if r.get("tries", 1) > 1]
    if tried:
        print("  asks that took more than one try: %d" % len(tried))


def sense_keep(store, sense):
    """the reading becomes an item of his, native: his own record of how
    that ask went, there to be read back."""
    n = sum(1 for i in store.items.values() if i.kind == "sense")
    store.put(Item("sense_%04d" % n, "sense", content=dict(sense),
                   native=True, tag="sense"))
    return "sense_%04d" % n


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
    read = None
    if TOOLSET["reading"]:                  # his dictionary from reading
        if getattr(store, "dictionary", None) is None:
            read_dictionary(store)
        read = store.dictionary
    for t in own:
        if TOOLSET["thes"]:
            bag |= SYN.get(t, set())
        if read:
            bag |= read.get(t, set())
    seeds = sorted(t for t in bag if store.get(t))
    if not seeds:
        return [], set(), []
    reached = walk(store, seeds)
    ctx = context(question)
    row = KINDS.get(kind(question)) if KINDS and TOOLSET["kinds"] != "off"         else None
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
            cands.append((score_key(len(hit), rare, fit,
                                    len(bag & (r | earned))), n))
    cands.sort(reverse=True)
    if TOOLSET["venn"]:                    # the survivors of the venn first
        C, _ = narrow(store, question, reached)
        cands = [c for c in cands if c[1] in C] + \
                [c for c in cands if c[1] not in C]
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
    d["compared"] = None
    if d["right"] and store.get(d["right"]) is not None:
        other = d["picked"] if d["verdict"] != "right" else \
            (cands[1][1] if len(cands) > 1 else None)
        if other and store.get(other) is not None:
            d["compared"] = assess(store, question, d["right"], other)
            CHANGED.add("attention")
    n_runs = sum(1 for i in store.items.values() if i.kind == "run")
    name = "run_%03d" % n_runs
    refs = [n for _, n in cands[:3]] + ([d["right"]] if d["right"] else [])
    store.put(Item(name, "run", content=dict(d, key=sorted(set(terms(question))),
                                             answers=[n for _, n in cands[:3]]),
                   tag="graded", refs=refs))
    SENSE["writes"] = SENSE.get("writes", 0) + 1
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


def retry_all(store, question, truth):
    """the correction as a test of every setting he has: which would have
    been right, and how long each took. filed in his selector for this
    kind of question, live, so his next pick knows."""
    prev = dict(TOOLSET)
    ctxs = ((1, context_at(1, store, question)),
            (2, context_at(2, store, question)))
    won = []
    for name in TOOLSETS:
        use(name)
        t0 = time.perf_counter()
        cands = score_all(store, question)[2]
        dt = time.perf_counter() - t0
        right = bool(cands) and \
            truth.lower() in str(store.get(cands[0][1]).content).lower()
        for lv, ctx in ctxs:
            c = SELECTOR.setdefault(lv, {}).setdefault(ctx, {}) \
                        .setdefault(name, [0, 0, 0.0])
            while len(c) < 3:
                c.append(0.0)
            c[0] += int(right)
            c[1] += 1
            c[2] += dt
        if right:
            won.append(name)
    TOOLSET.clear()
    TOOLSET.update(prev)
    CHANGED.add("selector")
    return won


# ------------------------------------------------------------ the deeper look
# owner: "the wrong thing shouldn't be a blind change. it's a deeper look
# and investigation." when something says he is wrong -- his critic, a
# tied field, a correction -- he does not swap answers. he looks: which
# question words the answer failed; what those words could be, from what
# he has read; which candidates satisfy them; which candidate wins when he
# asks every way he knows. then a decision, or "don't know" with reasons.
CRITIC = None
OBJECT_AT = 2.0        # the critic's score that calls for a look (mine, for now)


def atoms(store, own, name):
    """what he can see about a question and a candidate: the words each
    has, the words both have, his shared count, his rarity. the lens and
    the critic are built on these and nothing else."""
    it = store.get(name)
    r = {w for w in it.refs if store.get(w) is not None
         and store.get(w).kind == "term"}
    a = {"q:" + w for w in own} | {"c:" + w for w in r} | \
        {"both:" + w for w in own & r}
    shared = own & r
    a.add("share:%s" % (len(shared) if len(shared) < 3 else "3+"))
    if shared:
        rare = max(1.0 / len(store.get(t).refs) for t in shared
                   if store.get(t) and store.get(t).refs)
        a.add("rare:" + ("hi" if rare >= 0.5 else "mid" if rare >= 0.1 else "lo"))
    return a


def load_critic(path=LENSFILE):
    """his critic, learned by lens.py against himself and the key."""
    global CRITIC
    if not os.path.exists(path):
        CRITIC = None
        return 0
    d = json.load(open(path, encoding="utf-8"))
    index = {a: i for i, a in enumerate(d["atoms"])}
    conj = [tuple(c) for c, e in zip(d["critic"], d["critic_earned"]) if e]
    earned = [e for e in d["critic_earned"] if e]
    CRITIC = (conj, earned, index)
    return len(conj)


def critic_score(store, question, name):
    """how much this answer looks like the ones he got wrong."""
    if not CRITIC:
        return 0.0
    conj, earned, index = CRITIC
    ids = {index[x] for x in atoms(store, set(terms(question)), name) if x in index}
    return sum(e for c, e in zip(conj, earned) if all(i in ids for i in c))


def investigate(store, question, cands, reached):
    """the deeper look. returns (chosen, verdict, transcript)."""
    own = set(terms(question))
    top = cands[0][1]
    lines = []
    _, trace = narrow(store, question, reached)
    failed = [w for t, w, b, a in trace if t in ("dropped", "unknown") and ">" not in w]
    lines.append("failed by the answer: %s"
                 % (", ".join(failed) or "nothing; every word that could cut, cut"))
    if getattr(store, "dictionary", None) is None:
        read_dictionary(store)
    trans = {}
    for w in failed:
        ts = set(SYN.get(w, set())) | set(store.dictionary.get(w, set()))
        trans[w] = ts
        lines.append("  '%s' could be: %s" % (w, ", ".join(sorted(ts)[:6])
                                                or "no other word known"))
    field = cands[:5]
    sat = {}
    for key, n in field:
        r = set(store.get(n).refs)
        have = sorted(own & r)
        via = ["%s>%s" % (w, t) for w, ts in trans.items() for t in sorted(ts & r)[:1]]
        sat[n] = (len(have) + len(via), have, via)
    prev = dict(TOOLSET)
    wins = {}
    for name in TOOLSETS:                     # asked every way he knows
        use(name)
        c = score_all(store, question)[2]
        if c:
            wins[c[0][1]] = wins.get(c[0][1], 0) + 1
    TOOLSET.clear()
    TOOLSET.update(prev)
    for key, n in field:
        k, have, via = sat[n]
        lines.append("  %-30s satisfies %d (%s%s); wins %d of %d settings"
                     % (n[:30], k, " ".join(have) or "-",
                        (" " + " ".join(via)) if via else "", wins.get(n, 0), len(TOOLSETS)))
    ranked = sorted(field, key=lambda kn: (-sat[kn[1]][0], -wins.get(kn[1], 0),
                                           cands.index(kn)))
    best = ranked[0][1]
    runner = ranked[1][1] if len(ranked) > 1 else None
    if runner and sat[best][0] == sat[runner][0] and \
            wins.get(best, 0) == wins.get(runner, 0):
        lines.append("don't know: %s and %s satisfy the same and win the same"
                     % (best[:30], runner[:30]))
        return top, "don't know", lines
    lines.append("after looking: %s%s" % (best[:30], "" if best == top else
                                          " (was %s)" % top[:30]))
    return best, "chosen", lines


def residue(store, question, seeds, answers):
    """the run goes back into the store; answers that appeared together
    now share a link a future walk can cross."""
    n_runs = sum(1 for i in store.items.values() if i.kind == "run")
    name = "run_%03d" % n_runs
    content = {"q": question, "key": sorted(set(terms(question))),
               "answers": [a for a, _ in answers]}
    store.put(Item(name, "run", content=content, tag="run",
                   refs=list(seeds) + [a for a, _ in answers]))
    SENSE["writes"] = SENSE.get("writes", 0) + 1
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
    was = dict(SENSE)
    won = retry_all(store, q, text)
    d = grade(store, q, cands, reached, text)
    print("  under every setting, %d of %d would have been right%s"
          % (len(won), len(TOOLSETS), (": " + ", ".join(won[:4]) +
                                       (" ..." if len(won) > 4 else ""))
             if won else ""))
    name, why = select(store, q)
    print("  his pick for this kind of question is now %s (%s)"
          % (name, why.split(": ", 1)[-1]))
    if was.get("sure"):
        right = d["verdict"] == "right"
        last = [i for i in store.items.values() if i.kind == "sense"]
        if last:
            last[-1].content["verdict"] = "right" if right else d["verdict"]
            last[-1].content["tries"] = last[-1].content.get("tries", 1) + 1
            last[-1].content["writes"] = SENSE.get("writes", 0)
        r, n = 0, 0
        for i in store.items.values():
            if i.kind == "sense" and i.content.get("sure") == was["sure"] \
                    and "verdict" in i.content:
                r += i.content["verdict"] == "right"
                n += 1
        print("  he said %s; %s. when he says %s he is right %d of %d"
              % (was["sure"], "right" if right else "not", was["sure"], r, n))
    print("  %s -- picked %s, right is %s" % (d["verdict"], d["picked"],
                                              d["right"]))
    if d.get("compared"):
        c = d["compared"]
        print("  compared with %s: selects %s | trips %s"
              % (c["other"], " ".join(c["selects"]) or "-",
                 " ".join(c["trips"]) or "-"))
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
        print("his selector: %s" % (", ".join(
            "level %d over %d contexts" % (lv, len(t))
            for lv, t in sorted(SELECTOR.items())) or "no record yet"))
        print("his attention: %d words with a record" % len(ATTENTION.get(1, {})))
        print("his critic: %s" % ("%d conjunctions that mark a wrong answer"
                                  % load_critic() if os.path.exists(LENSFILE)
                                  else "none yet (walk/lens.py builds it)"))
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
        if q == "senses":
            senses(store)
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
        seeds, reached, cands, why = ask_selected(store, q)  # his tools; rerun
        print("  tools: %s" % why)
        answers = [(n, store.get(n)) for _, n in cands[:3]]
        show(store, answers, seeds, reached, set(terms(q)))
        if cands and (CRITIC or SENSE.get("sure") == "guess"):
            cs = critic_score(store, q, cands[0][1])
            if cs > OBJECT_AT or SENSE.get("sure") == "guess":
                print("  objection (critic %.1f, he said %s): looking deeper"
                      % (cs, SENSE.get("sure")))
                chosen, verdict, lines = investigate(store, q, cands, reached)
                for l in lines:
                    print("    " + l)
                SENSE["looked"] = verdict
                if verdict != "don't know" and chosen != cands[0][1]:
                    cands = [c for c in cands if c[1] == chosen] + \
                            [c for c in cands if c[1] != chosen]
                    answers = [(n, store.get(n)) for _, n in cands[:3]]
                    print("  answer after looking: %s"
                          % str(store.get(chosen).content)[:110])
        if prev and answers:
            compare_runs(store, prev, answers, q)
        if seeds and clean_win(cands):  # a tied field is not a lesson
            residue(store, q, seeds, answers)
        sense_keep(store, SENSE)        # after the writes, so it counts them
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
