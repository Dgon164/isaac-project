#!/usr/bin/env python3
"""school.py -- the python textbook, given to him and tested.

    python walk/school.py              read, follow along, sit the exam
    python walk/school.py -show 40     print every exam answer in full

The book: the official Python Tutorial, Doc/tutorial/*.rst out of the
CPython source already on this disk (walk/textbook/). Three things:

  1. READ.          every paragraph becomes sentences in his store,
                    tagged by chapter. rst markup stripped, no parser.
  2. FOLLOW ALONG.  every >>> example is run and checked against the
                    book's own printed answer: the textbook carries its
                    own test. verified examples enter the store as truth
                    +1, the rest as 0 (unverified, not wrong -- input(),
                    files, clocks, the network are not here).
  3. THE EXAM.      plain-english questions about the book; every key is
                    a phrase from the book (checked). he picks his tools
                    and answers by the walk; the venn line shows which
                    words did the work.

The store is saved to walk/python_store.json (rebuilt every run).
"""
import contextlib
import doctest
import io
import os
import re
import socket
import sys
import tempfile
import time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "engine"))
from core import Item, Store
from linker import link, terms
import mind
from mind import ask_selected, load_tools

BOOK = os.path.join(HERE, "textbook")
ORDER = ["appetite", "interpreter", "introduction", "controlflow",
         "datastructures", "modules", "inputoutput", "errors", "classes",
         "stdlib", "stdlib2", "venv", "whatnow", "floatingpoint",
         "appendix", "interactive"]
KEEP = {"method", "function", "class", "attribute", "data", "note",
        "seealso", "versionadded", "versionchanged", "warning", "tip",
        "hint", "important", "deprecated"}
ROLE = re.compile(r":[a-z:]+:`!?([^`]*)`")
LINK = re.compile(r"`([^`<]+?)(?: <[^>]*>)?`_+")


def indent(line):
    return len(line) - len(line.lstrip())


def prose(rst):
    """the book's paragraphs, unwrapped, markup gone. example blocks and
    junk directives (index, code-block, comments) are dropped; the bodies
    of method/function/note directives are kept -- they are prose."""
    paras, cur = [], []
    skip_to = None                 # drop indented lines while indent > this
    for line in rst.splitlines():
        if skip_to is not None:
            if line.strip() and indent(line) <= skip_to:
                skip_to = None
            else:
                continue
        s = line.strip()
        if s.startswith(".."):
            m = re.match(r"\.\. ([a-z-]+)::", s)
            if not (m and m.group(1) in KEEP):
                skip_to = indent(line)
            if cur:
                paras.append(" ".join(cur)); cur = []
            continue
        if re.fullmatch(r"[*=\-^~\"#]{3,}", s):
            continue                                # heading underline
        if not s:
            if cur:
                paras.append(" ".join(cur)); cur = []
            continue
        if re.match(r"^\s*(>>>|\.\.\.)", line):
            continue
        s = ROLE.sub(r"\1", s)
        s = LINK.sub(r"\1", s)
        s = s.replace("``", "").replace("*", "")
        cur.append(s)
        if s.endswith("::"):                        # a literal block follows
            cur[-1] = s[:-1]
            paras.append(" ".join(cur)); cur = []
            skip_to = indent(line)
    if cur:
        paras.append(" ".join(cur))
    return "\n\n".join(p for p in paras if len(p) > 3)


def put_sentence(store, text, tag, truth=1):
    ts = terms(text)
    if not ts:
        return None
    n = sum(1 for i in store.items.values() if i.kind == "sentence")
    name = "e%04d_%s" % (n, "_".join(ts[:3]))
    store.put(Item(name, "sentence", content=text, truth=truth, tag=tag,
                   refs=ts))
    for t in ts:
        it = store.get(t)
        if it is None:
            store.put(Item(t, "term", tag=tag, refs=[name]))
        elif name not in it.refs:
            it.refs = tuple(it.refs) + (name,)
    return name


def no_network(*a, **k):
    raise OSError("no network in school")


class Deadline(Exception):
    pass


def run_with_deadline(code, ns, seconds=2.0):
    """the book has a 'while True: pass' in it. a trace function raises
    inside the running example once its time is up."""
    end = time.time() + seconds

    def tracer(frame, event, arg):
        if time.time() > end:
            raise Deadline("took longer than %.0fs" % seconds)
        return tracer
    sys.settrace(tracer)
    try:
        exec(code, ns)
    finally:
        sys.settrace(None)


def follow_along(rst, chapter):
    """run every >>> example of a chapter in one namespace, in order, and
    check the book's printed answer. returns [(source, want, ok)]."""
    examples = doctest.DocTestParser().get_examples(rst)
    checker = doctest.OutputChecker()
    flags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
    ns = {"__name__": "__main__"}
    out = []
    for ex in examples:
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                run_with_deadline(compile(ex.source, "<book:%s>" % chapter,
                                          "single"), ns)
            got = buf.getvalue()
        except SystemExit:
            got = buf.getvalue()
        except BaseException as e:            # the REPL would show this
            got = buf.getvalue() + "Traceback (most recent call last):\n" \
                "  ...\n%s: %s\n" % (type(e).__name__, e)
        if ex.want.strip() == "" and got.strip() == "":
            ok = True
        else:
            ok = checker.check_output(ex.want, got, flags)
        out.append((ex.source.strip(), ex.want.strip(), ok))
    return out


EXAM = [
    ("What does the for statement iterate over?", "items of any sequence"),
    ("What is elif short for?", "else if"),
    ("What keyword introduces a function definition?",
     "keyword def introduces a function definition"),
    ("What does the break statement do?",
     "breaks out of the innermost enclosing"),
    ("What does the pass statement do?", "does nothing"),
    ("What does the range function generate?", "arithmetic progressions"),
    ("What is a list comprehension?", "concise way to create lists"),
    ("What is a tuple?", "number of values separated by commas"),
    ("What is a set?", "unordered collection with no duplicate elements"),
    ("What are dictionaries indexed by?", "indexed by keys"),
    ("What is a module?", "file containing python definitions and statements"),
    ("What does the len function return?", "returns the length of a string"),
    ("What index does the first character of a string have?",
     "first character having index 0"),
    ("What does the del statement do?",
     "remove an item from a list given its index"),
    ("What does the zip function do?", "paired with the zip"),
    ("What is a class?", "bundling data and functionality together"),
    ("What happens to the except clause when no exception occurs?",
     "except clause is skipped"),
    ("What does the global statement do?", "live in the global scope"),
    ("How do you get a shallow copy of a list?", "shallow copy of the list"),
    ("What does the return statement do?", "returns with a value from a function"),
]


def main():
    show = int(sys.argv[sys.argv.index("-show") + 1]) \
        if "-show" in sys.argv else 6
    t0 = time.time()
    store = Store()
    print("his tools: %d thesaurus words" % load_tools(), flush=True)
    socket.socket.connect = no_network
    socket.create_connection = no_network
    sys.stdin = io.StringIO("")            # input() in the book: EOF, not a wait
    import builtins

    def no_input(*a, **k):
        raise EOFError("no keyboard in school")
    builtins.input = no_input
    work = tempfile.mkdtemp(prefix="school_")
    os.chdir(work)
    print("\n%-16s %8s %10s %10s" % ("chapter", "sentences", "examples", "verified"))
    tot_ex = tot_ok = 0
    for ch in ORDER:
        path = os.path.join(BOOK, ch + ".rst")
        if not os.path.exists(path):
            continue
        rst = open(path, encoding="utf-8").read()
        before = sum(1 for i in store.items.values() if i.kind == "sentence")
        link(prose(rst), store, tag=ch)
        n_sent = sum(1 for i in store.items.values()
                     if i.kind == "sentence") - before
        results = follow_along(rst, ch)
        ok = sum(1 for _, _, o in results if o)
        for src, want, o in results:
            text = src.replace("\n", " ") + (" -> " + want.replace("\n", " ")
                                             if want else "")
            put_sentence(store, text, ch + " example", truth=1 if o else 0)
        tot_ex += len(results); tot_ok += ok
        print("%-16s %8d %10d %10d" % (ch, n_sent, len(results), ok))
    print("%-16s %8d %10d %10d   (%.0fs)" % (
        "all", sum(1 for i in store.items.values() if i.kind == "sentence"),
        tot_ex, tot_ok, time.time() - t0))
    print("store: %d items" % len(store.items))

    print("\nTHE EXAM (%d questions; a key is a phrase from the book):" % len(EXAM))
    book = " ".join(str(i.content).lower() for i in store.items.values()
                    if i.kind == "sentence")
    right = close = 0
    for i, (q, key) in enumerate(EXAM):
        if key.lower() not in book:
            print("  ?  %s   [key not in book: %s]" % (q, key))
            continue
        seeds, reached, cands, why = ask_selected(store, q)
        got = [str(store.get(n).content).lower() for _, n in cands[:3]]
        if got and key.lower() in got[0]:
            mark = "v"; right += 1
        elif any(key.lower() in g for g in got):
            mark = "~"; close += 1
        else:
            mark = "x"
        print("  %s  %s" % (mark, q))
        if i < show or mark != "v":
            print("       his: %s" % (str(store.get(cands[0][1]).content)[:110]
                                     if cands else "(nothing)"))
            print("       %s" % why.split("\n")[-1].strip())
    print("\n  right %d / %d   close (in his top 3) %d   wrong %d"
          % (right, len(EXAM), close, len(EXAM) - right - close))
    mind.STOREFILE = os.path.join(HERE, "python_store.json")
    mind.save(store)
    print("saved walk/python_store.json")


if __name__ == "__main__":
    main()
