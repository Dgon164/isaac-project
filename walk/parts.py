#!/usr/bin/env python3
"""parts.py -- the parts of a thing, taught, then quizzed. tuples first.

    python walk/parts.py               lesson, his rules, quiz, challenges
    python walk/parts.py -quiz 200     a longer quiz

He does not know what he is looking for, so the lesson names the parts
of a tuple (name, kind, values, length, first, last, made_by) on ten
labeled examples. Python itself labels them: the statement is run and
the object inspected. Then, for each part, he works out HOW TO FIND IT
by trying every simple locator he has against the lesson and keeping
the one that is right on every example. That is his rule for the part,
and he can say it.

He has two ways to answer about a new tuple: READ the statement with
his rules, or RUN it and inspect the object with what the textbook
taught (type, len, indexing). Every quiz question is graded per part
for both, and his record picks the way per part, with the reason.
Challenges are the tuples built to break READ.
"""
import ast
import inspect
import io
import os
import random
import sys
import tokenize

HERE = os.path.dirname(os.path.abspath(__file__))
PARTS = []          # the parts of the thing being learned; set from THING
THING = {}          # the thing: parts, lesson, truth, run, quiz, challenges

TUPLE_PARTS = ["name", "kind", "values", "length", "first", "last", "made_by"]

LESSON = [
    ("t = (1, 2, 3)", "parentheses"),
    ("point = 3, 4", "commas"),
    ("empty = ()", "parentheses"),
    ("single = 'hi',", "trailing comma"),
    ("pair = tuple([1, 2])", "tuple()"),
    ("rgb = ('red', 'green', 'blue')", "parentheses"),
    ("size = 640, 480, 32", "commas"),
    ("one = (7,)", "trailing comma"),
    ("digits = tuple('123')", "tuple()"),
    ("mixed = (1, 'two', 3.0)", "parentheses"),
]


# ------------------------------------------------------------- the truth
def run(statement):
    return THING["run"](statement)


def truth(statement, label):
    return THING["truth"](statement, label)


def run_tuple(statement):
    """RUN: execute the statement, inspect what it made. the parts as
    python sees them. made_by is not in the object: unknown to RUN."""
    ns = {}
    try:
        exec(statement, {}, ns)
    except Exception as e:
        return {"name": "-", "kind": "error: %s" % type(e).__name__,
                "values": "-", "length": "-", "first": "-", "last": "-",
                "made_by": "-"}
    name, v = next(iter(ns.items()))
    out = {"name": name, "kind": type(v).__name__, "made_by": "-"}
    try:
        items = list(v)
    except TypeError:
        items = None
    if items is None or isinstance(v, str):
        out.update(values=repr(v), length="-", first="-", last="-")
    else:
        out.update(values=", ".join(repr(x) for x in items),
                   length=str(len(items)),
                   first=repr(items[0]) if items else "",
                   last=repr(items[-1]) if items else "")
    return out


def truth_tuple(statement, made_by):
    t = run_tuple(statement)
    t["made_by"] = made_by
    return t


# ------------------------------------------------- the second thing: def
FUNC_PARTS = ["name", "kind", "params", "count", "first", "last", "returns"]

FUNC_LESSON = [
    ("def add(a, b):\n    return a + b", "-"),
    ("def hello():\n    print('hi')", "-"),
    ("def area(w, h=1):\n    return w * h", "-"),
    ("def greet(name):\n    \"\"\"say hi\"\"\"\n    return 'hi ' + name", "-"),
    ("def nothing():\n    pass", "-"),
    ("def total(*nums):\n    return sum(nums)", "-"),
    ("def mean(xs):\n    s = sum(xs)\n    return s / len(xs)", "-"),
    ("def square(x): return x * x", "-"),
    ("def first(items):\n    return items[0]", "-"),
    ("def shout(word, times=2):\n    return word.upper() * times", "-"),
]


def truth_function(statement, label):
    """the parts of a def as python's own parser sees them (ast): the
    ground truth, independent of both his ways of answering."""
    blank = {p: "-" for p in FUNC_PARTS}
    try:
        tree = ast.parse(statement)
    except SyntaxError:
        return blank
    node = tree.body[0] if tree.body else None
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        name, args, body = node.name, node.args, node.body
    elif isinstance(node, ast.Assign) and isinstance(node.value, ast.Lambda):
        name = node.targets[0].id
        args, body = node.value.args, [ast.Return(node.value.body)]
    else:
        return blank
    names = [a.arg for a in args.posonlyargs + args.args]
    if args.vararg:
        names.append(args.vararg.arg)
    names += [a.arg for a in args.kwonlyargs]
    if args.kwarg:
        names.append(args.kwarg.arg)
    returns = "no"
    for stmt in body:
        for sub in ast.walk(stmt):
            if isinstance(sub, (ast.FunctionDef, ast.Lambda)):
                continue
            if isinstance(sub, ast.Return) and sub.value is not None:
                returns = "yes"
    return {"name": name, "kind": "function", "params": ", ".join(names),
            "count": str(len(names)), "first": names[0] if names else "",
            "last": names[-1] if names else "", "returns": returns}


def run_function(statement):
    """RUN: define it and look at the function object. whether it returns
    a value is not on the object: unknown to RUN."""
    g = {}
    try:
        exec(statement, g)
    except Exception as e:
        return dict({p: "-" for p in FUNC_PARTS},
                    kind="error: %s" % type(e).__name__)
    fs = [v for k, v in g.items() if callable(v) and not k.startswith("__")]
    if not fs:
        return {p: "-" for p in FUNC_PARTS}
    f = fs[0]
    names = list(inspect.signature(f).parameters)
    return {"name": f.__name__, "kind": type(f).__name__,
            "params": ", ".join(names), "count": str(len(names)),
            "first": names[0] if names else "", "last": names[-1] if names else "",
            "returns": "-"}


FUNC_NAMES = ["add", "area", "greet", "total", "mean", "scale", "pick",
              "label", "shout", "clamp", "show", "combine"]
PARAM_NAMES = ["a", "b", "c", "x", "y", "n", "word", "items", "w", "h"]


def make_function(rng):
    name = rng.choice(FUNC_NAMES)
    n = rng.choice([0, 1, 1, 2, 2, 3])
    params = rng.sample(PARAM_NAMES, n)
    sig = list(params)
    if n >= 2 and rng.random() < 0.4:
        sig[-1] += "=" + rng.choice(["1", "2", "'x'", "None"])
    elif n >= 1 and rng.random() < 0.2:
        sig[-1] = "*" + params[-1]
    expr = " + ".join(params) if params else rng.choice(["0", "'hi'"])
    body_kind = rng.choice(["return", "return", "print", "pass"])
    body = {"return": "return " + expr, "print": "print(%s)" % expr,
            "pass": "pass"}[body_kind]
    if body_kind == "return" and rng.random() < 0.2:
        return "def %s(%s): %s" % (name, ", ".join(sig), body), "-"
    return "def %s(%s):\n    %s" % (name, ", ".join(sig), body), "-"


FUNC_CHALLENGES = [
    ("def f(a, b=2, *rest, **kw):\n    return a", "-"),
    ("sq = lambda x: x * x", "-"),
    ("def outer():\n    def inner(): return 1\n    return inner", "-"),
    ("def noop():\n    return", "-"),
    ("async def fetch(url):\n    return url", "-"),
    ("def show(x):\n    print(x)", "-"),
    ("def pairs(a, b, /, c):\n    return (a, b, c)", "-"),
    ("def later(n):\n    if n: return n\n    print('none')", "-"),
]


# ------------------------------------------------------------- reading
def toks(statement):
    out = []
    try:
        for tk in tokenize.generate_tokens(io.StringIO(statement).readline):
            if tk.type in (tokenize.ENCODING, tokenize.NEWLINE, tokenize.NL,
                           tokenize.ENDMARKER, tokenize.INDENT, tokenize.DEDENT):
                continue
            out.append(tk)
    except tokenize.TokenError:
        pass
    return out


LIT = (tokenize.NUMBER, tokenize.STRING)


def loc_tok(i):
    def f(tk, so_far):
        return tk[i].string if -len(tk) <= i < len(tk) else None
    f.__name__ = "token %d" % i
    return f


def loc_after_eq(tk, so_far):
    seen = False
    out = []
    for t in tk:
        if seen and (t.type in LIT or
                     (t.type == tokenize.NAME and t.string != "tuple")):
            out.append(t.string)
        if t.string == "=":
            seen = True
    return ", ".join(out)


def loc_inside(tk, so_far):
    depth, out = 0, []
    for t in tk:
        if t.string in "([":
            depth += 1
            continue
        if t.string in ")]":
            depth -= 1
            continue
        if depth > 0 and t.type in LIT:
            out.append(t.string)
    return ", ".join(out)


def loc_inside_names(tk, so_far):
    """the names inside the first parentheses (a def's parameters)."""
    depth, out, done = 0, [], False
    for t in tk:
        if done:
            break
        if t.string == "(":
            depth += 1
            continue
        if t.string == ")":
            depth -= 1
            if depth == 0:
                done = True
            continue
        if depth > 0 and t.type == tokenize.NAME:
            out.append(t.string)
    return ", ".join(out)


def loc_count(part):
    def f(tk, so_far):
        v = so_far.get(part)
        return None if v is None else str(len(v.split(", ")) if v else 0)
    f.__name__ = "count of %s" % part
    return f


def loc_first(part):
    def f(tk, so_far):
        v = so_far.get(part)
        return None if v is None else (v.split(", ")[0] if v else "")
    f.__name__ = "first of %s" % part
    return f


def loc_last(part):
    def f(tk, so_far):
        v = so_far.get(part)
        return None if v is None else (v.split(", ")[-1] if v else "")
    f.__name__ = "last of %s" % part
    return f


def features(tk):
    """what a statement shows on its face: which tokens it has, what it
    ends with. the signature classifier picks among these."""
    f = {"has:" + t.string for t in tk}
    if tk:
        f.add("last:" + tk[-1].string)
    body = [t for t in tk if t.string != ")"]
    if body:
        f.add("ends:" + body[-1].string)
    return f


def learn_signatures(examples, part):
    """by differentiation: for each label, the feature all its examples
    share that the most other examples lack."""
    labels = {}
    for tk, t in examples:
        labels.setdefault(t[part], []).append(features(tk))
    sig = {}
    for label, fs in labels.items():
        common = set.intersection(*fs)
        others = [f for l2, fs2 in labels.items() if l2 != label for f in fs2]
        best = None
        for feat in sorted(common):
            score = sum(1 for f in others if feat not in f)
            if best is None or score > best[0]:
                best = (score, feat)
        if best:
            sig[label] = best
    return sig


def loc_signature(sig):
    def f(tk, so_far):
        fs = features(tk)
        hits = [(score, label) for label, (score, feat) in sig.items()
                if feat in fs]
        return max(hits)[1] if hits else None
    f.__name__ = "signature " + "; ".join(
        "%s -> %s" % (feat, label) for label, (_, feat) in sorted(sig.items()))
    return f


def loc_const(value):
    def f(tk, so_far):
        return value
    f.__name__ = "always %s" % value
    return f


def learn_rules(lesson):
    """for each part, every locator he has against every example; the
    one right on the most examples is his rule (all of them, ideally)."""
    examples = [(toks(s), truth(s, m)) for s, m in lesson]
    rules, report = {}, []
    for part in PARTS:
        cands = [loc_tok(i) for i in range(-3, 4)] + \
            [loc_after_eq, loc_inside, loc_inside_names]
        for other in PARTS:
            if other != part and other in rules:
                cands += [loc_count(other), loc_first(other), loc_last(other)]
        labels = {t[part] for _, t in examples}
        if len(labels) == 1:
            cands.append(loc_const(labels.pop()))
        elif len(labels) <= 5:
            cands.append(loc_signature(learn_signatures(examples, part)))
        best = None
        for c in cands:
            right = 0
            for tk, t in examples:
                so_far = read(tk, rules, upto=part)
                if c(tk, so_far) == t[part]:
                    right += 1
            if best is None or right > best[0]:
                best = (right, c)
        rules[part] = best[1]
        report.append((part, best[1].__name__, best[0], len(examples)))
    return rules, report


def read(tk, rules, upto=None):
    """READ: apply his rules in part order; a derived part sees the
    parts before it."""
    out = {}
    for part in PARTS:
        if part == upto:
            break
        if part in rules:
            out[part] = rules[part](tk, out)
    return out


# ------------------------------------------------------------- the quiz
NAMES = ["a", "b", "coords", "color", "xy", "box", "row", "pt", "dims",
         "pair", "triple", "item", "vals", "size", "rgb", "corner"]
WORDS = ["red", "green", "blue", "up", "down", "left", "right", "hi"]


def make_tuple(rng):
    n = rng.choice([0, 1, 1, 2, 2, 3, 3, 4])
    items = []
    for _ in range(n):
        kind = rng.choice(["int", "int", "str", "float"])
        if kind == "int":
            items.append(str(rng.randint(0, 99)))
        elif kind == "float":
            items.append("%d.%d" % (rng.randint(0, 9), rng.randint(0, 9)))
        else:
            items.append("'%s'" % rng.choice(WORDS))
    name = rng.choice(NAMES)
    styles = ["parentheses", "tuple()"]
    if n >= 2:
        styles.append("commas")
    if n == 1:
        styles.append("trailing comma")
    style = rng.choice(styles)
    if style == "parentheses":
        s = "%s = (%s%s)" % (name, ", ".join(items), "," if n == 1 else "")
        if n == 1:
            style = "trailing comma"
    elif style == "commas":
        s = "%s = %s" % (name, ", ".join(items))
    elif style == "trailing comma":
        s = "%s = %s," % (name, items[0])
    else:
        s = "%s = tuple([%s])" % (name, ", ".join(items))
    return s, style


CHALLENGES = [
    ("x = 5", "-"),
    ("t = (len('abc'), 2)", "parentheses"),
    ("n = -1, -2", "commas"),
    ("w = (\"hi\", \"there\")", "parentheses"),
    ("q = tuple(range(3))", "tuple()"),
    ("s = ('a,b', 'c')", "parentheses"),
    ("nested = ((1, 2), 3)", "parentheses"),
    ("words = 'one two'.split()", "-"),
]


def grade(statement, made_by, rules, tally, show=False):
    t = truth(statement, made_by)
    tk = toks(statement)
    got = {"READ": read(tk, rules), "RUN": run(statement)}
    line = []
    for part in PARTS:
        marks = {}
        for tool, ans in got.items():
            ok = ans.get(part) == t[part]
            marks[tool] = ok
            c = tally.setdefault(part, {}).setdefault(tool, [0, 0])
            c[0] += ok
            c[1] += 1
        line.append((part, t[part], got["READ"].get(part), marks["READ"],
                     got["RUN"].get(part), marks["RUN"]))
    if show:
        print("  %s" % one_line(statement))
        for part, want, r, rok, u, uok in line:
            print("      %-8s truth %-22s READ %-22s %s   RUN %-22s %s"
                  % (part, want, str(r)[:22], "v" if rok else "x",
                     str(u)[:22], "v" if uok else "x"))
    return line


def his_pick(tally):
    """per part: the way with the better record, and why."""
    picks = {}
    for part in PARTS:
        rec = tally.get(part, {})
        ranked = sorted(((r / float(a) if a else 0, r, tool)
                         for tool, (r, a) in rec.items()), reverse=True)
        if not ranked:
            continue
        rate, r, tool = ranked[0]
        why = "%s %d/%d" % (tool, r, rec[tool][1])
        if len(ranked) > 1:
            why += " vs %s %d/%d" % (ranked[1][2], ranked[1][1],
                                     rec[ranked[1][2]][1])
        picks[part] = (tool, why)
    return picks


THINGS = {
    "tuple": dict(parts=TUPLE_PARTS, lesson=LESSON, truth=truth_tuple,
                  run=run_tuple, make=make_tuple, challenges=CHALLENGES,
                  what="tuple"),
    "function": dict(parts=FUNC_PARTS, lesson=FUNC_LESSON,
                     truth=truth_function, run=run_function,
                     make=make_function, challenges=FUNC_CHALLENGES,
                     what="function definition"),
}


def one_line(s):
    return s.replace("\n", " | ")


def main():
    n_quiz = int(sys.argv[sys.argv.index("-quiz") + 1]) \
        if "-quiz" in sys.argv else 40
    which = sys.argv[sys.argv.index("-thing") + 1] \
        if "-thing" in sys.argv else "tuple"
    THING.update(THINGS[which])
    PARTS[:] = THING["parts"]
    print("THE LESSON: the parts of a %s, labeled by python itself"
          % THING["what"])
    print("  %-36s " % "statement" + "".join("%-13s" % p for p in PARTS))
    for s, m in THING["lesson"]:
        t = truth(s, m)
        print("  %-36s " % one_line(s)[:36]
              + "".join("%-13s" % str(t[p])[:12] for p in PARTS))
    rules, report = learn_rules(THING["lesson"])
    print("\nHIS RULES for finding each part (locator right on n of the lesson):")
    for part, name, right, n in report:
        print("  %-8s = %-70s %d/%d" % (part, name[:70], right, n))

    rng = random.Random(7)
    tally = {}
    print("\nTHE QUIZ: %d new %ss, graded per part, READ vs RUN "
          "(first three shown):" % (n_quiz, THING["what"]))
    for i in range(n_quiz):
        s, m = THING["make"](rng)
        grade(s, m, rules, tally, show=i < 3)
    print("\n  his record after the quiz, and his pick per part:")
    print("  %-8s %-14s %-14s   pick" % ("part", "READ", "RUN"))
    for part in PARTS:
        rec = tally[part]
        tool, why = his_pick(tally)[part]
        print("  %-8s %-14s %-14s   %s  (%s)"
              % (part, "%d/%d" % tuple(rec["READ"]),
                 "%d/%d" % tuple(rec["RUN"]), tool, why))

    print("\nTHE CHALLENGES: built to break reading. his pick answers; "
          "the other way is shown too.")
    picks = his_pick(tally)
    for s, m in THING["challenges"]:
        t = truth(s, m)
        tk = toks(s)
        got = {"READ": read(tk, rules), "RUN": run(s)}
        print("  %s" % one_line(s))
        for part in PARTS:
            tool = picks[part][0]
            ans = got[tool].get(part)
            ok = ans == t[part]
            other = "RUN" if tool == "READ" else "READ"
            oans = got[other].get(part)
            ook = oans == t[part]
            print("      %-8s %s by %-4s %-24s %s%s"
                  % (part, "v" if ok else "x", tool, str(ans)[:24],
                     "" if ok else "(truth %s) " % t[part],
                     "" if ok or not ook else "-- %s had it: %s" % (other, oans)))
    print("\n(a wrong pick on a challenge is a correction: it goes in the "
          "record and moves his pick, the same as the quiz did)")


if __name__ == "__main__":
    main()
